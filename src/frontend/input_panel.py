"""左ペイン：電線選定条件の入力パネル (CustomTkinter)."""

from typing import Callable, Dict, List

import customtkinter as ctk

from src.backend.models import CableSizingInput
from src.backend.standards_data import (
    INSTALLATION_TYPES,
    LIFETIME_DELTA_T_OPTIONS,
    TEMPERATURE_CLASSES,
)
from src.frontend.theme import (
    COLOR_ACCENT,
    COLOR_BG_CARD,
    COLOR_BG_SUBCARD,
    COLOR_BORDER_DEFAULT,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FONT_FAMILY_UI,
)


class InputPanel(ctk.CTkScrollableFrame):
    """エンジニアが直感的にパラメータを設定できる左ペイン入力フォーム."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        on_change_callback: Callable[[CableSizingInput], None],
        on_export_csv_callback: Callable[[], None],
        on_export_txt_callback: Callable[[], None],
        width: int = 430,
    ) -> None:
        super().__init__(
            master,
            width=width,
            fg_color=COLOR_BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        self._on_change = on_change_callback
        self._on_export_csv = on_export_csv_callback
        self._on_export_txt = on_export_txt_callback
        self._updating_ui = False

        # 内部保持パラメータ
        self._state = CableSizingInput()

        # ドロップダウン表示名とIDのマッピング
        self._inst_label_to_id: Dict[str, str] = {}
        self._inst_id_to_label: Dict[str, str] = {}
        for inst_id, info in INSTALLATION_TYPES.items():
            label = str(info["label_ja"])
            self._inst_label_to_id[label] = inst_id
            self._inst_id_to_label[inst_id] = label

        self._life_label_to_dt: Dict[str, int] = {}
        self._life_dt_to_label: Dict[int, str] = {}
        for dt_val, l_info in LIFETIME_DELTA_T_OPTIONS.items():
            lbl = str(l_info["label"])
            self._life_label_to_dt[lbl] = dt_val
            self._life_dt_to_label[dt_val] = lbl

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self._sync_ui_from_state()

    def _build_ui(self) -> None:
        """入力UIセクションを構築する."""
        row_idx = 0

        # --- セクション0: プリセット読込バー ---
        preset_card = self._create_section_card(row_idx, "クイックプリセット（規格計算例・代表条件）")
        row_idx += 1

        preset_btn_frame = ctk.CTkFrame(preset_card, fg_color="transparent")
        preset_btn_frame.grid(row=1, column=0, padx=10, pady=(2, 8), sticky="ew")
        preset_btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            preset_btn_frame,
            text="標準条件 (100A / 45℃)",
            height=28,
            font=(FONT_FAMILY_UI, 11),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            hover_color=COLOR_BORDER_DEFAULT,
            command=self._apply_preset_default,
        ).grid(row=0, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            preset_btn_frame,
            text="Annex F 例1 (100,000h)",
            height=28,
            font=(FONT_FAMILY_UI, 11),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            hover_color=COLOR_BORDER_DEFAULT,
            command=self._apply_preset_annex_f1_std,
        ).grid(row=0, column=1, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            preset_btn_frame,
            text="Annex F 例1 (寿命50,000h)",
            height=28,
            font=(FONT_FAMILY_UI, 11),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            hover_color=COLOR_BORDER_DEFAULT,
            command=self._apply_preset_annex_f1_half,
        ).grid(row=1, column=0, padx=3, pady=3, sticky="ew")

        ctk.CTkButton(
            preset_btn_frame,
            text="高温主回路 (250A / 150℃)",
            height=28,
            font=(FONT_FAMILY_UI, 11),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            hover_color=COLOR_BORDER_DEFAULT,
            command=self._apply_preset_high_temp,
        ).grid(row=1, column=1, padx=3, pady=3, sticky="ew")

        # --- セクション1: 負荷電流・運転モード ---
        sec1 = self._create_section_card(row_idx, "1. 負荷電流・運転モード (Clause 4.2.3 a)")
        row_idx += 1

        # 用途区分 (電力配電用 / 制御用)
        app_row = ctk.CTkFrame(sec1, fg_color="transparent")
        app_row.grid(row=1, column=0, padx=12, pady=(4, 4), sticky="ew")
        app_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            app_row,
            text="電線用途:",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self._app_seg = ctk.CTkSegmentedButton(
            app_row,
            values=["電力配電用 (4.2.3)", "制御・信号用 (4.2.2)"],
            font=(FONT_FAMILY_UI, 11),
            command=self._on_app_type_changed,
        )
        self._app_seg.grid(row=0, column=1, sticky="ew")

        # 負荷電流 I (A)
        cur_header = ctk.CTkFrame(sec1, fg_color="transparent")
        cur_header.grid(row=2, column=0, padx=12, pady=(6, 2), sticky="ew")
        cur_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cur_header,
            text="負荷電流 I [A]:",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        cur_input_box = ctk.CTkFrame(cur_header, fg_color="transparent")
        cur_input_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            cur_input_box,
            text="-10",
            width=34,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_current(-10.0),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            cur_input_box,
            text="-1",
            width=30,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_current(-1.0),
        ).pack(side="left", padx=2)

        self._current_entry = ctk.CTkEntry(
            cur_input_box,
            width=76,
            height=28,
            justify="right",
            font=(FONT_FAMILY_UI, 13, "bold"),
        )
        self._current_entry.pack(side="left", padx=4)
        self._current_entry.bind("<Return>", self._on_current_entry_commit)
        self._current_entry.bind("<FocusOut>", self._on_current_entry_commit)
        self._current_entry.bind("<KeyRelease>", self._on_current_entry_key)

        ctk.CTkLabel(cur_input_box, text="A", font=(FONT_FAMILY_UI, 12)).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            cur_input_box,
            text="+1",
            width=30,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_current(1.0),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            cur_input_box,
            text="+10",
            width=34,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_current(10.0),
        ).pack(side="left", padx=2)

        self._current_slider = ctk.CTkSlider(
            sec1,
            from_=1.0,
            to=900.0,
            number_of_steps=899,
            command=self._on_current_slider_moved,
        )
        self._current_slider.grid(row=3, column=0, padx=12, pady=(2, 6), sticky="ew")

        # 運転モード切替
        ctk.CTkLabel(
            sec1,
            text="通電運転モード:",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=4, column=0, padx=12, pady=(4, 2), sticky="w")

        self._op_mode_seg = ctk.CTkSegmentedButton(
            sec1,
            values=["連続運転", "周期的負荷 (Cyclic)", "短時間運転 (Annex A)"],
            font=(FONT_FAMILY_UI, 11),
            command=self._on_op_mode_changed,
        )
        self._op_mode_seg.grid(row=5, column=0, padx=12, pady=(0, 8), sticky="ew")

        # 周期運転サブパネル
        self._cyclic_frame = ctk.CTkFrame(sec1, fg_color=COLOR_BG_SUBCARD, corner_radius=8)
        self._cyclic_frame.grid(row=6, column=0, padx=12, pady=(0, 8), sticky="ew")
        self._cyclic_frame.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            self._cyclic_frame,
            text="ON時間 ton(秒):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=0, padx=(8, 4), pady=6, sticky="w")
        self._cyclic_on_entry = ctk.CTkEntry(self._cyclic_frame, width=65, height=26, justify="right")
        self._cyclic_on_entry.grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        self._cyclic_on_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        ctk.CTkLabel(
            self._cyclic_frame,
            text="1周期 t1(秒):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=2, padx=(8, 4), pady=6, sticky="w")
        self._cyclic_total_entry = ctk.CTkEntry(self._cyclic_frame, width=65, height=26, justify="right")
        self._cyclic_total_entry.grid(row=0, column=3, padx=(4, 8), pady=6, sticky="ew")
        self._cyclic_total_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        # 短時間運転サブパネル
        self._short_time_frame = ctk.CTkFrame(sec1, fg_color=COLOR_BG_SUBCARD, corner_radius=8)
        self._short_time_frame.grid(row=7, column=0, padx=12, pady=(0, 8), sticky="ew")
        self._short_time_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._short_time_frame,
            text="ON時間 t2 (分):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=0, padx=8, pady=(6, 3), sticky="w")
        self._st_on_entry = ctk.CTkEntry(self._short_time_frame, width=80, height=26, justify="right")
        self._st_on_entry.grid(row=0, column=1, padx=8, pady=(6, 3), sticky="e")
        self._st_on_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        ctk.CTkLabel(
            self._short_time_frame,
            text="熱時定数 T の算出:",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=1, column=0, padx=8, pady=3, sticky="w")
        self._st_mode_seg = ctk.CTkSegmentedButton(
            self._short_time_frame,
            values=["経験式 (>50mm2)", "手動指定"],
            font=(FONT_FAMILY_UI, 11),
            command=self._on_st_mode_changed,
        )
        self._st_mode_seg.grid(row=1, column=1, padx=8, pady=3, sticky="e")

        self._st_tau_label = ctk.CTkLabel(
            self._short_time_frame,
            text="手動熱時定数 T (分):",
            font=(FONT_FAMILY_UI, 11),
        )
        self._st_tau_label.grid(row=2, column=0, padx=8, pady=(3, 6), sticky="w")
        self._st_tau_entry = ctk.CTkEntry(self._short_time_frame, width=80, height=26, justify="right")
        self._st_tau_entry.grid(row=2, column=1, padx=8, pady=(3, 6), sticky="e")
        self._st_tau_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        # --- セクション2: 電線被覆の耐熱クラスと多芯構造 ---
        sec2 = self._create_section_card(row_idx, "2. 電線被覆の耐熱クラス・芯線構成 (Annex C, Table 1)")
        row_idx += 1

        ctk.CTkLabel(
            sec2,
            text="最高許容導体温度 Tc(max) [℃]:",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=1, column=0, padx=12, pady=(6, 2), sticky="w")

        self._tc_seg = ctk.CTkSegmentedButton(
            sec2,
            values=["90 ℃", "105 ℃", "120 ℃", "140 ℃", "150 ℃"],
            font=(FONT_FAMILY_UI, 12, "bold"),
            command=self._on_tc_changed,
        )
        self._tc_seg.grid(row=2, column=0, padx=12, pady=(2, 4), sticky="ew")

        self._tc_std_label = ctk.CTkLabel(
            sec2,
            text="対応規格: EN 50264 / EN 50306 (k* = 1.00)",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_ACCENT,
        )
        self._tc_std_label.grid(row=3, column=0, padx=12, pady=(0, 6), sticky="w")

        # 単芯 / 多芯
        core_type_row = ctk.CTkFrame(sec2, fg_color="transparent")
        core_type_row.grid(row=4, column=0, padx=12, pady=(4, 6), sticky="ew")
        core_type_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            core_type_row,
            text="電線構造:",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=0, column=0, padx=(0, 8), sticky="w")

        self._core_type_seg = ctk.CTkSegmentedButton(
            core_type_row,
            values=["単芯ケーブル (k5=1.0)", "多芯ケーブル (Table 1)"],
            font=(FONT_FAMILY_UI, 11),
            command=self._on_core_type_changed,
        )
        self._core_type_seg.grid(row=0, column=1, sticky="ew")

        # 多芯時の同時負荷芯数フレーム
        self._multicore_frame = ctk.CTkFrame(sec2, fg_color=COLOR_BG_SUBCARD, corner_radius=8)
        self._multicore_frame.grid(row=5, column=0, padx=12, pady=(0, 8), sticky="ew")
        self._multicore_frame.grid_columnconfigure(0, weight=1)

        mc_top = ctk.CTkFrame(self._multicore_frame, fg_color="transparent")
        mc_top.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        mc_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            mc_top,
            text="多芯ケーブル内の同時負荷芯数:",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=0, sticky="w")

        self._cores_val_label = ctk.CTkLabel(
            mc_top,
            text="2 芯 (k5 = 0.91)",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_ACCENT,
        )
        self._cores_val_label.grid(row=0, column=1, sticky="e")

        self._cores_slider = ctk.CTkSlider(
            self._multicore_frame,
            from_=2,
            to=19,
            number_of_steps=17,
            command=self._on_cores_slider_moved,
        )
        self._cores_slider.grid(row=1, column=0, padx=8, pady=(2, 4), sticky="ew")

        # Table 1 規定芯数のクイックボタン
        mc_chips = ctk.CTkFrame(self._multicore_frame, fg_color="transparent")
        mc_chips.grid(row=2, column=0, padx=8, pady=(0, 6), sticky="ew")
        for idx, c_num in enumerate([2, 3, 4, 5, 7, 9, 12, 19]):
            mc_chips.grid_columnconfigure(idx, weight=1)
            ctk.CTkButton(
                mc_chips,
                text=f"{c_num}芯",
                height=22,
                width=36,
                font=(FONT_FAMILY_UI, 10),
                fg_color=COLOR_BG_CARD,
                text_color=COLOR_TEXT_PRIMARY,
                border_width=1,
                border_color=COLOR_BORDER_DEFAULT,
                command=lambda n=c_num: self._set_loaded_cores(n),
            ).grid(row=0, column=idx, padx=1, sticky="ew")

        # --- セクション3: 周囲温度 (1℃刻み) と敷設条件 (Table 2) ---
        sec3 = self._create_section_card(row_idx, "3. 周囲温度 (1℃刻み) と配線敷設条件 (Table 2)")
        row_idx += 1

        temp_header = ctk.CTkFrame(sec3, fg_color="transparent")
        temp_header.grid(row=1, column=0, padx=12, pady=(6, 2), sticky="ew")
        temp_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            temp_header,
            text="周囲温度 T [℃] (1℃刻み):",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        temp_ctrl_box = ctk.CTkFrame(temp_header, fg_color="transparent")
        temp_ctrl_box.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            temp_ctrl_box,
            text="-5℃",
            width=38,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_ambient_temp(-5),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            temp_ctrl_box,
            text="-1℃",
            width=38,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_ambient_temp(-1),
        ).pack(side="left", padx=2)

        self._temp_entry = ctk.CTkEntry(
            temp_ctrl_box,
            width=62,
            height=28,
            justify="right",
            font=(FONT_FAMILY_UI, 13, "bold"),
        )
        self._temp_entry.pack(side="left", padx=4)
        self._temp_entry.bind("<Return>", self._on_temp_entry_commit)
        self._temp_entry.bind("<FocusOut>", self._on_temp_entry_commit)
        self._temp_entry.bind("<KeyRelease>", self._on_temp_entry_key)

        ctk.CTkLabel(temp_ctrl_box, text="℃", font=(FONT_FAMILY_UI, 12)).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            temp_ctrl_box,
            text="+1℃",
            width=38,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_ambient_temp(1),
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            temp_ctrl_box,
            text="+5℃",
            width=38,
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=lambda: self._step_ambient_temp(5),
        ).pack(side="left", padx=2)

        # -25℃ 〜 +145℃ まで 1℃ 刻み (170ステップ)
        self._temp_slider = ctk.CTkSlider(
            sec3,
            from_=-25,
            to=145,
            number_of_steps=170,
            command=self._on_temp_slider_moved,
        )
        self._temp_slider.grid(row=2, column=0, padx=12, pady=(2, 4), sticky="ew")

        self._round_k1_check = ctk.CTkCheckBox(
            sec3,
            text="k1 を小数第2位に丸める (Table D.1 / Annex F 計算例互換)",
            font=(FONT_FAMILY_UI, 11),
            checkbox_width=18,
            checkbox_height=18,
            command=self._on_round_k1_toggled,
        )
        self._round_k1_check.grid(row=3, column=0, padx=12, pady=(0, 8), sticky="w")

        # 敷設方式 (Table 2 の全8列)
        ctk.CTkLabel(
            sec3,
            text="配線敷設方式 (Table 2 / Figure 2 の全8区分):",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=4, column=0, padx=12, pady=(4, 2), sticky="w")

        inst_labels: List[str] = list(self._inst_label_to_id.keys())
        self._inst_menu = ctk.CTkOptionMenu(
            sec3,
            values=inst_labels,
            font=(FONT_FAMILY_UI, 11),
            dropdown_font=(FONT_FAMILY_UI, 11),
            height=32,
            command=self._on_inst_type_changed,
        )
        self._inst_menu.grid(row=5, column=0, padx=12, pady=(2, 4), sticky="ew")

        # 選択された敷設方式の説明ボックス
        self._inst_desc_box = ctk.CTkFrame(sec3, fg_color=COLOR_BG_SUBCARD, corner_radius=8)
        self._inst_desc_box.grid(row=6, column=0, padx=12, pady=(2, 6), sticky="ew")
        self._inst_desc_box.grid_columnconfigure(0, weight=1)

        self._inst_desc_label = ctk.CTkLabel(
            self._inst_desc_box,
            text="",
            font=(FONT_FAMILY_UI, 11),
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            anchor="w",
            wraplength=370,
        )
        self._inst_desc_label.grid(row=0, column=0, padx=8, pady=6, sticky="ew")

        # 同時負荷電線本数（束ね本数）
        bundle_header = ctk.CTkFrame(sec3, fg_color="transparent")
        bundle_header.grid(row=7, column=0, padx=12, pady=(4, 2), sticky="ew")
        bundle_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            bundle_header,
            text="同時負荷電線本数 (束ね本数):",
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self._bundle_count_label = ctk.CTkLabel(
            bundle_header,
            text="4 本",
            font=(FONT_FAMILY_UI, 13, "bold"),
            text_color=COLOR_ACCENT,
        )
        self._bundle_count_label.grid(row=0, column=1, sticky="e")

        self._bundle_slider = ctk.CTkSlider(
            sec3,
            from_=1,
            to=20,
            number_of_steps=19,
            command=self._on_bundle_slider_moved,
        )
        self._bundle_slider.grid(row=8, column=0, padx=12, pady=(2, 4), sticky="ew")

        # Table 2 の規定行 (1, 2, 3, 4, 8, 12, 16, 20+) クイック選択ボタン
        bundle_chips = ctk.CTkFrame(sec3, fg_color="transparent")
        bundle_chips.grid(row=9, column=0, padx=12, pady=(0, 8), sticky="ew")
        self._bundle_chip_buttons: Dict[int, ctk.CTkButton] = {}
        for idx, b_cnt in enumerate([1, 2, 3, 4, 8, 12, 16, 20]):
            bundle_chips.grid_columnconfigure(idx, weight=1)
            btn_txt = "20+" if b_cnt == 20 else f"{b_cnt}本"
            btn = ctk.CTkButton(
                bundle_chips,
                text=btn_txt,
                height=24,
                width=38,
                font=(FONT_FAMILY_UI, 10),
                fg_color=COLOR_BG_SUBCARD,
                text_color=COLOR_TEXT_PRIMARY,
                border_width=1,
                border_color=COLOR_BORDER_DEFAULT,
                command=lambda n=b_cnt: self._set_bundled_cables(n),
            )
            btn.grid(row=0, column=idx, padx=1, sticky="ew")
            self._bundle_chip_buttons[b_cnt] = btn

        # --- セクション4: 予測寿命・短絡・保護装置オプション ---
        sec4 = self._create_section_card(row_idx, "4. 予測寿命 (Annex E) と短絡・付帯検証 (Annex F, Table 3)")
        row_idx += 1

        ctk.CTkLabel(
            sec4,
            text="予測ケーブル寿命と許容温度偏差 ΔT (k3):",
            font=(FONT_FAMILY_UI, 12),
            text_color=COLOR_TEXT_SECONDARY,
        ).grid(row=1, column=0, padx=12, pady=(6, 2), sticky="w")

        self._life_menu = ctk.CTkOptionMenu(
            sec4,
            values=list(self._life_label_to_dt.keys()),
            font=(FONT_FAMILY_UI, 11),
            dropdown_font=(FONT_FAMILY_UI, 11),
            height=30,
            command=self._on_lifetime_changed,
        )
        self._life_menu.grid(row=2, column=0, padx=12, pady=(0, 6), sticky="ew")

        # 短絡電流・保護装置・外径入力グリッド
        extra_grid = ctk.CTkFrame(sec4, fg_color=COLOR_BG_SUBCARD, corner_radius=8)
        extra_grid.grid(row=3, column=0, padx=12, pady=(2, 8), sticky="ew")
        extra_grid.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            extra_grid,
            text="短絡電流 (kA):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=0, padx=(8, 4), pady=(6, 3), sticky="w")
        self._sc_ka_entry = ctk.CTkEntry(extra_grid, width=60, height=26, justify="right")
        self._sc_ka_entry.grid(row=0, column=1, padx=4, pady=(6, 3), sticky="ew")
        self._sc_ka_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        ctk.CTkLabel(
            extra_grid,
            text="短絡時間 (秒):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=0, column=2, padx=(8, 4), pady=(6, 3), sticky="w")
        self._sc_sec_entry = ctk.CTkEntry(extra_grid, width=60, height=26, justify="right")
        self._sc_sec_entry.grid(row=0, column=3, padx=(4, 8), pady=(6, 3), sticky="ew")
        self._sc_sec_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        ctk.CTkLabel(
            extra_grid,
            text="保護素子(Table3):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=1, column=0, padx=(8, 4), pady=3, sticky="w")
        self._prot_menu = ctk.CTkOptionMenu(
            extra_grid,
            values=["指定なし", "6 A", "10 A", "16 A", "20 A", "25 A"],
            height=26,
            font=(FONT_FAMILY_UI, 11),
            command=self._on_prot_changed,
        )
        self._prot_menu.grid(row=1, column=1, padx=4, pady=3, sticky="ew")

        ctk.CTkLabel(
            extra_grid,
            text="外径 D (mm):",
            font=(FONT_FAMILY_UI, 11),
        ).grid(row=1, column=2, padx=(8, 4), pady=3, sticky="w")
        self._od_entry = ctk.CTkEntry(extra_grid, width=60, height=26, justify="right")
        self._od_entry.grid(row=1, column=3, padx=(4, 8), pady=3, sticky="ew")
        self._od_entry.bind("<KeyRelease>", self._on_subparam_entry_changed)

        self._screened_check = ctk.CTkCheckBox(
            extra_grid,
            text="シールド付きケーブル (曲げ半径 R = 10 x D を適用)",
            font=(FONT_FAMILY_UI, 11),
            checkbox_width=18,
            checkbox_height=18,
            command=self._on_screened_toggled,
        )
        self._screened_check.grid(row=2, column=0, columnspan=4, padx=8, pady=(3, 6), sticky="w")

        # --- セクション5: アクションボタン（エクスポート） ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.grid(row=row_idx, column=0, padx=8, pady=(4, 10), sticky="ew")
        action_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            action_frame,
            text="CSV形式で結果保存",
            height=34,
            font=(FONT_FAMILY_UI, 12, "bold"),
            fg_color=COLOR_ACCENT,
            command=self._on_export_csv,
        ).grid(row=0, column=0, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(
            action_frame,
            text="計算報告書 (TXT) 保存",
            height=34,
            font=(FONT_FAMILY_UI, 12, "bold"),
            fg_color=COLOR_BG_SUBCARD,
            text_color=COLOR_TEXT_PRIMARY,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
            hover_color=COLOR_BORDER_DEFAULT,
            command=self._on_export_txt,
        ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")

    def _create_section_card(self, row: int, title: str) -> ctk.CTkFrame:
        """セクション枠カードを生成する."""
        card = ctk.CTkFrame(
            self,
            fg_color=COLOR_BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER_DEFAULT,
        )
        card.grid(row=row, column=0, padx=6, pady=5, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=(FONT_FAMILY_UI, 12, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        title_lbl.grid(row=0, column=0, padx=12, pady=(8, 2), sticky="ew")
        return card

    def _sync_ui_from_state(self) -> None:
        """内部の CableSizingInput 状態を全UIウィジェットへ反映する."""
        self._updating_ui = True
        try:
            s = self._state

            # 用途
            self._app_seg.set("電力配電用 (4.2.3)" if s.cable_application == "power" else "制御・信号用 (4.2.2)")

            # 負荷電流
            self._current_entry.delete(0, "end")
            self._current_entry.insert(0, f"{s.load_current_a:.1f}".rstrip("0").rstrip("."))
            self._current_slider.set(min(900.0, max(1.0, s.load_current_a)))

            # 運転モード
            if s.operation_mode == "cyclic":
                self._op_mode_seg.set("周期的負荷 (Cyclic)")
                self._cyclic_frame.grid()
                self._short_time_frame.grid_remove()
            elif s.operation_mode == "short_time":
                self._op_mode_seg.set("短時間運転 (Annex A)")
                self._cyclic_frame.grid_remove()
                self._short_time_frame.grid()
            else:
                self._op_mode_seg.set("連続運転")
                self._cyclic_frame.grid_remove()
                self._short_time_frame.grid_remove()

            self._cyclic_on_entry.delete(0, "end")
            self._cyclic_on_entry.insert(0, f"{s.cyclic_on_sec:.0f}")
            self._cyclic_total_entry.delete(0, "end")
            self._cyclic_total_entry.insert(0, f"{s.cyclic_total_sec:.0f}")

            self._st_on_entry.delete(0, "end")
            self._st_on_entry.insert(0, f"{s.short_time_on_min:.1f}")
            self._st_mode_seg.set(
                "経験式 (>50mm2)" if s.short_time_constant_mode == "empirical" else "手動指定"
            )
            self._st_tau_entry.delete(0, "end")
            self._st_tau_entry.insert(0, f"{s.short_time_manual_tau_min:.1f}")
            if s.short_time_constant_mode == "empirical":
                self._st_tau_label.grid_remove()
                self._st_tau_entry.grid_remove()
            else:
                self._st_tau_label.grid()
                self._st_tau_entry.grid()

            # 耐熱クラス
            self._tc_seg.set(f"{s.tc_max_c} ℃")
            t_info = TEMPERATURE_CLASSES.get(s.tc_max_c, TEMPERATURE_CLASSES[90])
            self._tc_std_label.configure(
                text=f"対応規格: {t_info['standard_family']} (k* = {float(t_info['k_star_table']):.2f})"
            )

            # 単芯 / 多芯
            if s.is_multicore:
                self._core_type_seg.set("多芯ケーブル (Table 1)")
                self._multicore_frame.grid()
                self._cores_slider.set(min(19, max(2, s.num_loaded_cores)))
                self._cores_val_label.configure(text=f"{s.num_loaded_cores} 芯同時負荷")
            else:
                self._core_type_seg.set("単芯ケーブル (k5=1.0)")
                self._multicore_frame.grid_remove()

            # 周囲温度 (1℃刻み)
            self._temp_entry.delete(0, "end")
            self._temp_entry.insert(0, f"{int(s.ambient_temp_c)}")
            self._temp_slider.set(min(145, max(-25, int(s.ambient_temp_c))))
            if s.use_table_d1_rounded_k1:
                self._round_k1_check.select()
            else:
                self._round_k1_check.deselect()

            # 敷設方式
            inst_lbl = self._inst_id_to_label.get(s.installation_type_id, "")
            if inst_lbl:
                self._inst_menu.set(inst_lbl)
            self._update_installation_description()

            # 同時負荷電線本数
            self._bundle_slider.set(min(20, max(1, s.num_bundled_cables)))
            cnt_txt = "20 本以上 (20+)" if s.num_bundled_cables >= 20 else f"{s.num_bundled_cables} 本"
            self._bundle_count_label.configure(text=cnt_txt)
            self._update_bundle_chip_states()

            # 寿命
            life_lbl = self._life_dt_to_label.get(s.lifetime_delta_t_k, "")
            if life_lbl:
                self._life_menu.set(life_lbl)

            # 短絡・保護装置・外径
            self._sc_ka_entry.delete(0, "end")
            self._sc_ka_entry.insert(0, f"{s.short_circuit_current_ka:.1f}".rstrip("0").rstrip("."))
            self._sc_sec_entry.delete(0, "end")
            self._sc_sec_entry.insert(0, f"{s.short_circuit_duration_s:.2f}".rstrip("0").rstrip("."))
            self._prot_menu.set(
                "指定なし" if s.protection_device_rating_a == 0 else f"{s.protection_device_rating_a} A"
            )
            self._od_entry.delete(0, "end")
            self._od_entry.insert(0, f"{s.outer_diameter_mm:.1f}".rstrip("0").rstrip("."))
            if s.is_screened:
                self._screened_check.select()
            else:
                self._screened_check.deselect()
        finally:
            self._updating_ui = False

    def _update_installation_description(self) -> None:
        """選択中の敷設方式の解説文と、本数制限に関する注意ガイドを更新する."""
        inst_info = INSTALLATION_TYPES.get(self._state.installation_type_id, {})
        desc = str(inst_info.get("description", ""))
        self._inst_desc_label.configure(text=desc)

    def _update_bundle_chip_states(self) -> None:
        """敷設方式に応じた各本数チップの有効/対象外表示を更新する."""
        inst_info = INSTALLATION_TYPES.get(self._state.installation_type_id, {})
        invalid_counts = set(inst_info.get("invalid_counts", []))  # type: ignore[arg-type]
        for cnt, btn in self._bundle_chip_buttons.items():
            if cnt in invalid_counts or (self._state.installation_type_id == "type_a" and cnt >= 2):
                btn.configure(
                    fg_color=COLOR_BG_SUBCARD,
                    text_color=COLOR_TEXT_MUTED,
                    border_color=COLOR_BORDER_DEFAULT,
                )
            elif cnt == self._state.num_bundled_cables or (cnt == 20 and self._state.num_bundled_cables >= 20):
                btn.configure(
                    fg_color=COLOR_ACCENT,
                    text_color="#FFFFFF",
                    border_color=COLOR_ACCENT,
                )
            else:
                btn.configure(
                    fg_color=COLOR_BG_SUBCARD,
                    text_color=COLOR_TEXT_PRIMARY,
                    border_color=COLOR_BORDER_DEFAULT,
                )

    def _emit_change(self) -> None:
        if not self._updating_ui:
            self._on_change(self._state)

    # --- イベントハンドラ群 ---
    def _on_app_type_changed(self, value: str) -> None:
        self._state.cable_application = "power" if "4.2.3" in value else "control"
        self._emit_change()

    def _step_current(self, delta: float) -> None:
        new_val = max(0.5, min(2000.0, round(self._state.load_current_a + delta, 1)))
        self._state.load_current_a = new_val
        self._sync_ui_from_state()
        self._emit_change()

    def _on_current_slider_moved(self, value: float) -> None:
        if self._updating_ui:
            return
        self._state.load_current_a = float(round(value))
        self._updating_ui = True
        self._current_entry.delete(0, "end")
        self._current_entry.insert(0, f"{int(round(value))}")
        self._updating_ui = False
        self._emit_change()

    def _on_current_entry_key(self, _event: object = None) -> None:
        if self._updating_ui:
            return
        txt = self._current_entry.get().strip()
        try:
            val = float(txt)
            if 0.0 <= val <= 5000.0:
                self._state.load_current_a = val
                self._updating_ui = True
                self._current_slider.set(min(900.0, max(1.0, val)))
                self._updating_ui = False
                self._emit_change()
        except ValueError:
            pass

    def _on_current_entry_commit(self, _event: object = None) -> None:
        self._on_current_entry_key()

    def _on_op_mode_changed(self, value: str) -> None:
        if "周期" in value:
            self._state.operation_mode = "cyclic"
        elif "短時間" in value:
            self._state.operation_mode = "short_time"
        else:
            self._state.operation_mode = "continuous"
        self._sync_ui_from_state()
        self._emit_change()

    def _on_st_mode_changed(self, value: str) -> None:
        self._state.short_time_constant_mode = "empirical" if "経験式" in value else "manual"
        self._sync_ui_from_state()
        self._emit_change()

    def _on_subparam_entry_changed(self, _event: object = None) -> None:
        if self._updating_ui:
            return
        try:
            self._state.cyclic_on_sec = max(1.0, float(self._cyclic_on_entry.get().strip() or "480"))
        except ValueError:
            pass
        try:
            self._state.cyclic_total_sec = max(1.0, float(self._cyclic_total_entry.get().strip() or "520"))
        except ValueError:
            pass
        try:
            self._state.short_time_on_min = max(0.1, float(self._st_on_entry.get().strip() or "3.0"))
        except ValueError:
            pass
        try:
            self._state.short_time_manual_tau_min = max(0.1, float(self._st_tau_entry.get().strip() or "2.0"))
        except ValueError:
            pass
        try:
            self._state.short_circuit_current_ka = max(0.0, float(self._sc_ka_entry.get().strip() or "0"))
        except ValueError:
            pass
        try:
            self._state.short_circuit_duration_s = max(0.01, float(self._sc_sec_entry.get().strip() or "1.0"))
        except ValueError:
            pass
        try:
            self._state.outer_diameter_mm = max(1.0, float(self._od_entry.get().strip() or "10.0"))
        except ValueError:
            pass
        self._emit_change()

    def _on_tc_changed(self, value: str) -> None:
        tc_int = int(value.replace("℃", "").strip())
        self._state.tc_max_c = tc_int
        self._sync_ui_from_state()
        self._emit_change()

    def _on_core_type_changed(self, value: str) -> None:
        is_mc = "多芯" in value
        self._state.is_multicore = is_mc
        if is_mc and self._state.num_loaded_cores < 2:
            self._state.num_loaded_cores = 2
        elif not is_mc:
            self._state.num_loaded_cores = 1
        self._sync_ui_from_state()
        self._emit_change()

    def _on_cores_slider_moved(self, value: float) -> None:
        if self._updating_ui:
            return
        c_int = int(round(value))
        self._state.num_loaded_cores = c_int
        self._cores_val_label.configure(text=f"{c_int} 芯同時負荷")
        self._emit_change()

    def _set_loaded_cores(self, n_cores: int) -> None:
        self._state.is_multicore = True
        self._state.num_loaded_cores = n_cores
        self._sync_ui_from_state()
        self._emit_change()

    def _step_ambient_temp(self, delta_deg: int) -> None:
        """1℃刻み（または5℃刻み）で周囲温度 T を増減する."""
        new_t = max(-40, min(149, int(self._state.ambient_temp_c) + delta_deg))
        self._state.ambient_temp_c = new_t
        self._sync_ui_from_state()
        self._emit_change()

    def _on_temp_slider_moved(self, value: float) -> None:
        """スライダー操作時に 1℃ 刻みの整数温度として反映する."""
        if self._updating_ui:
            return
        t_int = int(round(value))
        self._state.ambient_temp_c = t_int
        self._updating_ui = True
        self._temp_entry.delete(0, "end")
        self._temp_entry.insert(0, f"{t_int}")
        self._updating_ui = False
        self._emit_change()

    def _on_temp_entry_key(self, _event: object = None) -> None:
        if self._updating_ui:
            return
        txt = self._temp_entry.get().strip()
        if txt in ("", "-"):
            return
        try:
            t_int = int(round(float(txt)))
            if -50 <= t_int <= 200:
                self._state.ambient_temp_c = t_int
                self._updating_ui = True
                self._temp_slider.set(min(145, max(-25, t_int)))
                self._updating_ui = False
                self._emit_change()
        except ValueError:
            pass

    def _on_temp_entry_commit(self, _event: object = None) -> None:
        if self._updating_ui:
            return
        txt = self._temp_entry.get().strip()
        try:
            t_int = int(round(float(txt)))
        except ValueError:
            t_int = 45
        self._state.ambient_temp_c = max(-50, min(200, t_int))
        self._sync_ui_from_state()
        self._emit_change()

    def _on_round_k1_toggled(self) -> None:
        self._state.use_table_d1_rounded_k1 = bool(self._round_k1_check.get())
        self._emit_change()

    def _on_inst_type_changed(self, label: str) -> None:
        inst_id = self._inst_label_to_id.get(label, "type_b")
        self._state.installation_type_id = inst_id
        self._update_installation_description()
        self._update_bundle_chip_states()
        self._emit_change()

    def _on_bundle_slider_moved(self, value: float) -> None:
        if self._updating_ui:
            return
        n_int = int(round(value))
        self._state.num_bundled_cables = n_int
        cnt_txt = "20 本以上 (20+)" if n_int >= 20 else f"{n_int} 本"
        self._bundle_count_label.configure(text=cnt_txt)
        self._update_bundle_chip_states()
        self._emit_change()

    def _set_bundled_cables(self, count: int) -> None:
        self._state.num_bundled_cables = count
        self._sync_ui_from_state()
        self._emit_change()

    def _on_lifetime_changed(self, label: str) -> None:
        self._state.lifetime_delta_t_k = self._life_label_to_dt.get(label, 0)
        self._emit_change()

    def _on_prot_changed(self, value: str) -> None:
        if value == "指定なし":
            self._state.protection_device_rating_a = 0
        else:
            self._state.protection_device_rating_a = int(value.replace("A", "").strip())
        self._emit_change()

    def _on_screened_toggled(self) -> None:
        self._state.is_screened = bool(self._screened_check.get())
        self._emit_change()

    # --- プリセット適用メソッド ---
    def set_input_state(self, new_state: CableSizingInput) -> None:
        """外部またはプリセットから入力状態を一括更新する."""
        self._state = new_state
        self._sync_ui_from_state()
        self._emit_change()

    def _apply_preset_default(self) -> None:
        self.set_input_state(
            CableSizingInput(
                load_current_a=100.0,
                operation_mode="continuous",
                tc_max_c=90,
                ambient_temp_c=45,
                use_table_d1_rounded_k1=False,
                installation_type_id="type_b",
                num_bundled_cables=4,
                is_multicore=False,
                num_loaded_cores=1,
                lifetime_delta_t_k=0,
            )
        )

    def _apply_preset_annex_f1_std(self) -> None:
        """規格書 Annex F.1 Example 1 (100,000時間寿命 -> 400 mm2)."""
        self.set_input_state(
            CableSizingInput(
                load_current_a=475.0,
                operation_mode="cyclic",
                cyclic_on_sec=480.0,
                cyclic_total_sec=520.0,
                tc_max_c=90,
                ambient_temp_c=55,
                use_table_d1_rounded_k1=True,
                installation_type_id="type_f",
                num_bundled_cables=4,
                is_multicore=False,
                num_loaded_cores=1,
                lifetime_delta_t_k=0,
            )
        )

    def _apply_preset_annex_f1_half(self) -> None:
        """規格書 Annex F.1 Example 1 後半 (50,000時間寿命 k3=1.10 -> 300 mm2)."""
        self.set_input_state(
            CableSizingInput(
                load_current_a=475.0,
                operation_mode="cyclic",
                cyclic_on_sec=480.0,
                cyclic_total_sec=520.0,
                tc_max_c=90,
                ambient_temp_c=55,
                use_table_d1_rounded_k1=True,
                installation_type_id="type_f",
                num_bundled_cables=4,
                is_multicore=False,
                num_loaded_cores=1,
                lifetime_delta_t_k=10,
            )
        )

    def _apply_preset_high_temp(self) -> None:
        """高温・主回路ケーブル例 (EN 50382 150℃, 周囲75℃, トレイ2層 4本)."""
        self.set_input_state(
            CableSizingInput(
                load_current_a=250.0,
                operation_mode="continuous",
                tc_max_c=150,
                ambient_temp_c=75,
                use_table_d1_rounded_k1=False,
                installation_type_id="trays_two_layers",
                num_bundled_cables=4,
                is_multicore=False,
                num_loaded_cores=1,
                lifetime_delta_t_k=0,
                short_circuit_current_ka=10.0,
                short_circuit_duration_s=0.5,
            )
        )
