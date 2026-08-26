"""Ventana inicial de configuración."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton, QListWidget,
    QMessageBox, QGroupBox, QSpinBox, QFormLayout,
)

from ..models import Tournament
from ..storage import clear_tournament
from .main_window import MainWindow


class SetupWindow(QMainWindow):
    def __init__(self, tournament: Tournament):
        super().__init__()
        self.tournament = tournament
        self.setWindowTitle("Pisoichess — Configuración inicial")
        self.resize(700, 600)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Grupo de jugadores
        group_players = QGroupBox("Jugadores")
        g_layout = QVBoxLayout(group_players)

        row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del jugador")
        self.category_input = QComboBox()
        self.category_input.addItems(["adulto", "niño"])
        add_btn = QPushButton("Añadir")
        add_btn.clicked.connect(self.add_player)
        
        row.addWidget(QLabel("Nombre:"))
        row.addWidget(self.name_input)
        row.addWidget(QLabel("Categoría:"))
        row.addWidget(self.category_input)
        row.addWidget(add_btn)
        g_layout.addLayout(row)

        self.player_list = QListWidget()
        g_layout.addWidget(self.player_list)

        remove_btn = QPushButton("Eliminar seleccionado")
        remove_btn.clicked.connect(self.remove_player)
        g_layout.addWidget(remove_btn)

        root.addWidget(group_players)

        # Configuración de grupos separados
        group_cfg = QGroupBox("Configuración de grupos")
        c_layout = QFormLayout(group_cfg)
        
        self.n_groups_adultos_spin = QSpinBox()
        self.n_groups_adultos_spin.setMinimum(1)
        self.n_groups_adultos_spin.setMaximum(8)
        self.n_groups_adultos_spin.setValue(1)
        c_layout.addRow("Número de grupos (adultos):", self.n_groups_adultos_spin)
        
        self.n_groups_ninos_spin = QSpinBox()
        self.n_groups_ninos_spin.setMinimum(1)
        self.n_groups_ninos_spin.setMaximum(8)
        self.n_groups_ninos_spin.setValue(1)
        c_layout.addRow("Número de grupos (niños):", self.n_groups_ninos_spin)
        
        root.addWidget(group_cfg)

        # Botones
        btn_row = QHBoxLayout()
        start_btn = QPushButton("Iniciar torneo")
        start_btn.clicked.connect(self.start_tournament)
        btn_row.addWidget(start_btn)

        if self.tournament.started:
            cont_btn = QPushButton("Continuar torneo actual")
            cont_btn.clicked.connect(self.continue_tournament)
            btn_row.addWidget(cont_btn)

        reset_btn = QPushButton("Reiniciar todo")
        reset_btn.clicked.connect(self.reset_all)
        btn_row.addWidget(reset_btn)

        root.addLayout(btn_row)

        # Cargar jugadores existentes
        for p in self.tournament.players:
            self._add_to_list(p.name, p.category)

    def _add_to_list(self, name: str, category: str):
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(f"[{category}] {name}")
        self.player_list.addItem(item)

    def add_player(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Introduce un nombre.")
            return
        cat = self.category_input.currentText()
        self.tournament.add_player(name, cat)
        self._add_to_list(name, cat)
        self.name_input.clear()
        self.name_input.setFocus()

    def remove_player(self):
        row = self.player_list.currentRow()
        if row < 0:
            return
        self.player_list.takeItem(row)
        if row < len(self.tournament.players):
            self.tournament.players.pop(row)

    def start_tournament(self):
        if len(self.tournament.players) < 2:
            QMessageBox.warning(self, "Aviso",
                                "Necesitas al menos 2 jugadores para iniciar.")
            return
        
        n_adultos = self.n_groups_adultos_spin.value()
        n_ninos = self.n_groups_ninos_spin.value()
        
        self.tournament.setup_groups(n_adultos, n_ninos)
        self.tournament.started = True
        
        self.main_win = MainWindow(self.tournament)
        self.main_win.show()
        self.close()

    def continue_tournament(self):
        self.main_win = MainWindow(self.tournament)
        self.main_win.show()
        self.close()

    def reset_all(self):
        reply = QMessageBox.question(
            self, "Confirmar",
            "¿Seguro que quieres borrar todo el torneo actual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            clear_tournament()
            self.tournament = Tournament()
            self.player_list.clear()