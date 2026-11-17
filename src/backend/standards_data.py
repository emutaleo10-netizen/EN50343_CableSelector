"""BS EN 50343:2024 (Railway applications - Rolling stock - Rules for installation of cabling) 規格データ定義.

PDFから抽出した許容電流基本表（Table B.1）、補正係数表（Table 1, Table 2, Table 3,
Table A.1, Table C.1, Table D.1, Table E.1, Table E.2, Table F.1, Table F.2, Table 4, Table G.7）を保持する。
"""

from typing import Dict, List, Optional, Tuple

# 基準周囲温度 T_ref = 45 ℃ (318.15 K)
T_REF_C: float = 45.0
KELVIN_OFFSET: float = 273.15
T_REF_K: float = T_REF_C + KELVIN_OFFSET

# 基本表の基準最高導体温度 T_c(max) = 90 ℃ (363.15 K)
T_BASE_MAX_C: float = 90.0
T_BASE_MAX_K: float = T_BASE_MAX_C + KELVIN_OFFSET

# 銅の温度係数 (Annex C, Annex E: 0.004)
COPPER_ALPHA: float = 0.004

# Clause 4.5 車両内機器間配線の原則最小断面積 (mm2)
DEFAULT_MIN_CSA_MM2: float = 1.0

# Clause 4.2.2 制御用電線の公称電流密度 (A/mm2)
CONTROL_CABLE_CURRENT_DENSITY: float = 5.0

# Annex B, Table B.1: 標準壁厚電線・単芯・自由空気中・Tref=45℃・Tc(max)=90℃ の基準許容電流 I_cable (A)
# 公称断面積 (mm2) -> I_cable (A)
TABLE_B1_CURRENT_RATINGS: Dict[float, float] = {
    1.0: 20.0,
    1.5: 25.0,
    2.5: 33.0,
    4.0: 46.0,
    6.0: 60.0,
    10.0: 85.0,
    16.0: 110.0,
    25.0: 150.0,
    35.0: 190.0,
    50.0: 240.0,
    70.0: 300.0,
    95.0: 360.0,
    120.0: 425.0,
    150.0: 490.0,
    185.0: 560.0,
    240.0: 675.0,
    300.0: 775.0,
    400.0: 950.0,
}

# 標準断面積リスト (昇順)
STANDARD_CSA_LIST: List[float] = sorted(TABLE_B1_CURRENT_RATINGS.keys())

# Annex C (Table C.1) & Annex E (Table E.1) & Annex F (Table F.2):
# 耐熱クラス Tc(max) [℃] ごとの規格情報と換算係数 k*
TEMPERATURE_CLASSES: Dict[int, Dict[str, object]] = {
    90: {
        "tc_max": 90,
        "k_star_table": 1.00,
        "standard_family": "EN 50264 (全パート) / EN 50306 (薄肉 90℃)",
        "temp_20000h": 110,
        "short_circuit_k": 122,
        "short_circuit_temp_range": "90 ℃ → 200 ℃",
        "description": "標準耐熱クラス (90 ℃) - EN 50264 / EN 50306",
    },
    105: {
        "tc_max": 105,
        "k_star_table": 1.14,
        "standard_family": "EN 50306 (全パート・薄肉 105℃)",
        "temp_20000h": 125,
        "short_circuit_k": 122,
        "short_circuit_temp_range": "90 ℃ → 200 ℃ 準拠",
        "description": "中耐熱クラス (105 ℃) - EN 50306 薄肉電線",
    },
    120: {
        "tc_max": 120,
        "k_star_table": 1.26,
        "standard_family": "EN 50382 (全パート・高温用 120℃)",
        "temp_20000h": 140,
        "short_circuit_k": 126,
        "short_circuit_temp_range": "120 ℃ → 250 ℃",
        "description": "高耐熱クラス (120 ℃) - EN 50382 高温電力電線",
    },
    140: {
        "tc_max": 140,
        "k_star_table": 1.40,
        "standard_family": "Annex C / Annex D 規定 140℃クラス",
        "temp_20000h": 160,
        "short_circuit_k": 126,
        "short_circuit_temp_range": "120 ℃ → 250 ℃ 準拠",
        "description": "高耐熱クラス (140 ℃) - Annex C / Table C.1",
    },
    150: {
        "tc_max": 150,
        "k_star_table": 1.46,
        "standard_family": "EN 50382 (全パート・高温用 150℃)",
        "temp_20000h": 170,
        "short_circuit_k": 146,
        "short_circuit_temp_range": "150 ℃ → 350 ℃",
        "description": "最高耐熱クラス (150 ℃) - EN 50382 高温電力電線",
    },
}

