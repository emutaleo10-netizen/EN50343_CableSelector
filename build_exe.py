"""PyInstaller を用いて単一の配布用 exe ファイルをビルドする自動化スクリプト.

使用方法:
    python build_exe.py
"""

import os
import subprocess
import sys
from pathlib import Path


def build_single_exe() -> int:
    """CustomTkinter のアセットを含めて単一 exe (--onefile --windowed) をビルドする."""
    project_root = Path(__file__).resolve().parent
    main_script = project_root / "main.py"

    try:
        import customtkinter
        ctk_path = Path(customtkinter.__file__).resolve().parent
    except ImportError:
        print("エラー: customtkinter がインストールされていません。pip install -r requirements.txt を実行してください。")
        return 1

    sep = ";" if os.name == "nt" else ":"
    add_data_ctk = f"{ctk_path}{sep}customtkinter/"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "EN50343_CableSelector",
        "--add-data",
        add_data_ctk,
        "--paths",
        str(project_root),
        str(main_script),
    ]

    print("PyInstaller ビルドを開始します...")
    print("実行コマンド:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(project_root), check=False)
    if completed.returncode == 0:
        dist_exe = project_root / "dist" / ("EN50343_CableSelector.exe" if os.name == "nt" else "EN50343_CableSelector")
        print(f"ビルドが正常に完了しました: {dist_exe}")
    else:
        print(f"ビルドが終了コード {completed.returncode} で失敗しました。")
    return completed.returncode


if __name__ == "__main__":
    sys.exit(build_single_exe())
