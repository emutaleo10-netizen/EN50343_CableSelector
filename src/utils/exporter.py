"""計算結果のCSVおよびテキストレポート出力ユーティリティ."""

import csv
from datetime import datetime
from pathlib import Path

from src.backend.models import CableSizingResult
from src.backend.standards_data import INSTALLATION_TYPES


def format_csa(csa: float) -> str:
    """断面積を見やすい文字列に整形する (例: 1.0 -> '1', 1.5 -> '1.5')."""
    if abs(csa - round(csa)) < 1e-6:
        return f"{int(round(csa))}"
    return f"{csa:.2f}".rstrip("0").rstrip(".")


def generate_text_report(result: CableSizingResult) -> str:
    """BS EN 50343:2024 電線選定計算書のテキストレポートを生成する."""
    p = result.input_params
    inst = INSTALLATION_TYPES.get(p.installation_type_id, {})
    inst_label = str(inst.get("label_ja", p.installation_type_id))
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "========================================================================",
        " BS EN 50343:2024 鉄道車両用電線サイズ選定 計算報告書",
        f" 作成日時: {now_str}",
        "========================================================================",
        "",
        "[1. 入力設計条件]",
        f"  ・用途区分             : {'電力配電用ケーブル (Clause 4.2.3)' if p.cable_application == 'power' else '制御・信号用ケーブル (Clause 4.2.2)'}",
        f"  ・入力負荷電流 I       : {p.load_current_a:.2f} A",
        f"  ・運転モード           : {p.operation_mode}",
        f"  ・実効負荷電流 I_load  : {result.effective_load_current_a:.2f} A",
        f"  ・耐熱クラス Tc(max)   : {p.tc_max_c} ℃ ({result.standard_family_name})",
        f"  ・周囲温度 T           : {p.ambient_temp_c} ℃ (基準周囲温度 Tref = 45 ℃)",
        f"  ・敷設方式 (Table 2)   : {inst_label}",
        f"  ・同時負荷電線本数     : {p.num_bundled_cables} 本",
        f"  ・電線構造             : {'多芯ケーブル (' + str(p.num_loaded_cores) + '芯同時負荷)' if p.is_multicore else '単芯ケーブル (1芯)'}",
        f"  ・予測寿命設定         : ΔT = +{p.lifetime_delta_t_k} K (推定寿命 {result.expected_lifetime_hours:,} 時間)",
        "",
    ]

    if not result.is_valid_configuration:
        lines.extend([
            "[2. 判定結果: 設定条件エラー（規格適用対象外）]",
            f"  ・理由: {result.error_message}",
            "========================================================================",
        ])
        return "\n".join(lines)

    k2_str = f"{result.k2:.3f}" if result.k2 is not None else "N/A"
    lines.extend([
        "[2. 適用補正係数の内訳 (Clause 4.2.3 b & Annex A〜E)]",
        f"  ・耐熱クラス換算係数 k* : {result.k_star:.3f} (理論式計算値: {result.k_star_formula_exact:.3f})",
        f"  ・周囲温度補正係数 k1   : {result.k1:.3f} (厳密値: {result.k1_exact:.3f}, 小数2位丸め: {result.k1_rounded_2dec:.2f})",
        f"  ・敷設・束線補正係数 k2 : {k2_str} {'(線形補間適用)' if result.k2_is_interpolated else '(Table 2 規定値)'}",
        f"  ・予測寿命補正係数 k3   : {result.k3:.3f}",
        f"  ・短時間運転補正係数 k4 : {result.k4:.3f}",
        f"  ・多芯ケーブル補正 k5   : {result.k5:.3f} {'(線形補間適用)' if result.k5_is_interpolated else ''}",
        f"  ・低減係数積 (k1〜k5)   : {result.combined_derating_factor:.4f}",
        f"  ・90℃基準からの総合係数 : {result.total_factor_from_90c:.4f}",
        f"  ・要求基準許容電流      : {result.required_i_cable_temp_a:.2f} A ({p.tc_max_c}℃クラス基準) / {result.required_i_cable_90_a:.2f} A (90℃ Table B.1基準)",
        "",
    ])

    sel = result.selected_candidate
    lines.append("[3. 電線サイズ選定結果]")
    if sel is not None:
        lines.extend([
            f"  ・推奨最小導体断面積    : {format_csa(sel.csa_mm2)} mm2",
            f"  ・基準許容電流 (90℃)   : {sel.i_cable_90_a:.1f} A (Table B.1)",
            f"  ・耐熱クラス補正後基準  : {sel.i_cable_temp_a:.1f} A ({p.tc_max_c}℃)",
            f"  ・実使用許容電流 I_corr : {sel.i_corr_a:.2f} A",
            f"  ・安全余裕電流 (ΔI)     : +{sel.margin_a:.2f} A",
            f"  ・安全余裕率            : {sel.margin_percent:.1f} % (電線負荷率: {sel.utilization_percent:.1f} %, 安全率: {sel.safety_factor:.2f} 倍)",
            f"  ・許容短絡電流          : {sel.short_circuit_limit_a:.0f} A ({p.short_circuit_duration_s:.2f} 秒間)",
        ])
    else:
        lines.append("  ・推奨最小導体断面積    : 適格サイズなし (400 mm2 でも容量不足)")

    lines.extend([
        "",
        "[4. 付帯技術要件 (Clause 4.7, 4.17.3, Annex G)]",
        f"  ・最小内部曲げ半径 R    : {result.min_bending_radius_mm:.1f} mm ({result.bending_radius_multiplier} x D, 外径 D={p.outer_diameter_mm:.1f} mm)",
        f"  ・最小有効接触面積 (銅) : {result.min_copper_contact_area_mm2:.2f} mm2 (最大電流密度 1.4 A/mm2)",
        f"  ・最小有効接触面積 (Al) : {result.min_aluminium_contact_area_mm2:.2f} mm2 (最大電流密度 0.8 A/mm2)",
    ])

    if result.warnings:
        lines.append("")
        lines.append("[5. 注意事項・警告]")
        for w in result.warnings:
            lines.append(f"  ・{w}")

    lines.extend([
        "",
        "[6. 全標準断面積 (Table B.1) 比較一覧]",
        f"{'断面積(mm2)':>10} | {'基準90℃(A)':>10} | {'耐熱基準(A)':>10} | {'実効I_corr(A)':>12} | {'余裕(A)':>9} | {'負荷率(%)':>9} | 判定",
        "-" * 84,
    ])
    for c in result.all_candidates:
        mark = ">> " if c.is_recommended else "   "
        lines.append(
            f"{mark}{format_csa(c.csa_mm2):>7} | {c.i_cable_90_a:>10.1f} | {c.i_cable_temp_a:>10.1f} | "
            f"{c.i_corr_a:>12.2f} | {c.margin_a:>+9.2f} | {c.utilization_percent:>8.1f}% | {c.status_text}"
        )

    lines.append("========================================================================")
    return "\n".join(lines)