# Clause 4.2.3 b, Table 1: 多芯ケーブル内の同時負荷芯数による補正係数 k5
# 芯数間の線形補間が認められている (1芯=単芯ケーブル時は 1.00)
TABLE_1_K5_MULTICORE: Dict[int, float] = {
    1: 1.00,
    2: 0.91,
    3: 0.78,
    4: 0.63,
    5: 0.59,
    7: 0.51,
    9: 0.46,
    12: 0.41,
    19: 0.38,
}

# Clause 4.2.3 b, Table 2 & Figure 2: 敷設方式および同時負荷電線本数による補正係数 k2
# Table 2 の8列すべてを忠実に定義する。
# - Type a): 自由空気中 (1本のみ 1.0、2本以上は対象外)
# - Type b): トレイ上・1層配列 (1本〜20本以上)
# - トレイ上・2層配列 (Cables on trays, in two layers): 2本を縦に積む設計はしないため2本は空欄(対象外)
# - Type c): トレイ上・多層配列 (Cables on trays, in several layers): 2本・3本を多層にする設計はしないため2本・3本は空欄(対象外)
# - Type d): 床面上または壁面上
# - Type e): 天井面または床下
# - Type f): 密閉チューブ・コンジット・密閉トレイ内
# - Type g): 断熱された密閉チューブ・コンジット内
INSTALLATION_TYPES: Dict[str, Dict[str, object]] = {
    "type_a": {
        "id": "type_a",
        "code": "Type a)",
        "label_ja": "Type a) 自由空気中（単一電線・離隔確保）",
        "header_en": "Cable in free air — Type a)",
        "description": (
            "単一電線を自由空気中に敷設。壁面から電線外径以上の離隔、隣接電線から互いの外径和以上の離隔を確保し、"
            "開口率15%以上（車体と熱接触良好な金属トレイ、それ以外は30%以上）のカバーなし穴あきトレイ・ラダー上に配置。"
        ),
        "table_factors": {
            1: 1.00,
        },
        "invalid_counts": list(range(2, 100)),
        "min_recommended_cables": 1,
        "max_recommended_cables": 1,
        "invalid_message": (
            "Type a)（自由空気中）は単一電線（1本）専用の敷設条件です（Table 2 にて2本以上は「-」）。"
            "複数本を束ねる・並べる場合は Type b) 以降の敷設方式を選択してください。"
        ),
    },
    "type_b": {
        "id": "type_b",
        "code": "Type b)",
        "label_ja": "Type b) トレイ上・1層配列（Cables on trays, in one layer）",
        "header_en": "Cables on trays, in one layer — Type b)",
        "description": (
            "Type a) と同等の開口率を持つカバーなし穴あきオープントレイまたはラダーサポート上に、"
            "電線同士を接触させて1層（横一列）で敷設（Figure 2 b）。"
        ),
        "table_factors": {
            1: 1.00,
            2: 0.87,
            3: 0.83,
            4: 0.78,
            8: 0.74,
            12: 0.73,
            16: 0.72,
            20: 0.71,
        },
        "invalid_counts": [],
        "min_recommended_cables": 1,
        "max_recommended_cables": 20,
        "invalid_message": "",
    },
    "trays_two_layers": {
        "id": "trays_two_layers",
        "code": "2 Layers (Tray)",
        "label_ja": "トレイ上・2層配列（Cables on trays, in two layers）",
        "header_en": "Cables on trays, in two layers",
        "description": (
            "穴あきオープントレイまたはラダーサポート上に電線を2層に重ねて敷設（Table 2 第3列）。"
            "2本のみを縦に2層積みする設計は行わないため、同時負荷本数2本は規格表で空欄（設計対象外）です。"
        ),
        "table_factors": {
            1: 1.00,
            3: 0.83,
            4: 0.71,
            8: 0.59,
            12: 0.54,
            16: 0.51,
            20: 0.47,
        },
        "invalid_counts": [2],
        "min_recommended_cables": 3,
        "max_recommended_cables": 20,
        "invalid_message": (
            "「トレイ上・2層配列（Cables on trays, in two layers）」では、電線2本のみを縦に積む設計は"
            "行わないため規格表（Table 2）で空欄（設計対象外）となっています。"
            "2本の場合は「Type b) トレイ上・1層配列」を選択するか、本数を3本以上に設定してください。"
        ),
    },
    "type_c": {
        "id": "type_c",
        "code": "Type c)",
        "label_ja": "Type c) トレイ上・多層配列（Cables on trays, in several layers）",
        "header_en": "Cables on trays, in several layers — Type c)",
        "description": (
            "穴あきオープントレイまたはラダーサポート上に電線を複数層（多層）に重ねて敷設（Figure 2 c）。"
            "2本や3本のみで多層積みする設計は行わないため、2本・3本は規格表で空欄（設計対象外）です。"
        ),
        "table_factors": {
            1: 1.00,
            4: 0.71,
            8: 0.52,
            12: 0.45,
            16: 0.41,
            20: 0.38,
        },
        "invalid_counts": [2, 3],
        "min_recommended_cables": 4,
        "max_recommended_cables": 20,
        "invalid_message": (
            "「Type c) トレイ上・多層配列（Cables on trays, in several layers）」では、電線2本または3本で"
            "多層にする設計は行わないため規格表（Table 2）で空欄（設計対象外）となっています。"
            "2〜3本の場合は「Type b) 1層配列」または「2層配列（3本）」を選択するか、本数を4本以上に設定してください。"
        ),
    },
    "type_d": {
        "id": "type_d",
        "code": "Type d)",
        "label_ja": "Type d) 床面上または壁面上（Cables on the floor or on a wall）",
        "header_en": "Cables on the floor or on a wall — Type d)",
        "description": "車両の床面上または壁面上に接触させて電線を敷設（Figure 2 d）。4本以上で係数 0.75 一定となります。",
        "table_factors": {
            1: 1.00,
            2: 0.85,
            3: 0.79,
            4: 0.75,
            8: 0.75,
            12: 0.75,
            16: 0.75,
            20: 0.75,
        },
        "invalid_counts": [],
        "min_recommended_cables": 1,
        "max_recommended_cables": 20,
        "invalid_message": "",
    },
    "type_e": {
        "id": "type_e",
        "code": "Type e)",
        "label_ja": "Type e) 天井面または床下（Cables on a ceiling or under floor）",
        "header_en": "Cables on a ceiling or under floor — Type e)",
        "description": "天井面の下側または床下構造の下面に沿って電線を敷設（Figure 2 e）。上方の放熱が制限されます。",
        "table_factors": {
            1: 0.95,
            2: 0.81,
            3: 0.72,
            4: 0.68,
            8: 0.62,
            12: 0.61,
            16: 0.61,
            20: 0.61,
        },
        "invalid_counts": [],
        "min_recommended_cables": 1,
        "max_recommended_cables": 20,
        "invalid_message": "",
    },
    "type_f": {
        "id": "type_f",
        "code": "Type f)",
        "label_ja": "Type f) 密閉チューブ・コンジット・密閉トレイ内（空気流動なし）",
        "header_en": "Cables in a closed tube, conduit or tray — Type f)",
        "description": (
            "有意な空気流動のない密閉チューブ、コンジット（電線管）、密閉トレイまたはボックス内に束ねて敷設（Figure 2 f）。"
            "保守・更新のため、チューブ内占有率は最大60%、トレイ・ダクト内は最大80%以下を推奨（Clause 4.12）。"
        ),
        "table_factors": {
            1: 0.95,
            2: 0.80,
            3: 0.70,
            4: 0.65,
            8: 0.52,
            12: 0.45,
            16: 0.41,
            20: 0.38,
        },
        "invalid_counts": [],
        "min_recommended_cables": 1,
        "max_recommended_cables": 20,
        "invalid_message": "",
    },
    "type_g": {
        "id": "type_g",
        "code": "Type g)",
        "label_ja": "Type g) 断熱された密閉チューブ・コンジット内（Thermally insulated）",
        "header_en": "Cables in a closed tube or conduit, thermally insulated — Type g)",
        "description": (
            "熱的に完全に断熱された密閉チューブ、コンジット、密閉トレイまたはボックス内に敷設（Figure 2 g）。"
            "放熱が最も厳しく、低減率が最大の敷設条件です。"
        ),
        "table_factors": {
            1: 0.76,
            2: 0.61,
            3: 0.53,
            4: 0.49,
            8: 0.40,
            12: 0.34,
            16: 0.31,
            20: 0.29,
        },
        "invalid_counts": [],
        "min_recommended_cables": 1,
        "max_recommended_cables": 20,
        "invalid_message": "",
    },
}

