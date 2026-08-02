from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QProgressBar, QPushButton, QRadioButton, QSpinBox, QTextEdit,
    QScrollArea, QSplitter, QVBoxLayout, QWidget,
)

from calculator import DAY_LABELS, TowerCalculation, TowerInput, Weekday, calculate_tower

TOWER_NAMES = ("Elysion", "Missilis", "Tetra", "Pilgrim")
ICON_FILENAMES = {name: f"{name}_logo.webp" for name in TOWER_NAMES}
MAXIMUM_INPUT_VALUE = 999_999


@dataclass(frozen=True, slots=True)
class SavedTowerState:
    last_reached_floor: int = 0
    current_molds: int = 0
    requested_openings: int = 1


class JsonStorage:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> tuple[int, dict[str, SavedTowerState]]:
        defaults = {name: SavedTowerState() for name in TOWER_NAMES}
        if not self.path.exists():
            self.save(0, defaults)
            return 0, defaults
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            towers = data.get("towers", {})
            saved = {name: self._state_from_data(towers.get(name, {})) for name in TOWER_NAMES}
            return min(6, max(0, int(data.get("day", 0)))), saved
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return 0, defaults

    @staticmethod
    def _state_from_data(state: dict[str, Any]) -> SavedTowerState:
        if "last_reached_floor" in state:
            floor = int(state["last_reached_floor"])
        else:
            floor = int(state.get("blocked_floor", 1)) - 1
        return SavedTowerState(
            max(0, floor),
            max(0, int(state.get("current_molds", 0))),
            max(0, int(state.get("requested_openings", 1))),
        )

    def save(self, day: int, towers: dict[str, SavedTowerState]) -> None:
        payload = {"day": day, "towers": {name: asdict(state) for name, state in towers.items()}}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class TowerWidget(QGroupBox):
    values_changed = Signal()

    def __init__(self, name: str, icon_path: Path) -> None:
        super().__init__(name)
        self.name = name
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.last_reached_floor = self._spin(0, 0)
        self.current_molds = self._spin(0, 0)
        self.requested_openings = self._spin(0, 1)
        self.progress = QProgressBar()
        icon = QLabel()
        icon.setFixedSize(150, 60)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap(str(icon_path))
        if not pixmap.isNull():
            icon.setPixmap(pixmap.scaled(120, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        layout.addRow(self._label("Tower"), icon)
        layout.addRow(self._label("Last Reached Floor"), self.last_reached_floor)
        layout.addRow(self._label("Current Molds"), self.current_molds)
        layout.addRow(self._label("Requested Opens"), self.requested_openings)
        layout.addRow(self._label("Progress"), self.progress)
        for control in (self.last_reached_floor, self.current_molds, self.requested_openings):
            control.valueChanged.connect(self._refresh_progress)
            control.valueChanged.connect(self.values_changed)
        self._refresh_progress()

    @staticmethod
    def _spin(minimum: int, value: int) -> QSpinBox:
        control = QSpinBox()
        control.setRange(minimum, MAXIMUM_INPUT_VALUE)
        control.setValue(value)
        control.setAccelerated(True)
        return control

    @staticmethod
    def _label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        label.setFixedWidth(175)
        return label

    def _refresh_progress(self) -> None:
        current = self.current_molds.value()
        target = TowerInput(
            self.name,
            self.last_reached_floor.value(),
            current,
            self.requested_openings.value(),
        ).target_molds
        self.progress.setRange(0, max(1, target))
        self.progress.setValue(current)
        self.progress.setFormat(f"{current} / {target} Mold")

    def request(self) -> TowerInput:
        return TowerInput(self.name, self.last_reached_floor.value(), self.current_molds.value(), self.requested_openings.value())

    def save_state(self) -> SavedTowerState:
        return SavedTowerState(self.last_reached_floor.value(), self.current_molds.value(), self.requested_openings.value())

    def restore_state(self, state: SavedTowerState) -> None:
        self.last_reached_floor.setValue(state.last_reached_floor)
        self.current_molds.setValue(state.current_molds)
        self.requested_openings.setValue(state.requested_openings)


class MainWindow(QMainWindow):
    def __init__(self, data_path: Path, reports_path: Path, icons_path: Path) -> None:
        super().__init__()
        self.storage = JsonStorage(data_path)
        self.reports_path = reports_path
        self.towers: dict[str, TowerWidget] = {}
        self.last_report = ""
        self.setWindowTitle("NIKKE Tower Tracker")
        self.resize(1120, 920)
        self.setMinimumSize(980, 800)
        self._build(icons_path)
        self._restore()
        self._style()

    def _build(self, icons_path: Path) -> None:
        root, root_layout = QWidget(), QVBoxLayout()
        root.setLayout(root_layout)
        root_layout.setContentsMargins(24, 24, 24, 24)
        form, layout = QWidget(), QVBoxLayout()
        form.setLayout(layout)
        layout.setSpacing(16)
        title = QLabel("NIKKE Tower Tracker")
        title.setObjectName("appTitle")
        layout.addWidget(title)
        layout.addWidget(self._day_selector())

        grid = QGridLayout()
        for index, name in enumerate(TOWER_NAMES):
            tower = TowerWidget(name, icons_path / ICON_FILENAMES[name])
            tower.values_changed.connect(self._inputs_changed)
            self.towers[name] = tower
            grid.addWidget(tower, index // 2, index % 2)
        layout.addLayout(grid)

        buttons = QHBoxLayout()
        calculate = QPushButton("Calculate")
        calculate.setObjectName("primaryButton")
        calculate.clicked.connect(self.calculate)
        self.report_button = QPushButton("Create TXT Report")
        self.report_button.setEnabled(False)
        self.report_button.clicked.connect(self.write_report)
        buttons.addWidget(calculate)
        buttons.addWidget(self.report_button)
        buttons.addStretch()
        layout.addLayout(buttons)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(240)
        self.output.setPlaceholderText("Calculation results will appear here.")
        splitter = QSplitter(Qt.Orientation.Vertical)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(form)
        splitter.addWidget(scroll)
        splitter.addWidget(self.output)
        splitter.setSizes([500, 340])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        root_layout.addWidget(splitter)
        self.setCentralWidget(root)

    def _day_selector(self) -> QGroupBox:
        group = QGroupBox("What day is today?")
        layout = QHBoxLayout(group)
        self.days = QButtonGroup(self)
        for index, label in enumerate(DAY_LABELS):
            button = QRadioButton(label)
            button.toggled.connect(self._inputs_changed)
            self.days.addButton(button, index)
            layout.addWidget(button)
        layout.addStretch()
        return group

    def _restore(self) -> None:
        day, towers = self.storage.load()
        self.days.button(day).setChecked(True)
        for name, widget in self.towers.items():
            widget.restore_state(towers[name])

    def _save(self) -> None:
        day = max(0, self.days.checkedId())
        self.storage.save(day, {name: tower.save_state() for name, tower in self.towers.items()})

    def _inputs_changed(self) -> None:
        self._save()
        self.last_report = ""
        self.report_button.setEnabled(False)

    def calculate(self) -> None:
        self._save()
        start_day = Weekday(self.days.checkedId())
        results = [calculate_tower(tower.request(), start_day) for tower in self.towers.values()]
        self.last_report = self._format_report(results, start_day)
        self.output.setPlainText(self.last_report)
        self.report_button.setEnabled(True)

    def write_report(self) -> None:
        if not self.last_report:
            return
        self.reports_path.mkdir(exist_ok=True)
        report = self.reports_path / f"{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"
        report.write_text(self.last_report, encoding="utf-8")
        self.statusBar().showMessage(f"Report created: {report.name}", 5000)

    @staticmethod
    def _format_report(results: list[TowerCalculation], day: Weekday) -> str:
        lines = ["NIKKE TOWER TRACKER REPORT", "=" * 36, f"Start day: {DAY_LABELS[day]}", ""]
        for result in results:
            request = result.request
            lines += [
                f"[{request.tower_name}]", f"Last Reached Floor: {request.last_reached_floor}",
                f"Final Floor: {result.end_floor}",
                f"Floors Climbed: {result.climbed_floors}", f"Starting Molds: {request.current_molds}",
                f"Target Molds: {request.target_molds}", f"Final Molds: {result.final_molds}",
                f"Molds Gained: {result.gained_molds}", f"Estimated Time: {_duration(result.elapsed_days)}",
                "Floor-by-Floor Details:",
            ]
            lines += [f"Floor {item.floor} +{item.gained_molds} -> {item.total_molds}" for item in result.rewards] or ["No additional floors are required."]
            lines.append("")
        total_days = max((result.elapsed_days for result in results), default=0)
        return "\n".join(lines + ["OVERALL SUMMARY", "-" * 36, f"All towers completed in: {_duration(total_days)}"])

    def closeEvent(self, event: Any) -> None:
        self._save()
        event.accept()

    def _style(self) -> None:
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #090b10; color: #e6e9f0; } QWidget { font-size: 15px; }
            QLabel#appTitle { background: transparent; border: 0; font-size: 32px; font-weight: 700; color: #d8b35b; padding: 0; }
            QLabel#fieldLabel { background: #151922; border: 1px solid #2a3140; border-radius: 5px; color: #e6e9f0; font-weight: 700; padding: 8px 10px; }
            QGroupBox { border: 1px solid #242b38; border-radius: 9px; margin-top: 13px; padding: 18px 14px 14px; font-size: 16px; font-weight: 700; }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 7px; color: #d8b35b; background: #090b10; }
            QSpinBox, QTextEdit { background: #11151d; border: 1px solid #2a3140; border-radius: 6px; padding: 8px; color: #e6e9f0; font-size: 16px; min-height: 24px; }
            QSpinBox:focus, QTextEdit:focus { border-color: #a98b49; }
            QRadioButton { border: 1px solid #2a3140; border-radius: 5px; padding: 8px 11px; color: #e6e9f0; font-weight: 700; }
            QRadioButton:checked { background: #191f2a; border-color: #a98b49; }
            QRadioButton::indicator { width: 18px; height: 18px; border: 2px solid #8f98a9; border-radius: 10px; background: #090b10; }
            QRadioButton::indicator:checked { border: 6px solid #d8b35b; background: #090b10; }
            QPushButton { background: #1b212d; border: 1px solid #30394a; border-radius: 7px; padding: 11px 22px; color: #e6e9f0; font-size: 16px; font-weight: 700; }
            QPushButton#primaryButton, QProgressBar::chunk { background: #a98b49; color: #090b10; }
            QPushButton:disabled { background: #12161e; color: #606979; }
            QProgressBar { background: #11151d; border: 1px solid #2a3140; border-radius: 6px; color: #e6e9f0; font-size: 15px; font-weight: 700; text-align: center; min-height: 28px; }
            QScrollArea, QScrollArea > QWidget > QWidget, QStatusBar { background: #090b10; border: 0; }
            QScrollBar { background: #0d1016; } QScrollBar::handle { background: #303847; border-radius: 5px; min-height: 24px; }
            QSplitter::handle { background: #242b38; height: 3px; }
        """)


def _duration(days: int) -> str:
    weeks, remainder = divmod(days, 7)
    return f"{weeks} weeks {remainder} days ({days} days)"
