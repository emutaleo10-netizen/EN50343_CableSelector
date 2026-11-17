"""アプリケーションのメインウィンドウ制御クラス (CustomTkinter)."""

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from src.backend.calculator import EN50343Calculator
from src.backend.models import CableSizingInput, CableSizingResult
from src.frontend.input_panel import InputPanel
from src.frontend.output_panel import OutputPanel
from src.frontend.theme import (
    COLOR_BG_HEADER,
    COLOR_BG_MAIN,
    FONT_FAMILY_UI,
)
from src.utils.exporter import export_csv_report, generate_text_report


class EN50343AppWindow(ctk.CTk):
    """BS EN 50343:2024 鉄道車両向け電線選定システムのメインウィンドウ."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("BS EN 50343:2024 鉄道車両向け電線選定・許容電流計算システム")
        self.geometry("1460x900")
        self.minsize(1200, 760)
        self.configure(fg_color=COLOR_BG_MAIN)

        self._latest_result: Optional[CableSizingResult] = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

        # 初回計算の実行
        initial_input = CableSizingInput()
        self._on_input_changed(initial_input)

    def _build_header(self) -> None:
        """上部のアプリケーションヘッダーバーを構築する."""
        header = ctk.CTkFrame(self, fg_color=COLOR_BG_HEADER, corner_radius=0, height=54)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=0, padx=18, pady=8, sticky="w")

        ctk.CTkLabel(
            title_box,
            text="BS EN 50343:2024  Railway Rolling Stock Cable Sizing System",
            font=(FONT_FAMILY_UI, 17, "bold"),
            text_color="#FFFFFF",
        ).pack(side="left", padx=(0, 14))

        ctk.CTkLabel(
            title_box,
            text="鉄道車両向け電線選択・ディレーティング計算自動化ツール",
            font=(FONT_FAMILY_UI, 12),
            text_color="#93C5FD",
        ).pack(side="left")

        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.grid(row=0, column=1, padx=18, pady=8, sticky="e")

        ctk.CTkLabel(
            right_box,
            text="表示テーマ:",
            font=(FONT_FAMILY_UI, 11),
            text_color="#E2E8F0",
        ).pack(side="left", padx=(0, 6))

        self._theme_seg = ctk.CTkSegmentedButton(
            right_box,
            values=["Dark", "Light"],
            font=(FONT_FAMILY_UI, 11),
            height=28,
            command=self._on_theme_changed,
        )
        self._theme_seg.set("Dark")
        self._theme_seg.pack(side="left")

    def _build_body(self) -> None:
        """左右2ペインのメインレイアウトを構築する."""
        self._input_panel = InputPanel(
            self,
            on_change_callback=self._on_input_changed,
            on_export_csv_callback=self._export_csv,
            on_export_txt_callback=self._export_txt,
            width=445,
        )
        self._input_panel.grid(row=1, column=0, padx=(12, 6), pady=12, sticky="nsew")

        self._output_panel = OutputPanel(self)
        self._output_panel.grid(row=1, column=1, padx=(6, 12), pady=12, sticky="nsew")

    def _on_theme_changed(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)

    def _on_input_changed(self, params: CableSizingInput) -> None:
        """入力パネルの値が変更された際にリアルタイム計算を行い出力パネルを更新する."""
        result = EN50343Calculator.evaluate(params)
        self._latest_result = result
        self._output_panel.update_result(result)

    def _export_csv(self) -> None:
        if self._latest_result is None:
            return
        file_path = filedialog.asksaveasfilename(
            title="計算結果 (CSV) の保存先を選択",
            defaultextension=".csv",
            initialfile="EN50343_CableSizing_Result.csv",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")],
        )
        if not file_path:
            return
        try:
            export_csv_report(Path(file_path), self._latest_result)
            messagebox.showinfo("CSV出力完了", f"CSVファイルを保存しました:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{exc}")

    def _export_txt(self) -> None:
        if self._latest_result is None:
            return
        file_path = filedialog.asksaveasfilename(
            title="計算報告書 (TXT) の保存先を選択",
            defaultextension=".txt",
            initialfile="EN50343_CableSizing_Report.txt",
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")],
        )
        if not file_path:
            return
        try:
            report_str = generate_text_report(self._latest_result)
            Path(file_path).write_text(report_str, encoding="utf-8")
            messagebox.showinfo("報告書出力完了", f"計算報告書を保存しました:\n{file_path}")
        except OSError as exc:
            messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{exc}")