# Annex A, Table A.1: 短時間電流運転（OFF時間が熱時定数Tの5倍超）における補正係数 k4
# (t2 / T, k4) のペアリスト（昇順）
TABLE_A1_K4_SHORT_TIME: List[Tuple[float, float]] = [
    (0.60, 1.49),
    (0.75, 1.38),
    (0.90, 1.30),
    (1.20, 1.19),
    (1.50, 1.13),
    (1.80, 1.09),
    (2.10, 1.06),
    (2.40, 1.04),
    (2.70, 1.03),
    (3.00, 1.02),
]

# Annex E, Table E.2: 予測ケーブル寿命短縮時の温度偏差 ΔT (K) と寿命影響の説明
LIFETIME_DELTA_T_OPTIONS: Dict[int, Dict[str, object]] = {
    0: {
        "delta_t": 0,
        "label": "ΔT = 0 K（標準予測寿命 100,000時間 / 変更なし）",
        "expected_hours": 100000,
        "life_factor_desc": "標準寿命 (1/1)",
        "k3_90c_example": 1.00,
    },
    10: {
        "delta_t": 10,
        "label": "ΔT = +10 K（予測寿命 1/2：約 50,000時間）",
        "expected_hours": 50000,
        "life_factor_desc": "寿命 1/2 (半減)",
        "k3_90c_example": 1.10,
    },
    20: {
        "delta_t": 20,
        "label": "ΔT = +20 K（予測寿命 1/4：約 25,000時間）",
        "expected_hours": 25000,
        "life_factor_desc": "寿命 1/4",
        "k3_90c_example": 1.18,
    },
    30: {
        "delta_t": 30,
        "label": "ΔT = +30 K（予測寿命 1/8：約 12,500時間）",
        "expected_hours": 12500,
        "life_factor_desc": "寿命 1/8",
        "k3_90c_example": 1.26,
    },
}

