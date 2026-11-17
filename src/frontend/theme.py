"""CustomTkinter UI向けのカラーパレットおよびフォントスタイル定義."""

from typing import Tuple

# CustomTkinter の (Lightモード色, Darkモード色) タプル定義
COLOR_BG_MAIN: Tuple[str, str] = ("#F1F5F9", "#0F172A")
COLOR_BG_CARD: Tuple[str, str] = ("#FFFFFF", "#1E293B")
COLOR_BG_SUBCARD: Tuple[str, str] = ("#F8FAFC", "#0F172A")
COLOR_BG_HEADER: Tuple[str, str] = ("#1E3A8A", "#0B1120")

COLOR_BORDER_DEFAULT: Tuple[str, str] = ("#CBD5E1", "#334155")
COLOR_BORDER_ACCENT: Tuple[str, str] = ("#2563EB", "#3B82F6")
COLOR_BORDER_RECOMMENDED: Tuple[str, str] = ("#059669", "#10B981")

COLOR_TEXT_PRIMARY: Tuple[str, str] = ("#0F172A", "#F8FAFC")
COLOR_TEXT_SECONDARY: Tuple[str, str] = ("#475569", "#94A3B8")
COLOR_TEXT_MUTED: Tuple[str, str] = ("#64748B", "#64748B")

# ステータスカラー
COLOR_SUCCESS: Tuple[str, str] = ("#059669", "#10B981")
COLOR_SUCCESS_BG: Tuple[str, str] = ("#D1FAE5", "#064E3B")

COLOR_WARNING: Tuple[str, str] = ("#D97706", "#F59E0B")
COLOR_WARNING_BG: Tuple[str, str] = ("#FEF3C7", "#451A03")

COLOR_DANGER: Tuple[str, str] = ("#DC2626", "#EF4444")
COLOR_DANGER_BG: Tuple[str, str] = ("#FEE2E2", "#450A0A")

COLOR_ACCENT: Tuple[str, str] = ("#2563EB", "#3B82F6")
COLOR_ACCENT_HOVER: Tuple[str, str] = ("#1D4ED8", "#2563EB")
COLOR_ACCENT_BG: Tuple[str, str] = ("#DBEAFE", "#1E3A8A")

# テーブル行の背景色
COLOR_ROW_RECOMMENDED: Tuple[str, str] = ("#DCFCE7", "#064E3B")
COLOR_ROW_OK_EVEN: Tuple[str, str] = ("#FFFFFF", "#1E293B")
COLOR_ROW_OK_ODD: Tuple[str, str] = ("#F8FAFC", "#172033")
COLOR_ROW_NG: Tuple[str, str] = ("#FFF1F2", "#2A1215")

# Windows で日本語が美しく表示されるフォントファミリー
FONT_FAMILY_UI: str = "Meiryo UI"
FONT_FAMILY_MONO: str = "Consolas"
