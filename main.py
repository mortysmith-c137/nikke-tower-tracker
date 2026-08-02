from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication

from ui import MainWindow


def application_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_directory() -> Path:
    return Path(getattr(sys, "_MEIPASS", application_directory()))


def dark_palette() -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#090b10"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6e9f0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#11151d"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#151922"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6e9f0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1b212d"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6e9f0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#a98b49"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#090b10"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#8790a0"))
    return palette


def main() -> int:
    base_directory = application_directory()
    assets_directory = resource_directory() / "assets" / "icons"
    app = QApplication(sys.argv)
    app.setApplicationName("NIKKE Tower Tracker")
    app.setStyle("Fusion")
    app.setPalette(dark_palette())

    icon_path = assets_directory / "nikke.jpeg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow(base_directory / "data.json", base_directory / "reports", assets_directory)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