# Clause 4.2.4, Table 3: 保護装置定格電流に基づく簡易導体サイズ選定表 (Tc(max) >= 90℃, 周囲温度 <= 45℃)
# 定格電流 (A) -> {"open_tray_or_free_air_max4": CSA (mm2), "closed_tube_max4": CSA (mm2)}
TABLE_3_PROTECTION_DEVICE_SIZING: Dict[int, Dict[str, float]] = {
    6: {"open_max4": 1.0, "closed_tube_max4": 1.0},
    10: {"open_max4": 1.0, "closed_tube_max4": 1.5},
    16: {"open_max4": 1.5, "closed_tube_max4": 2.5},
    20: {"open_max4": 2.5, "closed_tube_max4": 4.0},
    25: {"open_max4": 4.0, "closed_tube_max4": 6.0},
}

# Annex F, Table F.1: 90℃電線の1秒間推奨短絡許容電流 (90℃ → 200℃, k=122)
TABLE_F1_SHORT_CIRCUIT_1S_90C: Dict[float, int] = {
    1.0: 122,
    1.5: 183,
    2.5: 305,
    4.0: 488,
    6.0: 732,
    10.0: 1220,
    16.0: 1952,
    25.0: 3050,
    35.0: 4270,
    50.0: 6100,
    70.0: 8540,
    95.0: 11590,
    120.0: 14640,
    150.0: 18300,
    185.0: 22570,
    240.0: 29280,
    300.0: 36600,
    400.0: 48800,
}

# Annex G, Table G.7: 圧着接続の最小引張試験強度 (N)
# CSA (mm2) -> (オープンバレル, クローズドバレル, 絶縁付端子, 非絶縁銅端子)
TABLE_G7_PULL_OUT_FORCE_N: Dict[float, Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]] = {
    0.25: (32, 35, 32, None),
    0.50: (60, 70, 56, 75),
    0.75: (85, 100, 84, 112),
    1.0: (108, 130, 108, 150),
    1.5: (150, 195, 150, 225),
    2.5: (230, 325, 230, 375),
    4.0: (310, 520, 310, 600),
    6.0: (360, 780, 360, 780),
    10.0: (380, 1000, None, 1300),
    16.0: (None, 1600, None, 1600),
    25.0: (None, 2000, None, 2500),
    35.0: (None, 2800, None, 3500),
    50.0: (None, 3000, None, 4500),
    70.0: (None, 4200, None, 5250),
    95.0: (None, 5700, None, 5700),
    120.0: (None, 7200, None, 7200),
    150.0: (None, 9000, None, 9000),
    185.0: (None, 11100, None, 11100),
    240.0: (None, 14400, None, 14400),
    300.0: (None, None, None, 18000),
    400.0: (None, None, None, 20000),
    500.0: (None, None, None, 20000),
}