def export_csv_report(filepath: Path, result: CableSizingResult) -> None:
    """全断面積の計算結果および条件サマリーをCSVファイルに出力する."""
    p = result.input_params
    with filepath.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["BS EN 50343:2024 鉄道車両向け電線選定 計算結果データ"])
        writer.writerow([
            "入力負荷電流(A)",
            "実効負荷電流I_load(A)",
            "耐熱クラスTc(max)(℃)",
            "周囲温度T(℃)",
            "敷設方式ID",
            "同時負荷電線本数",
            "多芯フラグ",
            "同時負荷芯数",
            "k*",
            "k1",
            "k2",
            "k3",
            "k4",
            "k5",
            "総合係数(90℃比)",
        ])
        writer.writerow([
            f"{p.load_current_a:.2f}",
            f"{result.effective_load_current_a:.2f}",
            p.tc_max_c,
            p.ambient_temp_c,
            p.installation_type_id,
            p.num_bundled_cables,
            p.is_multicore,
            p.num_loaded_cores,
            f"{result.k_star:.4f}",
            f"{result.k1:.4f}",
            f"{result.k2:.4f}" if result.k2 is not None else "N/A",
            f"{result.k3:.4f}",
            f"{result.k4:.4f}",
            f"{result.k5:.4f}",
            f"{result.total_factor_from_90c:.4f}",
        ])
        writer.writerow([])
        writer.writerow([
            "公称断面積(mm2)",
            "基準許容電流_90℃(A)",
            "耐熱補正後基準電流(A)",
            "短時間係数k4",
            "実使用許容電流_I_corr(A)",
            "電流余裕(A)",
            "安全余裕率(%)",
            "負荷率(%)",
            "安全率(倍)",
            "許容短絡電流(A)",
            "推奨フラグ",
            "判定ステータス",
        ])
        for c in result.all_candidates:
            writer.writerow([
                format_csa(c.csa_mm2),
                f"{c.i_cable_90_a:.1f}",
                f"{c.i_cable_temp_a:.1f}",
                f"{c.k4_for_csa:.3f}",
                f"{c.i_corr_a:.2f}",
                f"{c.margin_a:.2f}",
                f"{c.margin_percent:.1f}",
                f"{c.utilization_percent:.1f}",
                f"{c.safety_factor:.2f}" if c.safety_factor < 1e6 else "INF",
                f"{c.short_circuit_limit_a:.0f}",
                "推奨" if c.is_recommended else "",
                c.status_text,
            ])
