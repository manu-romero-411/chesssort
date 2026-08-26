"""Ventana principal."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QScrollArea, QLabel, QGroupBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
)

from ..models import Tournament
from .rounds_window import RoundsWindow
from .elimination_widget import EliminationWidget
from .selector_window import SelectorWindow


class MainWindow(QMainWindow):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
        self.setWindowTitle("Pisoichess — Torneo")
        self.resize(1100, 750)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Pestaña 1: Fase de grupos
        self.groups_tab = QWidget()
        g_layout = QVBoxLayout(self.groups_tab)
        g_layout.setSpacing(16)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.groups_container = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.groups_layout.setSpacing(16)
        self.scroll.setWidget(self.groups_container)
        g_layout.addWidget(self.scroll)

        btn_row = QHBoxLayout()
        self.rounds_btn = QPushButton("📋 Ver Rondas")
        self.rounds_btn.clicked.connect(self.open_rounds_window)
        btn_row.addWidget(self.rounds_btn)

        btn_row.addStretch()

        self.confirm_btn = QPushButton("✅ Confirmar resultados")
        self.confirm_btn.clicked.connect(self.confirm_results)
        self.confirm_btn.setEnabled(not self.tournament.groups_confirmed)
        btn_row.addWidget(self.confirm_btn)
        g_layout.addLayout(btn_row)

        self.tabs.addTab(self.groups_tab, "Fase de grupos")

        # Pestaña 2: Fase eliminatoria
        self.elimination_tab = EliminationWidget(self.tournament)
        self.tabs.addTab(self.elimination_tab, "Fase eliminatoria")
        self.tabs.setTabEnabled(1, self.tournament.groups_confirmed)

        self.rounds_window: RoundsWindow | None = None

        self.refresh_standings()

    def refresh_standings(self):
        while self.groups_layout.count():
            item = self.groups_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        for category in ["adulto", "niño"]:
            cat_groups = [g for g in self.tournament.groups if g.category == category]
            if not cat_groups:
                continue
            
            cat_label = QLabel(f"{'👨 ADULTOS' if category == 'adulto' else '👦 NIÑOS'}")
            cat_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 8px;")
            self.groups_layout.addWidget(cat_label)

            for g in cat_groups:
                box = QGroupBox(f"Grupo {g.name}")
                v = QVBoxLayout(box)

                df = self.tournament.group_standings(g)
                table = QTableWidget(len(df), len(df.columns))
                table.setHorizontalHeaderLabels(df.columns.tolist())
                table.verticalHeader().setVisible(False)
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table.setFixedHeight(40 + 32 * len(df))

                for r in range(len(df)):
                    for c, col in enumerate(df.columns):
                        val = df.iloc[r][col]
                        item = QTableWidgetItem(str(val))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        table.setItem(r, c, item)

                v.addWidget(table)
                self.groups_layout.addWidget(box)

        self.groups_layout.addStretch()

        if self.rounds_window is not None:
            self.rounds_window.refresh_all()

    def open_rounds_window(self):
        if self.rounds_window is None or not self.rounds_window.isVisible():
            self.rounds_window = RoundsWindow(self.tournament, parent=self)
            self.rounds_window.show()
        else:
            self.rounds_window.raise_()
            self.rounds_window.activateWindow()

    def confirm_results(self):
        if not self.tournament.all_group_matches_played():
            QMessageBox.warning(
                self, "Aviso",
                "Aún hay enfrentamientos sin resultado en algún grupo.")
            return
        
        for g in self.tournament.groups:
            for m in g.matches:
                m.locked = True
        
        self.tournament.groups_confirmed = True
        self.confirm_btn.setEnabled(False)
        self.tabs.setTabEnabled(1, True)
        
        if self.rounds_window is not None:
            self.rounds_window.close()
            self.rounds_window = None

    def open_selector(self):
        """Abre ventana de selección de clasificados."""
        selector = SelectorWindow(self.tournament, parent=self)
        if selector.exec():
            self.tournament.selected_adultos = selector.selected_adultos
            self.tournament.selected_ninos = selector.selected_ninos