"""BS EN 50343:2024 電線選定計算エンジンの単体テスト.

規格書 Annex F の計算例 (Example 1〜3)、Table 2 の空欄（設計対象外）判定、
1℃刻みの周囲温度補正 k1、および多芯ケーブル補正 k5 の補間を検証する。
"""

import math
import unittest

from src.backend.calculator import EN50343Calculator
from src.backend.models import CableSizingInput


class TestEN50343Calculator(unittest.TestCase):
    """EN50343Calculator の規格整合性テスト."""

    def test_annex_f_example_1_standard_lifetime(self) -> None:
        """Annex F.1 Example 1 (k3=1.0, 100,000h): 475A, ON 480s / Cycle 520s, T=55℃, Type f 4本."""
        params = CableSizingInput(
            load_current_a=475.0,
            operation_mode="cyclic",
            cyclic_on_sec=480.0,
            cyclic_total_sec=520.0,
            ambient_temp_c=55,
            use_table_d1_rounded_k1=True,  # Annex F Example 1 uses k1 = 0.88 from Table D.1
            tc_max_c=90,
            installation_type_id="type_f",
            num_bundled_cables=4,
            is_multicore=False,
            num_loaded_cores=1,
            lifetime_delta_t_k=0,
        )
        res = EN50343Calculator.evaluate(params)
        self.assertTrue(res.is_valid_configuration)
        # I_load = 475 * sqrt(480/520) = 456.365... -> 456.4 A
        self.assertAlmostEqual(res.effective_load_current_a, 456.37, places=1)
        self.assertAlmostEqual(res.k1, 0.88, places=2)
        self.assertAlmostEqual(res.k2 or 0.0, 0.65, places=2)
        self.assertAlmostEqual(res.k3, 1.00, places=2)
        self.assertAlmostEqual(res.k4, 1.00, places=2)
        self.assertAlmostEqual(res.k5, 1.00, places=2)
        # Required I_cable = 456.365 / (0.88 * 0.65) = 797.8 A (~798 A)
        self.assertAlmostEqual(res.required_i_cable_90_a, 797.8, places=0)
        # 300 mm2 (775 A) is too small, so 400 mm2 (950 A) is selected
        self.assertIsNotNone(res.selected_candidate)
        if res.selected_candidate is not None:
            self.assertEqual(res.selected_candidate.csa_mm2, 400.0)

    def test_annex_f_example_1_reduced_lifetime_50000h(self) -> None:
        """Annex F.1 Example 1 (k3=1.10, 50,000h): 300 mm2 が適格となることを確認."""
        params = CableSizingInput(
            load_current_a=475.0,
            operation_mode="cyclic",
            cyclic_on_sec=480.0,
            cyclic_total_sec=520.0,
            ambient_temp_c=55,
            use_table_d1_rounded_k1=True,
            tc_max_c=90,
            installation_type_id="type_f",
            num_bundled_cables=4,
            is_multicore=False,
            num_loaded_cores=1,
            lifetime_delta_t_k=10,
        )
        res = EN50343Calculator.evaluate(params)
        self.assertTrue(res.is_valid_configuration)
        self.assertAlmostEqual(res.k3, 1.10, places=2)
        # Required I_cable = 456.365 / (0.88 * 0.65 * 1.10) = 725.3 A (~725 A)
        self.assertAlmostEqual(res.required_i_cable_90_a, 725.3, places=0)
        self.assertIsNotNone(res.selected_candidate)
        if res.selected_candidate is not None:
            self.assertEqual(res.selected_candidate.csa_mm2, 300.0)

    def test_table_2_invalid_combinations(self) -> None:
        """Table 2 の設計対象外（空欄または -）の組み合わせがエラーとして検出されることを確認."""
        # 1) Type a で 2本以上
        k2_a, _, err_a = EN50343Calculator.calculate_k2("type_a", 2)
        self.assertIsNone(k2_a)
        self.assertIsNotNone(err_a)

        # 2) トレイ上・2層配列 (trays_two_layers) で 2本 (2本を縦には積まない)
        k2_two2, _, err_two2 = EN50343Calculator.calculate_k2("trays_two_layers", 2)
        self.assertIsNone(k2_two2)
        self.assertIsNotNone(err_two2)

        # トレイ上・2層配列で 3本は 0.83 で有効
        k2_two3, _, err_two3 = EN50343Calculator.calculate_k2("trays_two_layers", 3)
        self.assertAlmostEqual(k2_two3 or 0.0, 0.83, places=2)
        self.assertIsNone(err_two3)

        # 3) Type c (トレイ上・多層配列) で 2本および3本は対象外
        k2_c2, _, err_c2 = EN50343Calculator.calculate_k2("type_c", 2)
        self.assertIsNone(k2_c2)
        self.assertIsNotNone(err_c2)

        k2_c3, _, err_c3 = EN50343Calculator.calculate_k2("type_c", 3)
        self.assertIsNone(k2_c3)
        self.assertIsNotNone(err_c3)

        # Type c で 4本は 0.71 で有効
        k2_c4, _, err_c4 = EN50343Calculator.calculate_k2("type_c", 4)
        self.assertAlmostEqual(k2_c4 or 0.0, 0.71, places=2)
        self.assertIsNone(err_c4)

    def test_k1_1degc_step_calculation(self) -> None:
        """1℃刻みの周囲温度 T に対して k1 が正確に算出されることを確認."""
        for temp in range(-20, 89):
            k1_val, k1_exact, _, err = EN50343Calculator.calculate_k1(temp, 90, use_rounded_2dec=False)
            self.assertIsNone(err)
            expected = math.sqrt((90.0 - float(temp)) / (90.0 - 45.0))
            self.assertAlmostEqual(k1_val or 0.0, expected, places=6)
            self.assertAlmostEqual(k1_exact, expected, places=6)


if __name__ == "__main__":
    unittest.main()
