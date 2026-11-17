"""右ペイン：電線選定結果カード・補正係数内訳・全サイズ比較テーブル表示パネル (CustomTkinter)."""

from typing import Dict, List

import customtkinter as ctk

from src.backend.models import CableSizingResult
from src.backend.standards_data import (
    INSTALLATION_TYPES,
    STANDARD_CSA_LIST,
    TABLE_1_K5_MULTICORE,
    TABLE_B1_CURRENT_RATINGS,
    TEMPERATURE_CLASSES,
)
from src.frontend.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD,
    COLOR_BG_SUBCARD,
    COLOR_BORDER_ACCENT,
    COLOR_BORDER_DEFAULT,
    COLOR_BORDER_RECOMMENDED,
    COLOR_DANGER,
    COLOR_DANGER_BG,
    COLOR_ROW_NG,
    COLOR_ROW_OK_EVEN,
    COLOR_ROW_OK_ODD,
    COLOR_ROW_RECOMMENDED,
    COLOR_SUCCESS,
    COLOR_SUCCESS_BG,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    COLOR_WARNING_BG,
    FONT_FAMILY_MONO,
    FONT_FAMILY_UI,
)
from src.utils.exporter import format_csa


class OutputPanel(ctk.CTkFrame):
    """計算結果をリアルタイムかつ視覚的に表示する右ペインダッシュボード."""

    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # テーブル行ウィジェットのキャッシュ (高速・チラつき防止のため事前生成)
        self._table_rows: Dict[float, Dict[str, object]] = {}
        self._factor_cards: Dict[str, Dict[str, object]] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        """出力エリアの全ウィジェットを構築する."""
        # --- Row 0: エラー / 警告バナー (必要時のみ表示) ---
        self._alert_banner = ctk.CTkFrame(
            self,
            fg_color=COLOR_DANGER_BG,
            corner_radius=10,
            border_width=2,
            border_color=COLOR_DANGER,
        )
        self._alert_banner.grid(row=0, column=0, padx=4, pady=(0, 8), sticky="ew")
        self._alert_banner.grid_columnconfigure(0, weight=1)

        self._alert_title_lbl = ctk.CTkLabel(
            self._alert_banner,
            text="",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_DANGER,
            anchor="w",
        )
        self._alert_title_lbl.grid(row=0, column=0, padx=14, pady=(8, 2), sticky="ew")

        self._alert_msg_lbl = ctk.CTkLabel(
            self._alert_banner,
            text="",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="w",
            wraplength=850,
        )
        self._alert_msg_lbl.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        self._alert_banner.grid_remove()

        # --- Row 1: 上段 4枚の大型サマリーカード ---
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.grid(row=1, column=0, padx=0, pady=(0, 8), sticky="ew")
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        # カード1: 最小要求断面積 (CSA)
        self._card_csa = ctk.CTkFrame(
            kpi_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=2,
            border_color=COLOR_BORDER_RECOMMENDED,
        )
        self._card_csa.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="nsew")
        self._card_csa.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._card_csa,
            text="最小要求断面積 (規格推奨)",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")

        self._csa_value_lbl = ctk.CTkLabel(
            self._card_csa,
            text="35 mm²",
            font=(FONT_FAMILY_UI, 28, "bold"),
            text_color=COLOR_SUCCESS,
        )
        self._csa_value_lbl.grid(row=1, column=0, padx=14, pady=(2, 2), sticky="w")

        self._csa_sub_lbl = ctk.CTkLabel(
            self._card_csa,
            text="Table B.1 基準許容電流: 190 A",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._csa_sub_lbl.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

        # カード2: 実使用許容電流 I_corr & 負荷電流 I_load
        self._card_icorr = ctk.CTkFrame(
            kpi_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        self._card_icorr.grid(row=0, column=1, padx=5, pady=2, sticky="nsew")
        self._card_icorr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._card_icorr,
            text="補正後許容電流 I_corr",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")

        self._icorr_value_lbl = ctk.CTkLabel(
            self._card_icorr,
            text="148.2 A",
            font=(FONT_FAMILY_UI, 26, "bold"),
            text_color=COLOR_ACCENT,
        )
        self._icorr_value_lbl.grid(row=1, column=0, padx=14, pady=(2, 2), sticky="w")

        self._icorr_sub_lbl = ctk.CTkLabel(
            self._card_icorr,
            text="実効負荷電流 I_load: 100.0 A",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._icorr_sub_lbl.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

        # カード3: 安全余裕度・電線負荷率
        self._card_margin = ctk.CTkFrame(
            kpi_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        self._card_margin.grid(row=0, column=2, padx=5, pady=2, sticky="nsew")
        self._card_margin.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._card_margin,
            text="安全余裕度・電線負荷率",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")

        self._margin_value_lbl = ctk.CTkLabel(
            self._card_margin,
            text="+48.2 A (余裕 32.5%)",
            font=(FONT_FAMILY_UI, 20, "bold"),
            text_color=COLOR_SUCCESS,
        )
        self._margin_value_lbl.grid(row=1, column=0, padx=14, pady=(4, 4), sticky="w")

        self._util_bar = ctk.CTkProgressBar(self._card_margin, height=10, corner_radius=5)
        self._util_bar.grid(row=2, column=0, padx=14, pady=(0, 2), sticky="ew")
        self._util_bar.set(0.67)

        self._util_sub_lbl = ctk.CTkLabel(
            self._card_margin,
            text="負荷率: 67.5% / 安全率: 1.48倍",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._util_sub_lbl.grid(row=3, column=0, padx=14, pady=(0, 8), sticky="w")

        # カード4: 総合補正係数・要求基準電流
        self._card_factor = ctk.CTkFrame(
            kpi_frame,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        self._card_factor.grid(row=0, column=3, padx=(5, 0), pady=2, sticky="nsew")
        self._card_factor.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self._card_factor,
            text="総合補正係数・要求基準値",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=14, pady=(10, 0), sticky="w")

        self._total_k_lbl = ctk.CTkLabel(
            self._card_factor,
            text="× 0.780",
            font=(FONT_FAMILY_UI, 24, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        )
        self._total_k_lbl.grid(row=1, column=0, padx=14, pady=(2, 2), sticky="w")

        self._req_icable_lbl = ctk.CTkLabel(
            self._card_factor,
            text="90℃基準要求 I_cable ≥ 128.2 A",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._req_icable_lbl.grid(row=2, column=0, padx=14, pady=(0, 10), sticky="w")

        # --- Row 2: 中段 適用補正係数の内訳カード (k*, k1, k2, k3, k4, k5) ---
        factors_container = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        factors_container.grid(row=2, column=0, padx=0, pady=(0, 8), sticky="ew")
        factors_container.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="fcard")

        header_row = ctk.CTkFrame(factors_container, fg_color="transparent")
        header_row.grid(row=0, column=0, columnspan=6, padx=14, pady=(8, 4), sticky="ew")
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="適用補正係数の内訳 (I_corr = I_cable,90 × k* × k1 × k2 × k3 × k4 × k5)",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self._formula_summary_lbl = ctk.CTkLabel(
            header_row,
            text="",
            font=(FONT_FAMILY_MONO, 11),
            text_color=COLOR_ACCENT,
        )
        self._formula_summary_lbl.grid(row=0, column=1, sticky="e")

        factor_defs = [
            ("k_star", "k* 耐熱クラス換算", "Annex C / Table C.1"),
            ("k1", "k1 周囲温度補正", "Clause 4.2.3 b (1℃刻み)"),
            ("k2", "k2 敷設・束線補正", "Table 2 / Figure 2"),
            ("k3", "k3 予測寿命補正", "Annex E / Table E.2"),
            ("k4", "k4 短時間運転補正", "Annex A / Table A.1"),
            ("k5", "k5 多芯ケーブル補正", "Table 1 (多芯同時負荷)"),
        ]

        for col_i, (f_key, f_title, f_ref) in enumerate(factor_defs):
            f_box = ctk.CTkFrame(
                factors_container,
                fg_color=COLOR_BG_SUBCARD,
                corner_radius=8,
                border_width=1,
                border_color=COLOR_BORDER_DEFAULT,
            )
            f_box.grid(row=1, column=col_i, padx=5, pady=(2, 10), sticky="nsew")
            f_box.grid_columnconfigure(0, weight=1)

            t_lbl = ctk.CTkLabel(
                f_box,
                text=f_title,
                font=(FONT_FAMILY_UI, 11, "bold"),
                text_color=COLOR_TEXT_SECONDARY,
            )
            t_lbl.grid(row=0, column=0, padx=8, pady=(6, 0), sticky="w")

            v_lbl = ctk.CTkLabel(
                f_box,
                text="1.000",
                font=(FONT_FAMILY_MONO, 18, "bold"),
                text_color=COLOR_TEXT_PRIMARY,
            )
            v_lbl.grid(row=1, column=0, padx=8, pady=(2, 2), sticky="w")

            p_bar = ctk.CTkProgressBar(f_box, height=6, corner_radius=3)
            p_bar.grid(row=2, column=0, padx=8, pady=(0, 3), sticky="ew")
            p_bar.set(1.0)

            d_lbl = ctk.CTkLabel(
                f_box,
                text=f_ref,
                font=(FONT_FAMILY_UI, 10),
                text_color=COLOR_TEXT_MUTED,
                anchor="w",
            )
            d_lbl.grid(row=3, column=0, padx=8, pady=(0, 6), sticky="ew")

            self._factor_cards[f_key] = {
                "box": f_box,
                "val_lbl": v_lbl,
                "bar": p_bar,
                "desc_lbl": d_lbl,
            }

        # --- Row 3: 下段 タブビュー (全断面積比較表 / 付帯技術検証 / 規格リファレンス表) ---
        self._tabview = ctk.CTkTabview(
            self,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            height=420,
        )
        self._tabview.grid(row=3, column=0, padx=0, pady=0, sticky="nsew")

        tab_table_name = "全断面積 (1〜400 mm²) リアルタイム比較表"
        tab_verify_name = "短絡耐量・曲げ半径・端子接触面積 検証"
        tab_ref_name = "EN 50343 規格係数リファレンス表"

        self._tabview.add(tab_table_name)
        self._tabview.add(tab_verify_name)
        self._tabview.add(tab_ref_name)

        self._build_comparison_table_tab(self._tabview.tab(tab_table_name))
        self._build_verification_tab(self._tabview.tab(tab_verify_name))
        self._build_reference_tab(self._tabview.tab(tab_ref_name))

    def _build_comparison_table_tab(self, parent: ctk.CTkFrame) -> None:
        """全18断面積の許容電流・余裕度・判定を一覧表示するタブを構築する."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        # テーブル固定ヘッダー
        hdr = ctk.CTkFrame(parent, fg_color=COLOR_BG_SUBCARD, corner_radius=6, height=34)
        hdr.grid(row=0, column=0, padx=6, pady=(4, 2), sticky="ew")
        col_weights = [10, 11, 11, 13, 13, 18, 12, 16]
        col_titles = [
            "公称断面積",
            "基準 I_cable(90℃)",
            "耐熱クラス基準",
            "実効許容 I_corr",
            "電流余裕 ΔI",
            "電線負荷率 (I_load / I_corr)",
            "短絡許容電流",
            "総合判定",
        ]
        for idx, (w, title) in enumerate(zip(col_weights, col_titles)):
            hdr.grid_columnconfigure(idx, weight=w, uniform="tbl_col")
            ctk.CTkLabel(
                hdr,
                text=title,
                font=(FONT_FAMILY_UI, 11, "bold"),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="center",
            ).grid(row=0, column=idx, padx=4, pady=6, sticky="ew")

        # スクロール領域
        scroll_tbl = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_tbl.grid(row=1, column=0, padx=2, pady=(0, 4), sticky="nsew")
        scroll_tbl.grid_columnconfigure(0, weight=1)

        for row_i, csa in enumerate(STANDARD_CSA_LIST):
            bg_col = COLOR_ROW_OK_EVEN if row_i % 2 == 0 else COLOR_ROW_OK_ODD
            row_frame = ctk.CTkFrame(
                scroll_tbl,
                fg_color=bg_col,
                corner_radius=6,
                border_width=1,
                border_color=COLOR_BORDER_DEFAULT,
            )
            row_frame.grid(row=row_i, column=0, padx=2, pady=2, sticky="ew")
            for idx, w in enumerate(col_weights):
                row_frame.grid_columnconfigure(idx, weight=w, uniform="tbl_col")

            lbl_csa = ctk.CTkLabel(
                row_frame,
                text=f"{format_csa(csa)} mm²",
                font=(FONT_FAMILY_MONO, 12, "bold"),
                anchor="center",
            )
            lbl_csa.grid(row=0, column=0, padx=4, pady=5, sticky="ew")

            lbl_i90 = ctk.CTkLabel(
                row_frame,
                text=f"{TABLE_B1_CURRENT_RATINGS[csa]:.0f} A",
                font=(FONT_FAMILY_MONO, 12),
                anchor="center",
            )
            lbl_i90.grid(row=0, column=1, padx=4, pady=5, sticky="ew")

            lbl_itemp = ctk.CTkLabel(
                row_frame,
                text="-",
                font=(FONT_FAMILY_MONO, 12),
                anchor="center",
            )
            lbl_itemp.grid(row=0, column=2, padx=4, pady=5, sticky="ew")

            lbl_icorr = ctk.CTkLabel(
                row_frame,
                text="-",
                font=(FONT_FAMILY_MONO, 12, "bold"),
                anchor="center",
            )
            lbl_icorr.grid(row=0, column=3, padx=4, pady=5, sticky="ew")

            lbl_margin = ctk.CTkLabel(
                row_frame,
                text="-",
                font=(FONT_FAMILY_MONO, 12),
                anchor="center",
            )
            lbl_margin.grid(row=0, column=4, padx=4, pady=5, sticky="ew")

            # 負荷率ゲージ + パーセント表示
            util_cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            util_cell.grid(row=0, column=5, padx=6, pady=3, sticky="ew")
            util_cell.grid_columnconfigure(0, weight=1)

            u_bar = ctk.CTkProgressBar(util_cell, height=8, corner_radius=4)
            u_bar.grid(row=0, column=0, padx=(2, 6), pady=4, sticky="ew")
            u_bar.set(0.5)

            lbl_util = ctk.CTkLabel(
                util_cell,
                text="50.0%",
                width=52,
                font=(FONT_FAMILY_MONO, 11),
                anchor="e",
            )
            lbl_util.grid(row=0, column=1, padx=2, sticky="e")

            lbl_sc = ctk.CTkLabel(
                row_frame,
                text="-",
                font=(FONT_FAMILY_MONO, 11),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="center",
            )
            lbl_sc.grid(row=0, column=6, padx=4, pady=5, sticky="ew")

            lbl_status = ctk.CTkLabel(
                row_frame,
                text="-",
                font=(FONT_FAMILY_UI, 11, "bold"),
                anchor="center",
            )
            lbl_status.grid(row=0, column=7, padx=6, pady=5, sticky="ew")

            self._table_rows[csa] = {
                "index": row_i,
                "frame": row_frame,
                "lbl_csa": lbl_csa,
                "lbl_i90": lbl_i90,
                "lbl_itemp": lbl_itemp,
                "lbl_icorr": lbl_icorr,
                "lbl_margin": lbl_margin,
                "u_bar": u_bar,
                "lbl_util": lbl_util,
                "lbl_sc": lbl_sc,
                "lbl_status": lbl_status,
            }

    def _build_verification_tab(self, parent: ctk.CTkFrame) -> None:
        """短絡電流・保護装置・曲げ半径・端子接触面積・圧着引張強度の検証タブを構築する."""
        parent.grid_columnconfigure((0, 1), weight=1)
        parent.grid_rowconfigure((0, 1), weight=1)

        # 1. 短絡電流・保護装置検証カード
        card_sc = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_SUBCARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        card_sc.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")
        card_sc.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_sc,
            text="短絡電流耐量・保護装置定格との整合性 (Clause 4.2.4, 4.2.7, Annex F.2)",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_ACCENT,
        ).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        self._verify_sc_text = ctk.CTkLabel(
            card_sc,
            text="",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="nw",
            wraplength=420,
        )
        self._verify_sc_text.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")

        # 2. 最小曲げ半径・固定間隔要件カード
        card_mech = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_SUBCARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        card_mech.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")
        card_mech.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_mech,
            text="最小曲げ半径・固定間隔・余長要件 (Clause 4.7, 4.8, 4.15)",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_ACCENT,
        ).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        self._verify_mech_text = ctk.CTkLabel(
            card_mech,
            text="",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="nw",
            wraplength=420,
        )
        self._verify_mech_text.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")

        # 3. 端子・バスバー接触面積と電流密度検証カード
        card_term = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_SUBCARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        card_term.grid(row=1, column=0, padx=8, pady=8, sticky="nsew")
        card_term.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_term,
            text="電気端子・バスバー有効接触面積要件 (Clause 4.17.3, 4.22)",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_ACCENT,
        ).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        self._verify_term_text = ctk.CTkLabel(
            card_term,
            text="",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="nw",
            wraplength=420,
        )
        self._verify_term_text.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")

        # 4. 圧着接続の引張試験強度 (Annex G, Table G.7)
        card_crimp = ctk.CTkFrame(
            parent,
            fg_color=COLOR_BG_SUBCARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        card_crimp.grid(row=1, column=1, padx=8, pady=8, sticky="nsew")
        card_crimp.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_crimp,
            text="圧着端子の最小引張強度 (Annex G, Table G.7)",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_ACCENT,
        ).grid(row=0, column=0, padx=14, pady=(12, 6), sticky="w")

        self._verify_crimp_text = ctk.CTkLabel(
            card_crimp,
            text="",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_PRIMARY,
            justify="left",
            anchor="nw",
            wraplength=420,
        )
        self._verify_crimp_text.grid(row=1, column=0, padx=14, pady=(0, 12), sticky="nsew")

    def _build_reference_tab(self, parent: ctk.CTkFrame) -> None:
        """BS EN 50343:2024 の主要規格テーブルをアプリ内で参照できるリファレンスビュー."""
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        ref_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        ref_scroll.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        ref_scroll.grid_columnconfigure(0, weight=1)

        ref_lines: List[str] = [
            "■ Table 2 — 敷設方式および同時負荷電線本数による補正係数 k2 (Clause 4.2.3 b)",
            "--------------------------------------------------------------------------------------------------------------------",
            f"{'本数':<6} | {'Type a(自由空気)':<15} | {'Type b(1層)':<12} | {'トレイ2層':<12} | {'Type c(多層)':<12} | {'Type d(床/壁)':<13} | {'Type e(天井)':<12} | {'Type f(管内)':<12} | {'Type g(断熱管)':<12}",
            "--------------------------------------------------------------------------------------------------------------------",
        ]
        for n in [1, 2, 3, 4, 8, 12, 16, 20]:
            n_lbl = "20+" if n == 20 else f"{n}"
            row_vals: List[str] = []
            for key in ["type_a", "type_b", "trays_two_layers", "type_c", "type_d", "type_e", "type_f", "type_g"]:
                tf = INSTALLATION_TYPES[key]["table_factors"]  # type: ignore[index]
                if n in tf:  # type: ignore[operator]
                    row_vals.append(f"{tf[n]:.2f}")  # type: ignore[index]
                else:
                    row_vals.append("- (対象外)")
            ref_lines.append(
                f"{n_lbl:<6} | {row_vals[0]:<15} | {row_vals[1]:<12} | {row_vals[2]:<12} | "
                f"{row_vals[3]:<12} | {row_vals[4]:<13} | {row_vals[5]:<12} | {row_vals[6]:<12} | {row_vals[7]:<12}"
            )

        ref_lines.extend([
            "",
            "■ Table 1 — 多芯ケーブル内の同時負荷芯数による補正係数 k5 (Clause 4.2.3 b)",
            "--------------------------------------------------------------------------------------------------------------------",
            "  同時負荷芯数 :   1芯(単芯) |   2芯  |   3芯  |   4芯  |   5芯  |   7芯  |   9芯  |  12芯  |  19芯",
            "  補正係数 k5  :     1.00    |  0.91  |  0.78  |  0.63  |  0.59  |  0.51  |  0.46  |  0.41  |  0.38",
            "",
            "■ Table C.1 & Table E.1 — 耐熱クラス別 換算係数 k* および対応規格ファミリー",
            "--------------------------------------------------------------------------------------------------------------------",
        ])
        for tc, info in TEMPERATURE_CLASSES.items():
            ref_lines.append(
                f"  Tc(max) = {tc:>3} ℃ : k* = {float(info['k_star_table']):.2f}  |  20,000h試験温度 = {info['temp_20000h']} ℃  |  {info['standard_family']}"
            )

        ref_textbox = ctk.CTkTextbox(
            ref_scroll,
            height=360,
            font=(FONT_FAMILY_MONO, 12),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            wrap="none",
        )
        ref_textbox.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        ref_textbox.insert("1.0", "\n".join(ref_lines))
        ref_textbox.configure(state="disabled")

    def update_result(self, result: CableSizingResult) -> None:
        """計算結果を画面全体にリアルタイム反映する."""
        p = result.input_params

        # 1. エラー・警告バナーの制御
        if not result.is_valid_configuration:
            self._alert_banner.configure(fg_color=COLOR_DANGER_BG, border_color=COLOR_DANGER)
            self._alert_title_lbl.configure(
                text="規格適用対象外の条件設定（Table 2 / 周囲温度制約）",
                text_color=COLOR_DANGER,
            )
            self._alert_msg_lbl.configure(text=result.error_message)
            self._alert_banner.grid()
        elif result.warnings:
            self._alert_banner.configure(fg_color=COLOR_WARNING_BG, border_color=COLOR_WARNING)
            self._alert_title_lbl.configure(
                text="設計上の注意事項・規格注記",
                text_color=COLOR_WARNING,
            )
            self._alert_msg_lbl.configure(text=" / ".join(result.warnings))
            self._alert_banner.grid()
        else:
            self._alert_banner.grid_remove()

        # 設定無効時のフォールバック表示
        if not result.is_valid_configuration:
            self._card_csa.configure(border_color=COLOR_DANGER)
            self._csa_value_lbl.configure(text="選定不可", text_color=COLOR_DANGER)
            self._csa_sub_lbl.configure(text="左ペインの敷設方式または温度を見直してください")
            self._icorr_value_lbl.configure(text="--- A", text_color=COLOR_TEXT_MUTED)
            self._icorr_sub_lbl.configure(text=f"実効負荷電流 I_load: {result.effective_load_current_a:.1f} A")
            self._margin_value_lbl.configure(text="---", text_color=COLOR_TEXT_MUTED)
            self._util_bar.set(0.0)
            self._util_sub_lbl.configure(text="計算対象外")
            self._total_k_lbl.configure(text="---")
            self._req_icable_lbl.configure(text="---")

            # 係数カード更新
            self._update_factor_cards_on_error(result)
            for csa, r_widgets in self._table_rows.items():
                r_widgets["frame"].configure(fg_color=COLOR_ROW_OK_EVEN, border_color=COLOR_BORDER_DEFAULT, border_width=1)  # type: ignore[attr-defined]
                r_widgets["lbl_itemp"].configure(text="-")  # type: ignore[attr-defined]
                r_widgets["lbl_icorr"].configure(text="-")  # type: ignore[attr-defined]
                r_widgets["lbl_margin"].configure(text="-")  # type: ignore[attr-defined]
                r_widgets["u_bar"].set(0.0)  # type: ignore[attr-defined]
                r_widgets["lbl_util"].configure(text="-")  # type: ignore[attr-defined]
                r_widgets["lbl_status"].configure(text="条件エラー", text_color=COLOR_DANGER)  # type: ignore[attr-defined]
            return

        # 2. サマリーカード4枚の更新
        sel = result.selected_candidate
        if sel is not None:
            self._card_csa.configure(border_color=COLOR_BORDER_RECOMMENDED)
            self._csa_value_lbl.configure(
                text=f"{format_csa(sel.csa_mm2)} mm²",
                text_color=COLOR_SUCCESS,
            )
            self._csa_sub_lbl.configure(
                text=f"基準(90℃): {sel.i_cable_90_a:.0f} A / {p.tc_max_c}℃基準: {sel.i_cable_temp_a:.1f} A"
            )

            self._icorr_value_lbl.configure(
                text=f"{sel.i_corr_a:.1f} A",
                text_color=COLOR_ACCENT,
            )
            self._icorr_sub_lbl.configure(
                text=f"実効負荷 I_load: {result.effective_load_current_a:.1f} A (入力 {p.load_current_a:.1f} A)"
            )

            # 余裕度と負荷率
            util_ratio = max(0.0, min(1.0, sel.utilization_percent / 100.0))
            self._util_bar.set(util_ratio)
            if sel.utilization_percent <= 85.0:
                m_col = COLOR_SUCCESS
                self._util_bar.configure(progress_color=COLOR_SUCCESS)
            else:
                m_col = COLOR_WARNING
                self._util_bar.configure(progress_color=COLOR_WARNING)

            self._margin_value_lbl.configure(
                text=f"+{sel.margin_a:.1f} A (余裕 {sel.margin_percent:.1f}%)",
                text_color=m_col,
            )
            sf_str = f"{sel.safety_factor:.2f}倍" if sel.safety_factor < 100 else "99+倍"
            self._util_sub_lbl.configure(
                text=f"負荷率: {sel.utilization_percent:.1f}% / 安全率: {sf_str}"
            )
        else:
            self._card_csa.configure(border_color=COLOR_DANGER)
            self._csa_value_lbl.configure(text="400 mm² 超", text_color=COLOR_DANGER)
            self._csa_sub_lbl.configure(text="単一電線では容量不足（並列配線が必要）")

            max_cand = result.all_candidates[-1]
            self._icorr_value_lbl.configure(
                text=f"最大 {max_cand.i_corr_a:.1f} A",
                text_color=COLOR_DANGER,
            )
            self._icorr_sub_lbl.configure(
                text=f"実効負荷 I_load: {result.effective_load_current_a:.1f} A"
            )
            self._margin_value_lbl.configure(
                text=f"{max_cand.margin_a:.1f} A (不足)",
                text_color=COLOR_DANGER,
            )
            self._util_bar.set(1.0)
            self._util_bar.configure(progress_color=COLOR_DANGER)
            self._util_sub_lbl.configure(
                text=f"400mm²での負荷率: {max_cand.utilization_percent:.1f}%"
            )

        self._total_k_lbl.configure(text=f"× {result.total_factor_from_90c:.3f}")
        self._req_icable_lbl.configure(
            text=f"要求基準値: {result.required_i_cable_90_a:.1f} A(90℃) / {result.required_i_cable_temp_a:.1f} A({p.tc_max_c}℃)"
        )

        # 3. 補正係数内訳カード6枚の更新
        self._formula_summary_lbl.configure(
            text=(
                f"k*({result.k_star:.2f}) × k1({result.k1:.3f}) × k2({result.k2:.2f}) "
                f"× k3({result.k3:.2f}) × k4({result.k4:.2f}) × k5({result.k5:.2f}) "
                f"= {result.total_factor_from_90c:.3f}"
            )
        )

        self._set_factor_card(
            "k_star",
            f"{result.k_star:.2f}",
            min(1.0, result.k_star / 1.5),
            f"Tc(max)={p.tc_max_c}℃ (式:{result.k_star_formula_exact:.2f})",
        )
        self._set_factor_card(
            "k1",
            f"{result.k1:.3f}" if not p.use_table_d1_rounded_k1 else f"{result.k1:.2f}",
            min(1.0, max(0.0, result.k1 / 1.2)),
            f"周囲 T={p.ambient_temp_c}℃ (丸め:{result.k1_rounded_2dec:.2f})",
        )
        inst_code = str(INSTALLATION_TYPES.get(p.installation_type_id, {}).get("code", p.installation_type_id))
        k2_note = f"{inst_code} / {p.num_bundled_cables}本" + ("(補間)" if result.k2_is_interpolated else "")
        self._set_factor_card(
            "k2",
            f"{result.k2:.3f}" if result.k2_is_interpolated else f"{result.k2:.2f}",
            min(1.0, max(0.0, result.k2 or 0.0)),
            k2_note,
        )
        self._set_factor_card(
            "k3",
            f"{result.k3:.2f}",
            min(1.0, result.k3 / 1.3),
            f"ΔT=+{p.lifetime_delta_t_k}K ({result.expected_lifetime_hours // 1000}kh)",
        )
        st_desc = "連続/周期運転" if p.operation_mode != "short_time" else f"短時間 t2={p.short_time_on_min:.1f}分"
        self._set_factor_card(
            "k4",
            f"{result.k4:.2f}",
            min(1.0, result.k4 / 1.5),
            st_desc,
        )
        mc_desc = "単芯 (1芯)" if not p.is_multicore else f"多芯 ({p.num_loaded_cores}芯負荷)"
        self._set_factor_card(
            "k5",
            f"{result.k5:.3f}" if result.k5_is_interpolated else f"{result.k5:.2f}",
            min(1.0, max(0.0, result.k5)),
            mc_desc,
        )

        # 4. 全断面積比較テーブルの更新
        for cand in result.all_candidates:
            rw = self._table_rows[cand.csa_mm2]
            idx = int(rw["index"])  # type: ignore[arg-type]
            frame: ctk.CTkFrame = rw["frame"]  # type: ignore[assignment]

            if cand.is_recommended:
                frame.configure(
                    fg_color=COLOR_ROW_RECOMMENDED,
                    border_color=COLOR_BORDER_RECOMMENDED,
                    border_width=2,
                )
            elif cand.is_qualifying:
                bg = COLOR_ROW_OK_EVEN if idx % 2 == 0 else COLOR_ROW_OK_ODD
                frame.configure(fg_color=bg, border_color=COLOR_BORDER_DEFAULT, border_width=1)
            else:
                frame.configure(fg_color=COLOR_ROW_NG, border_color=COLOR_BORDER_DEFAULT, border_width=1)

            rw["lbl_itemp"].configure(text=f"{cand.i_cable_temp_a:.1f} A")  # type: ignore[attr-defined]
            rw["lbl_icorr"].configure(  # type: ignore[attr-defined]
                text=f"{cand.i_corr_a:.1f} A",
                text_color=COLOR_SUCCESS if cand.is_recommended else COLOR_TEXT_PRIMARY,
            )

            m_sign = "+" if cand.margin_a >= 0 else ""
            rw["lbl_margin"].configure(  # type: ignore[attr-defined]
                text=f"{m_sign}{cand.margin_a:.1f} A ({cand.margin_percent:.0f}%)",
                text_color=COLOR_SUCCESS if cand.margin_a >= 0 else COLOR_DANGER,
            )

            u_bar: ctk.CTkProgressBar = rw["u_bar"]  # type: ignore[assignment]
            u_bar.set(max(0.0, min(1.0, cand.utilization_percent / 100.0)))
            if cand.utilization_percent > 100.0:
                u_bar.configure(progress_color=COLOR_DANGER)
            elif cand.utilization_percent > 85.0:
                u_bar.configure(progress_color=COLOR_WARNING)
            else:
                u_bar.configure(progress_color=COLOR_SUCCESS)

            rw["lbl_util"].configure(  # type: ignore[attr-defined]
                text=f"{cand.utilization_percent:.1f}%",
                text_color=COLOR_DANGER if cand.utilization_percent > 100.0 else COLOR_TEXT_PRIMARY,
            )
            rw["lbl_sc"].configure(text=f"{cand.short_circuit_limit_a / 1000.0:.2f} kA")  # type: ignore[attr-defined]

            if cand.is_recommended:
                s_col = COLOR_SUCCESS
            elif cand.is_qualifying:
                s_col = COLOR_ACCENT
            else:
                s_col = COLOR_DANGER
            rw["lbl_status"].configure(text=cand.status_text, text_color=s_col)  # type: ignore[attr-defined]

        # 5. 付帯技術検証タブの更新
        self._update_verification_tab_contents(result)

    def _set_factor_card(self, key: str, val_str: str, ratio: float, desc_str: str) -> None:
        fc = self._factor_cards[key]
        fc["val_lbl"].configure(text=val_str, text_color=COLOR_TEXT_PRIMARY)  # type: ignore[attr-defined]
        fc["bar"].set(ratio)  # type: ignore[attr-defined]
        fc["desc_lbl"].configure(text=desc_str)  # type: ignore[attr-defined]

    def _update_factor_cards_on_error(self, result: CableSizingResult) -> None:
        p = result.input_params
        self._formula_summary_lbl.configure(text="条件エラーのため計算停止中")
        self._set_factor_card("k_star", f"{result.k_star:.2f}", 0.5, f"Tc(max)={p.tc_max_c}℃")
        self._set_factor_card(
            "k1",
            f"{result.k1:.3f}" if result.k1 > 0 else "対象外",
            0.0,
            f"周囲 T={p.ambient_temp_c}℃",
        )
        self._set_factor_card(
            "k2",
            f"{result.k2:.2f}" if result.k2 is not None else "対象外",
            0.0,
            "Table 2 対象外",
        )

    def _update_verification_tab_contents(self, result: CableSizingResult) -> None:
        p = result.input_params
        sel = result.selected_candidate
        sel_csa_str = f"{format_csa(sel.csa_mm2)} mm²" if sel else "未選定"

        # 1) 短絡・保護装置
        sc_lines = [
            f"・選定断面積: {sel_csa_str}",
            f"・短絡計算定数 K (Table F.2): {TEMPERATURE_CLASSES[p.tc_max_c]['short_circuit_k']} ({TEMPERATURE_CLASSES[p.tc_max_c]['short_circuit_temp_range']})",
        ]
        if sel is not None:
            sc_lines.append(
                f"・選定サイズの許容短絡電流 ({p.short_circuit_duration_s:.2f}秒): {sel.short_circuit_limit_a:,.0f} A ({sel.short_circuit_limit_a / 1000.0:.2f} kA)"
            )
        if p.short_circuit_current_ka > 0:
            sc_lines.append(
                f"・入力短絡電流 {p.short_circuit_current_ka:.2f} kA ({p.short_circuit_duration_s:.2f}秒) に対する必要最小断面積: {result.min_short_circuit_csa_mm2:.2f} mm²"
            )
        else:
            sc_lines.append("・短絡電流条件: 未指定（左ペインで短絡電流 kA を入力すると自動検証します）")

        if result.protection_table3_csa_mm2 is not None:
            sc_lines.append(
                f"・保護装置定格 ({p.protection_device_rating_a} A, Table 3) の要求断面積: {format_csa(result.protection_table3_csa_mm2)} mm² 以上"
            )
        else:
            sc_lines.append("・保護装置定格 (Table 3): 指定なし")
        self._verify_sc_text.configure(text="\n".join(sc_lines))

        # 2) 曲げ半径・固定間隔・余長
        fix_interval = "150 mm 以下 (外径 ≤ 5mm 低電力単芯)" if (not p.is_multicore and p.outer_diameter_mm <= 5.0) else "250 mm 以下 (電力単芯・多芯ケーブル)"
        reterm_count = "最低 3 回分の再端末処理余長 (≤ 16 mm²)" if (sel and sel.csa_mm2 <= 16.0) else "最低 1 回分の再端末処理余長 (> 16 mm²)"
        mech_lines = [
            f"・ケーブル外径 D = {p.outer_diameter_mm:.1f} mm / {'シールドあり' if p.is_screened else 'シールドなし'}",
            f"・最小内部曲げ半径 R (Table 4): {result.min_bending_radius_mm:.1f} mm ({result.bending_radius_multiplier} × D)",
            f"・最大固定間隔 (Clause 4.15): {fix_interval}",
            "  （コンジット・チューブ自体は水平300mm / 垂直500mm間隔以下で固定）",
            f"・端末余長要件 (Clause 4.8): {reterm_count}",
        ]
        self._verify_mech_text.configure(text="\n".join(mech_lines))

        # 3) 端子・バスバー接触面積
        term_lines = [
            f"・実効負荷電流 I_load = {result.effective_load_current_a:.2f} A",
            f"・銅 (Cu) 接触面の最小有効面積 (≤ 1.4 A/mm²): {result.min_copper_contact_area_mm2:.2f} mm²",
            f"・アルミ (Al) 接触面の最小有効面積 (≤ 0.8 A/mm²): {result.min_aluminium_contact_area_mm2:.2f} mm²",
            "・有効接触面積計算式 (Clause 4.17.3): A = D² - (π × d²) / 4",
            "  （D: スラストワッシャ外径または端子幅、d: ボルト穴内径）",
            "・1ボルトあたりの最大圧着端子枚数: 電力用2枚(バスバー)/3枚(絶縁スタッド)、アース・制御用3〜4枚",
        ]
        self._verify_term_text.configure(text="\n".join(term_lines))

        # 4) 圧着引張試験強度 (Table G.7)
        crimp_lines = [f"・選定断面積: {sel_csa_str} (EN 60228 Class 5 / Class 6 撚線導体)"]
        if result.pull_out_forces_n is not None:
            f_open, f_closed, f_ins, f_non_ins = result.pull_out_forces_n
            crimp_lines.extend([
                f"  - オープンバレル圧着端子 (EN 60352-2)  : {str(f_open) + ' N' if f_open else '対象外 (>10mm²)'}",
                f"  - クローズドバレル端子 (切削バレル)     : {str(f_closed) + ' N' if f_closed else '対象外 (>240mm²)'}",
                f"  - 絶縁被覆付圧着端子 (リング/クリップ)  : {str(f_ins) + ' N' if f_ins else '対象外 (>6mm²)'}",
                f"  - 非絶縁銅圧着ラグ (DIN 46235 等)      : {str(f_non_ins) + ' N' if f_non_ins else '対象外'}",
            ])
        else:
            crimp_lines.append("  - 該当する断面積の引張強度データなし")
        self._verify_crimp_text.configure(text="\n".join(crimp_lines))
