"""Ventana para seleccionar manualmente los clasificados a eliminatorias."""
from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QGroupBox, QScrollArea, QWidget, QMessageBox,
)

from ..models import Tournament


class SelectorWindow(QDialog):
    def __init__(self, tournament: Tournament, parent=None):
        super().__init__(parent)
        self.tournament = tournament
        self.setWindowTitle("Seleccionar clasificados a eliminatorias")
        self.resize(600, 500)
        self.setModal(True)

        self.selected_adultos: List[int] = []
        self.selected_ninos: List[int] = []

        root = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        self.checkboxes: Dict[int, QCheckBox] = {}

        for category in ["adulto", "niño"]:
            top2 = tournament.get_top2_per_group(category)
            if not top2:
                continue
            
            cat_label = QLabel(f"{' ADULTOS' if category == 'adulto' else '👦 NIÑOS'}")
            cat_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 4px;")
            layout.addWidget(cat_label)

            for group_name, player_ids in top2.items():
                box = QGroupBox(f"Grupo {group_name} (top 2)")
                v = QVBoxLayout(box)
                
                for pid in player_ids:
                    p = tournament.get_player(pid)
                    if p is None:
                        continue
                    cb = QCheckBox(p.name)
                    cb.setChecked(True)  # Por defecto seleccionados
                    self.checkboxes[pid] = cb
                    v.addWidget(cb)
                
                layout.addWidget(box)

        scroll.setWidget(container)
        root.addWidget(scroll)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        
        ok_btn = QPushButton("Confirmar selección")
        ok_btn.clicked.connect(self.accept_selection)
        btn_row.addWidget(ok_btn)
        
        root.addLayout(btn_row)

    def accept_selection(self):
        self.selected_adultos = []
        self.selected_ninos = []
        
        for pid, cb in self.checkboxes.items():
            if cb.isChecked():
                p = self.tournament.get_player(pid)
                if p:
                    if p.category == "adulto":
                        self.selected_adultos.append(pid)
                    else:
                        self.selected_ninos.append(pid)
        
        if len(self.selected_adultos) < 2 and len(self.selected_ninos) < 2:
            QMessageBox.warning(self, "Aviso",
                "Debes seleccionar al menos 2 jugadores en alguna categoría.")
            return
        
        self.accept()