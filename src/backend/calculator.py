"""BS EN 50343:2024 電線選定・許容電流計算エンジン."""

import math
from typing import Dict, List, Optional, Tuple

from src.backend.models import CableSizingInput, CableSizingResult, CSACandidateEvaluation
from src.backend.standards_data import (
    CONTROL_CABLE_CURRENT_DENSITY,
    COPPER_ALPHA,
    DEFAULT_MIN_CSA_MM2,
    INSTALLATION_TYPES,
    KELVIN_OFFSET,
    LIFETIME_DELTA_T_OPTIONS,
    STANDARD_CSA_LIST,
    TABLE_1_K5_MULTICORE,
    TABLE_3_PROTECTION_DEVICE_SIZING,
    TABLE_A1_K4_SHORT_TIME,
    TABLE_B1_CURRENT_RATINGS,
    TABLE_G7_PULL_OUT_FORCE_N,
    TEMPERATURE_CLASSES,
    T_BASE_MAX_K,
    T_REF_C,
    T_REF_K,
)


class EN50343Calculator:
    """BS EN 50343:2024 に準拠した電線サイズ・許容電流・補正係数の計算クラス."""

    @staticmethod
    def calculate_effective_load_current(
        load_current_a: float,
        operation_mode: str,
        cyclic_on_sec: float = 480.0,
        cyclic_total_sec: float = 520.0,
    ) -> Tuple[float, Optional[str]]:
        """Clause 4.2.3 a) に基づき負荷電流 I_load (A) を算出する."""
        if load_current_a < 0:
            return 0.0, "負荷電流には 0 A 以上の値を入力してください。"

        if operation_mode == "cyclic":
            if cyclic_total_sec <= 0 or cyclic_on_sec <= 0:
                return load_current_a, "周期運転の周期時間およびON時間は正の値にしてください。"
            if cyclic_on_sec > cyclic_total_sec:
                return load_current_a, "ON時間が1周期時間を超えているため、デューティ比 100% として計算します。"
            effective_i = load_current_a * math.sqrt(cyclic_on_sec / cyclic_total_sec)
            return effective_i, None

        return load_current_a, None

    @staticmethod
    def calculate_k_star(tc_max_c: int, use_table_value: bool = True) -> Tuple[float, float]:
        """Annex C (Table C.1) に基づき 90℃ 以外の耐熱クラス換算係数 k* を計算する.

        Returns:
            (適用する k*, 理論式による厳密値 k*_exact)
        """
        tc_k = float(tc_max_c) + KELVIN_OFFSET
        numerator = (tc_k - T_REF_K) * (1.0 + COPPER_ALPHA * T_BASE_MAX_K)
        denominator = (T_BASE_MAX_K - T_REF_K) * (1.0 + COPPER_ALPHA * tc_k)
        if numerator <= 0 or denominator <= 0:
            return 1.0, 1.0

        k_star_exact = math.sqrt(numerator / denominator)
        if use_table_value and tc_max_c in TEMPERATURE_CLASSES:
            table_val = float(TEMPERATURE_CLASSES[tc_max_c]["k_star_table"])
            return table_val, k_star_exact
        return round(k_star_exact, 2), k_star_exact

    @staticmethod
    def calculate_k1(
        ambient_temp_c: int,
        tc_max_c: int,
        use_rounded_2dec: bool = False,
    ) -> Tuple[Optional[float], float, float, Optional[str]]:
        """Clause 4.2.3 b) および Annex D に基づき周囲温度補正係数 k1 を 1℃刻みで計算する.

        式: k1 = sqrt((Tc(max) - T) / (Tc(max) - Tref))

        Returns:
            (適用する k1, 厳密値 k1_exact, 小数第2位丸め値 k1_rounded, エラーメッセージ)
        """
        t_c = float(int(round(ambient_temp_c)))
        tc_max = float(tc_max_c)

        if t_c >= tc_max:
            return (
                None,
                0.0,
                0.0,
                f"周囲温度 ({int(t_c)} ℃) が電線の最高許容導体温度 Tc(max) ({tc_max_c} ℃) 以上であるため通電できません。"
                "より高い耐熱クラスの電線を選択するか、周囲温度条件を見直してください。",
            )

        denom = tc_max - T_REF_C
        if denom <= 0:
            return None, 0.0, 0.0, "基準温度条件が不正です。"

        k1_exact = math.sqrt((tc_max - t_c) / denom)
        k1_rounded = round(k1_exact, 2)
        applied_k1 = k1_rounded if use_rounded_2dec else k1_exact
        return applied_k1, k1_exact, k1_rounded, None

    @staticmethod
    def calculate_k2(
        installation_type_id: str,
        num_cables: int,
    ) -> Tuple[Optional[float], bool, Optional[str]]:
        """Clause 4.2.3 b) および Table 2 に基づき敷設方式・同時負荷電線本数の補正係数 k2 を算出する.

        Table 2 で空欄または「-」となっている非適用領域（Type a の2本以上、2層配列の2本、Type c 多層配列の2〜3本）は
        設計上成立しない組み合わせとして None とエラー理由を返す。
        有効な本数定義間の端数本数（例: 5〜7本、9〜11本など）は線形補間を行う。

        Returns:
            (k2, 線形補間されたかどうか, エラーまたは警告メッセージ)
        """
        if installation_type_id not in INSTALLATION_TYPES:
            return None, False, f"未定義の敷設方式です: {installation_type_id}"

        inst_info = INSTALLATION_TYPES[installation_type_id]
        n = max(1, int(num_cables))

        invalid_counts: List[int] = list(inst_info.get("invalid_counts", []))  # type: ignore[arg-type]
        if n in invalid_counts or (installation_type_id == "type_a" and n >= 2):
            return None, False, str(inst_info.get("invalid_message", "選択された敷設方式と電線本数の組み合わせは規格対象外です。"))

        factors: Dict[int, float] = dict(inst_info["table_factors"])  # type: ignore[arg-type]
        defined_counts = sorted(factors.keys())

        # 20本以上は 20本の値を適用 (Table 2: "20 cables and more together")
        if n >= 20 and 20 in factors:
            return factors[20], False, None

        if n in factors:
            return factors[n], False, None

        # 定義された本数の間で線形補間 (ただし invalid_counts を跨ぐ区間は補間しない)
        for i in range(len(defined_counts) - 1):
            c_low = defined_counts[i]
            c_high = defined_counts[i + 1]
            if c_low < n < c_high:
                # もし区間に invalid_counts が含まれていれば補間不可
                if any(c_low < inv < c_high for inv in invalid_counts):
                    return None, False, str(inst_info.get("invalid_message", "規格表で定義されていない本数領域です。"))
                v_low = factors[c_low]
                v_high = factors[c_high]
                ratio = float(n - c_low) / float(c_high - c_low)
                interp_val = v_low + ratio * (v_high - v_low)
                return interp_val, True, None

        return None, False, str(inst_info.get("invalid_message", "指定された電線本数に対する係数 k2 が定義されていません。"))

    @staticmethod
    def calculate_k3(tc_max_c: int, delta_t_k: int) -> Tuple[float, Optional[str]]:
        """Annex E (E.2) に基づき予測ケーブル寿命変更補正係数 k3 を算出する.

        式: k3(ΔT) = sqrt( ((Tc(max) + ΔT - Tref) * (1 + 0.004 * Tc(max))) /
                           ((Tc(max) - Tref) * (1 + 0.004 * (Tc(max) + ΔT))) )
        温度はすべてケルビン (K) を使用する。
        """
        if delta_t_k == 0:
            return 1.0, None

        warning_msg = None
        dt = float(delta_t_k)
        if dt < 0 or dt > 30:
            warning_msg = "Annex E.2 により ΔT の推奨範囲は 0 K 〜 30 K です。"

        # 90℃クラスの代表値 (Table E.2: ΔT=10->1.10, 20->1.18, 30->1.26) と式の一致確認
        tc_k = float(tc_max_c) + KELVIN_OFFSET
        num = (tc_k + dt - T_REF_K) * (1.0 + COPPER_ALPHA * tc_k)
        den = (tc_k - T_REF_K) * (1.0 + COPPER_ALPHA * (tc_k + dt))
        if num <= 0 or den <= 0:
            return 1.0, "寿命補正係数 k3 の計算範囲外です。"

        k3_val = round(math.sqrt(num / den), 2)
        return k3_val, warning_msg

    @staticmethod
    def calculate_thermal_time_constant_empirical(csa_mm2: float) -> float:
        """Annex A に記載の EN 50264 電線の熱時定数経験式 T = 1.8 * (sqrt(A) - 5) [分].

        規格上は 50 mm2 超に対して規定されているが、50 mm2 以下でも下限値 (0.5分) を設けて安全側に評価する。
        """
        if csa_mm2 <= 25.0:
            return 0.5
        val = 1.8 * (math.sqrt(csa_mm2) - 5.0)
        return max(0.5, val)

    @classmethod
    def calculate_k4(
        cls,
        operation_mode: str,
        short_time_on_min: float,
        short_time_constant_mode: str,
        short_time_manual_tau_min: float,
        csa_mm2: float = 50.0,
    ) -> float:
        """Annex A (Table A.1) に基づき短時間電流運転時の補正係数 k4 を算出する."""
        if operation_mode != "short_time":
            return 1.0

        if short_time_on_min <= 0:
            return 1.0

        if short_time_constant_mode == "empirical":
            # Annex A: 50 mm2 を超える電線に対して T = 1.8 * (sqrt(A) - 5) が適用可能
            if csa_mm2 <= 50.0:
                return 1.0
            tau = cls.calculate_thermal_time_constant_empirical(csa_mm2)
        else:
            tau = max(0.1, short_time_manual_tau_min)

        coeff_of_use = short_time_on_min / tau  # t2 / T

        # Table A.1 に基づく補間
        if coeff_of_use <= TABLE_A1_K4_SHORT_TIME[0][0]:
            return TABLE_A1_K4_SHORT_TIME[0][1]
        if coeff_of_use > TABLE_A1_K4_SHORT_TIME[-1][0]:
            return 1.0

        for i in range(len(TABLE_A1_K4_SHORT_TIME) - 1):
            r_low, k_low = TABLE_A1_K4_SHORT_TIME[i]
            r_high, k_high = TABLE_A1_K4_SHORT_TIME[i + 1]
            if r_low <= coeff_of_use <= r_high:
                ratio = (coeff_of_use - r_low) / (r_high - r_low)
                return k_low + ratio * (k_high - k_low)

        return 1.0

    @staticmethod
    def calculate_k5(is_multicore: bool, num_loaded_cores: int) -> Tuple[float, bool, Optional[str]]:
        """Clause 4.2.3 b) および Table 1 に基づき多芯ケーブル補正係数 k5 を算出する."""
        if not is_multicore or num_loaded_cores <= 1:
            return 1.0, False, None

        n = int(num_loaded_cores)
        defined_cores = sorted(TABLE_1_K5_MULTICORE.keys())

        if n in TABLE_1_K5_MULTICORE:
            return TABLE_1_K5_MULTICORE[n], False, None

        if n > defined_cores[-1]:
            return (
                TABLE_1_K5_MULTICORE[defined_cores[-1]],
                False,
                "同時負荷芯数が19芯を超えています。Table 1 の注記に従いケーブル製造業者との協議が推奨されます（19芯の係数 0.38 を適用中）。",
            )

        for i in range(len(defined_cores) - 1):
            c_low = defined_cores[i]
            c_high = defined_cores[i + 1]
            if c_low < n < c_high:
                v_low = TABLE_1_K5_MULTICORE[c_low]
                v_high = TABLE_1_K5_MULTICORE[c_high]
                ratio = float(n - c_low) / float(c_high - c_low)
                return v_low + ratio * (v_high - v_low), True, None

        return 1.0, False, None

    @staticmethod
    def calculate_short_circuit_limit(csa_mm2: float, tc_max_c: int, duration_s: float) -> float:
        """Annex F (F.2, Table F.1, Table F.2) に基づき許容短絡電流 I = K * S / sqrt(t) を算出する."""
        if duration_s <= 0:
            return float("inf")
        t_clamped = min(5.0, max(0.001, duration_s))
        k_const = 122.0
        if tc_max_c in TEMPERATURE_CLASSES:
            k_const = float(TEMPERATURE_CLASSES[tc_max_c]["short_circuit_k"])
        return (k_const * csa_mm2) / math.sqrt(t_clamped)

    @staticmethod
    def get_protection_device_min_csa(
        protection_rating_a: int,
        installation_type_id: str,
    ) -> Optional[float]:
        """Clause 4.2.4 (Table 3) に基づき保護装置定格から要求される最小断面積を返す."""
        if protection_rating_a not in TABLE_3_PROTECTION_DEVICE_SIZING:
            return None
        row = TABLE_3_PROTECTION_DEVICE_SIZING[protection_rating_a]
        if installation_type_id in ("type_f", "type_g"):
            return row["closed_tube_max4"]
        return row["open_max4"]

    @classmethod
    def evaluate(cls, params: CableSizingInput) -> CableSizingResult:
        """入力パラメータに基づき BS EN 50343:2024 の全計算プロセスを実行し結果を返す."""
        result = CableSizingResult(input_params=params)

        # 耐熱クラス情報
        temp_info = TEMPERATURE_CLASSES.get(params.tc_max_c, TEMPERATURE_CLASSES[90])
        result.standard_family_name = str(temp_info["standard_family"])

        life_info = LIFETIME_DELTA_T_OPTIONS.get(params.lifetime_delta_t_k, LIFETIME_DELTA_T_OPTIONS[0])
        result.expected_lifetime_hours = int(life_info["expected_hours"])

        # 1. 負荷電流 I_load の計算
        eff_load, load_warn = cls.calculate_effective_load_current(
            params.load_current_a,
            params.operation_mode,
            params.cyclic_on_sec,
            params.cyclic_total_sec,
        )
        result.effective_load_current_a = eff_load
        if load_warn:
            result.warnings.append(load_warn)

        # 2. 温度クラス換算係数 k*
        k_star, k_star_exact = cls.calculate_k_star(params.tc_max_c, use_table_value=True)
        result.k_star = k_star
        result.k_star_formula_exact = k_star_exact

        # 3. 周囲温度補正係数 k1 (1℃刻み)
        k1_val, k1_exact, k1_round, k1_err = cls.calculate_k1(
            params.ambient_temp_c,
            params.tc_max_c,
            use_rounded_2dec=params.use_table_d1_rounded_k1,
        )
        result.k1_exact = k1_exact
        result.k1_rounded_2dec = k1_round
        if k1_err or k1_val is None:
            result.is_valid_configuration = False
            result.error_message = k1_err or "周囲温度エラー"
            result.k1 = 0.0
            return result
        result.k1 = k1_val

        # 4. 敷設方式・束線補正係数 k2 (Table 2)
        k2_val, k2_interp, k2_err = cls.calculate_k2(
            params.installation_type_id,
            params.num_bundled_cables,
        )
        result.k2 = k2_val
        result.k2_is_interpolated = k2_interp
        if k2_err or k2_val is None:
            result.is_valid_configuration = False
            result.error_message = k2_err or "敷設方式・本数の組み合わせが規格対象外です。"
            return result

        # 5. 予測寿命補正係数 k3 (Annex E)
        k3_val, k3_warn = cls.calculate_k3(params.tc_max_c, params.lifetime_delta_t_k)
        result.k3 = k3_val
        if k3_warn:
            result.warnings.append(k3_warn)
        if params.lifetime_delta_t_k > 0:
            result.warnings.append(
                f"予測寿命短縮 (ΔT = +{params.lifetime_delta_t_k} K, k3 = {k3_val:.2f}) が適用されています。"
                f"推定寿命は約 {result.expected_lifetime_hours:,} 時間です（ケーブル製造業者との合意が必要）。"
            )

        # 6. 多芯ケーブル補正係数 k5 (Table 1)
        k5_val, k5_interp, k5_warn = cls.calculate_k5(params.is_multicore, params.num_loaded_cores)
        result.k5 = k5_val
        result.k5_is_interpolated = k5_interp
        if k5_warn:
            result.warnings.append(k5_warn)

        # 7. 付帯条件の計算 (短絡・保護装置・制御線・曲げ半径・端子接触面積)
        if params.short_circuit_current_ka > 0 and params.short_circuit_duration_s > 0:
            sc_current_a = params.short_circuit_current_ka * 1000.0
            k_const = float(temp_info["short_circuit_k"])
            t_s = min(5.0, max(0.001, params.short_circuit_duration_s))
            result.min_short_circuit_csa_mm2 = (sc_current_a * math.sqrt(t_s)) / k_const
            if params.short_circuit_duration_s > 5.0:
                result.warnings.append("短絡・短時間電流の式 (Clause 4.2.7 / Annex F.2) は最大 5 秒までが対象です。")

        if params.protection_device_rating_a > 0:
            prot_csa = cls.get_protection_device_min_csa(
                params.protection_device_rating_a,
                params.installation_type_id,
            )
            result.protection_table3_csa_mm2 = prot_csa
            if params.ambient_temp_c > 45:
                result.warnings.append(
                    "Table 3（保護装置定格による選定）は周囲温度最大 45 ℃ までの条件で規定されています。"
                )

        if params.cable_application == "control":
            # Clause 4.2.2: 制御線は公称 5 A/mm2 基準かつ Clause 4.5 の最小断面積以上
            ctrl_csa = max(params.min_csa_override_mm2, eff_load / CONTROL_CABLE_CURRENT_DENSITY)
            result.control_cable_min_csa_mm2 = ctrl_csa

        # Table 4: 最小曲げ半径
        if params.is_screened:
            result.bending_radius_multiplier = 10
        else:
            result.bending_radius_multiplier = 4 if params.outer_diameter_mm <= 12.0 else 5
        result.min_bending_radius_mm = float(result.bending_radius_multiplier) * params.outer_diameter_mm

        # Clause 4.17.3: 銅接触面 (<= 1.4 A/mm2), アルミ接触面 (<= 0.8 A/mm2)
        result.min_copper_contact_area_mm2 = eff_load / 1.4
        result.min_aluminium_contact_area_mm2 = eff_load / 0.8

        # 8. 全標準断面積 (1.0〜400 mm2) の評価
        candidates: List[CSACandidateEvaluation] = []
        selected: Optional[CSACandidateEvaluation] = None

        min_csa_req = max(DEFAULT_MIN_CSA_MM2, params.min_csa_override_mm2)
        if params.min_csa_override_mm2 < DEFAULT_MIN_CSA_MM2:
            min_csa_req = params.min_csa_override_mm2
            result.warnings.append(
                f"最小断面積が {min_csa_req} mm2 に設定されています（Clause 4.5 により盤内配線・多芯ケーブル等の条件付き許容時のみ 1.0 mm2 未満が使用可能）。"
            )

        for csa in STANDARD_CSA_LIST:
            i_cable_90 = TABLE_B1_CURRENT_RATINGS[csa]
            i_cable_temp = i_cable_90 * k_star

            k4_csa = cls.calculate_k4(
                params.operation_mode,
                params.short_time_on_min,
                params.short_time_constant_mode,
                params.short_time_manual_tau_min,
                csa_mm2=csa,
            )

            derating = k1_val * k2_val * k3_val * k4_csa * k5_val
            total_factor = k_star * derating
            i_corr = i_cable_90 * total_factor

            margin_a = i_corr - eff_load
            margin_pct = ((i_corr - eff_load) / i_corr * 100.0) if i_corr > 0 else -100.0
            util_pct = (eff_load / i_corr * 100.0) if i_corr > 0 else 999.9
            safety_factor = (i_corr / eff_load) if eff_load > 0 else float("inf")

            sc_limit_a = cls.calculate_short_circuit_limit(
                csa,
                params.tc_max_c,
                params.short_circuit_duration_s if params.short_circuit_duration_s > 0 else 1.0,
            )

            meets_load = i_corr >= eff_load - 1e-9
            meets_min_csa = csa >= min_csa_req - 1e-9
            meets_sc = True
            if params.short_circuit_current_ka > 0:
                meets_sc = csa >= result.min_short_circuit_csa_mm2 - 1e-9

            meets_prot = True
            if result.protection_table3_csa_mm2 is not None:
                meets_prot = csa >= result.protection_table3_csa_mm2 - 1e-9

            meets_ctrl = True
            if result.control_cable_min_csa_mm2 is not None:
                meets_ctrl = csa >= result.control_cable_min_csa_mm2 - 1e-9

            if params.cable_application == "control":
                is_qualifying = meets_ctrl and meets_min_csa and meets_sc and meets_prot
            else:
                is_qualifying = meets_load and meets_min_csa and meets_sc and meets_prot

            status_reasons: List[str] = []
            if not meets_load and params.cable_application != "control":
                status_reasons.append("許容電流不足")
            if not meets_ctrl and params.cable_application == "control":
                status_reasons.append("制御線定格(5A/mm2)不足")
            if not meets_min_csa:
                status_reasons.append("最小断面積未満")
            if not meets_sc:
                status_reasons.append("短絡耐量不足")
            if not meets_prot:
                status_reasons.append("保護素子Table3未満")

            if is_qualifying:
                status_text = "適格 (OK)"
            else:
                status_text = "NG (" + "・".join(status_reasons) + ")"

            cand = CSACandidateEvaluation(
                csa_mm2=csa,
                i_cable_90_a=i_cable_90,
                i_cable_temp_a=i_cable_temp,
                k4_for_csa=k4_csa,
                derating_factor=derating,
                total_factor_from_90c=total_factor,
                i_corr_a=i_corr,
                margin_a=margin_a,
                margin_percent=margin_pct,
                utilization_percent=util_pct,
                safety_factor=safety_factor,
                short_circuit_limit_a=sc_limit_a,
                meets_load=meets_load,
                meets_min_csa=meets_min_csa,
                meets_short_circuit=meets_sc,
                meets_protection_table3=meets_prot,
                meets_control_rule=meets_ctrl,
                is_qualifying=is_qualifying,
                is_recommended=False,
                status_text=status_text,
            )

            if is_qualifying and selected is None:
                cand.is_recommended = True
                cand.status_text = "推奨 (最小要求断面積)"
                selected = cand

            candidates.append(cand)

        result.all_candidates = candidates
        result.selected_candidate = selected

        # 代表 k4 と要求基準許容電流のセット
        rep_k4 = selected.k4_for_csa if selected is not None else candidates[-1].k4_for_csa
        result.k4 = rep_k4
        result.combined_derating_factor = k1_val * k2_val * k3_val * rep_k4 * k5_val
        result.total_factor_from_90c = k_star * result.combined_derating_factor

        if result.combined_derating_factor > 0:
            result.required_i_cable_temp_a = eff_load / result.combined_derating_factor
        if result.total_factor_from_90c > 0:
            result.required_i_cable_90_a = eff_load / result.total_factor_from_90c

        if selected is not None:
            result.pull_out_forces_n = TABLE_G7_PULL_OUT_FORCE_N.get(selected.csa_mm2)
        else:
            result.warnings.append(
                "単一電線（最大 400 mm2）では要求条件を満たすサイズがありません。"
                "複数本の並列配線（バンドル分割）、より高い耐熱クラス（EN 50382 120℃/150℃）、"
                "または放熱性の高い敷設方式への変更を検討してください。"
            )

        return result
