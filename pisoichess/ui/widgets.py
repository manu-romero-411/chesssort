"""Widgets reutilizables con emojis."""
from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtGui import QFont


class ResultButton(QPushButton):
    def __init__(self, emoji: str, tooltip: str, value: int, parent: "MatchWidget"):
        super().__init__(emoji)
        self.value = value
        self.match_widget = parent
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setMinimumWidth(50)
        self.setToolTip(tooltip)
        self.setFont(QFont("Sans", 14))
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        for b in self.match_widget.result_buttons:
            if b is not self:
                b.setChecked(False)
        if self.isChecked():
            self.match_widget.set_result(self.value)
        else:
            self.match_widget.set_result(None)


class MatchWidget(QFrame):
    def __init__(self,
                 name1: str, name2: str,
                 result: Optional[int],
                 modes: int = 3,
                 editable: bool = True,
                 on_change: Optional[Callable[[Optional[int]], None]] = None,
                 clear_callback: Optional[Callable[[], None]] = None,
                 parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self.modes = modes
        self.on_change = on_change
        self.clear_callback = clear_callback
        self.editable = editable

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        self.label1 = QLabel(name1 or "—")
        self.label1.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label1.setMinimumWidth(130)
        self.label1.setWordWrap(True)

        self.label2 = QLabel(name2 or "—")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label2.setMinimumWidth(130)
        self.label2.setWordWrap(True)

        self.result_buttons: list[ResultButton] = []
        if modes == 3:
            self.result_buttons = [
                ResultButton("✅", "Gana jugador 1", 1, self),
                ResultButton("🤝", "Tablas", 0, self),
                ResultButton("✅", "Gana jugador 2", 2, self),
            ]
        else:
            self.result_buttons = [
                ResultButton("✅", "Gana jugador 1", 1, self),
                ResultButton("✅", "Gana jugador 2", 2, self),
            ]

        layout.addWidget(self.label1)
        for b in self.result_buttons:
            layout.addWidget(b)
            b.setEnabled(editable)
        layout.addWidget(self.label2)

        if clear_callback is not None:
            self.clear_btn = QPushButton("🗑️")
            self.clear_btn.setFixedSize(32, 32)
            self.clear_btn.setToolTip("Borrar resultado")
            self.clear_btn.clicked.connect(self.clear_callback)
            self.clear_btn.setEnabled(editable)
            layout.addWidget(self.clear_btn)
        else:
            self.clear_btn = None

        self.set_result(result, emit=False)

    def set_names(self, name1: str, name2: str):
        self.label1.setText(name1 or "—")
        self.label2.setText(name2 or "—")

    def set_result(self, value: Optional[int], emit: bool = True):
        for b in self.result_buttons:
            checked = (b.value == value) if value is not None else False
            b.blockSignals(True)
            b.setChecked(checked)
            b.blockSignals(False)
        if emit and self.on_change is not None:
            self.on_change(value)

    def set_editable(self, editable: bool):
        self.editable = editable
        for b in self.result_buttons:
            b.setEnabled(editable)
        if self.clear_btn is not None:
            self.clear_btn.setEnabled(editable)