"""電線選定エンジンの入出力データモデル定義."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class CableSizingInput:
    """電線選定の入力パラメータ群."""

    # 1. 負荷電流・運転モード条件
    load_current_a: float = 100.0
    operation_mode: str = "continuous"  # "continuous" | "cyclic" | "short_time"
    cyclic_on_sec: float = 480.0
    cyclic_total_sec: float = 520.0
    short_time_on_min: float = 3.0
    short_time_constant_mode: str = "empirical"  # "empirical" | "manual"
    short_time_manual_tau_min: float = 2.0

    # 2. 電線仕様・耐熱クラス・多芯条件
    tc_max_c: int = 90  # 90, 105, 120, 140, 150
    is_multicore: bool = False
    num_loaded_cores: int = 1  # 単芯時は1, 多芯時は2〜19
    cable_application: str = "power"  # "power" (4.2.3) | "control" (4.2.2)

    # 3. 周囲温度 (1℃刻み)・敷設条件
    ambient_temp_c: int = 45
    use_table_d1_rounded_k1: bool = False
    installation_type_id: str = "type_b"
    num_bundled_cables: int = 4

    # 4. 寿命・保護・短絡・機械的条件
    lifetime_delta_t_k: int = 0  # 0, 10, 20, 30
    min_csa_override_mm2: float = 1.0  # Clause 4.5 原則 1.0 mm2
    short_circuit_current_ka: float = 0.0  # 0.0 の場合は短絡チェック無効
    short_circuit_duration_s: float = 1.0  # 最大 5.0 秒
    protection_device_rating_a: int = 0  # 0=未指定, 6, 10, 16, 20, 25
    is_screened: bool = False
    outer_diameter_mm: float = 10.0


@dataclass
class CSACandidateEvaluation:
    """各標準断面積 (1.0〜400 mm2) ごとの評価結果."""

    csa_mm2: float
    i_cable_90_a: float
    i_cable_temp_a: float
    k4_for_csa: float
    derating_factor: float
    total_factor_from_90c: float
    i_corr_a: float
    margin_a: float
    margin_percent: float
    utilization_percent: float
    safety_factor: float
    short_circuit_limit_a: float
    meets_load: bool
    meets_min_csa: bool
    meets_short_circuit: bool
    meets_protection_table3: bool
    meets_control_rule: bool
    is_qualifying: bool
    is_recommended: bool = False
    status_text: str = ""


@dataclass
class CableSizingResult:
    """電線選定計算の総合出力結果."""

    input_params: CableSizingInput
    is_valid_configuration: bool = True
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    # ステップ a: 実効負荷電流
    effective_load_current_a: float = 0.0

    # ステップ b: 各種補正係数
    k_star: float = 1.0
    k_star_formula_exact: float = 1.0
    k1: float = 1.0
    k1_exact: float = 1.0
    k1_rounded_2dec: float = 1.0
    k2: Optional[float] = 1.0
    k2_is_interpolated: bool = False
    k3: float = 1.0
    k4: float = 1.0
    k5: float = 1.0
    k5_is_interpolated: bool = False

    # 総合係数と要求基準許容電流
    combined_derating_factor: float = 1.0  # k1 * k2 * k3 * k4 * k5
    total_factor_from_90c: float = 1.0  # k* * k1 * k2 * k3 * k4 * k5
    required_i_cable_temp_a: float = 0.0  # I_load / (k1*k2*k3*k4*k5)
    required_i_cable_90_a: float = 0.0  # I_load / (k* * k1*k2*k3*k4*k5)

    # ステップ c: 選定された推奨断面積と全候補リスト
    selected_candidate: Optional[CSACandidateEvaluation] = None
    all_candidates: List[CSACandidateEvaluation] = field(default_factory=list)

    # 付帯検証情報 (短絡・保護装置・制御線・曲げ半径・端子接触面積・引張強度)
    min_short_circuit_csa_mm2: float = 0.0
    protection_table3_csa_mm2: Optional[float] = None
    control_cable_min_csa_mm2: Optional[float] = None
    bending_radius_multiplier: int = 4
    min_bending_radius_mm: float = 40.0
    min_copper_contact_area_mm2: float = 0.0
    min_aluminium_contact_area_mm2: float = 0.0
    pull_out_forces_n: Optional[Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]] = None
    standard_family_name: str = ""
    expected_lifetime_hours: int = 100000
