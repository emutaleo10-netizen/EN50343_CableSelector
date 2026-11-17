"""BS EN 50343:2024 鉄道車両向け電線選定アプリケーション エントリポイント."""

import ctypes
import sys

from src.frontend.app_window import EN50343AppWindow


def enable_windows_high_dpi() -> None:
    """Windows環境における高DPIスケーリングの滲みを防止する."""
    if sys.platform == "win32":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def main() -> None:
    """アプリケーションを起動する."""
    enable_windows_high_dpi()
    app = EN50343AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
