"""PyInstaller 単一exeビルド時のリソースパス解決ユーティリティ."""

import os
import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """実行環境（通常Python実行 または PyInstaller --onefile 実行）に応じた絶対パスを返す."""
    if hasattr(sys, "_MEIPASS"):
        base_path = Path(getattr(sys, "_MEIPASS"))
    else:
        base_path = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    return base_path / relative_path
