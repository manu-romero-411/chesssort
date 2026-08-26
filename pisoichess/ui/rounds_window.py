"""Ventana de rondas con layout limpio."""
from typing import Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, 
    QWidget, QGroupBox, QFrame,
)

from ..models import Tournament, Group, GroupMatch
from .widgets import MatchWidget


class RoundsWindow(QDialog):
    def __init__(self, tournament: Tournament, parent=None):
        super().__init__(parent)
        self.tournament = tournament
        self.setWindowTitle("Rondas — Fase de grupos")
        self.resize(700, 800)
        self.setModal(False)

        root = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setSpacing(16)
        
        scroll.setWidget(container)
        root.addWidget(scroll)

        self.match_widgets: Dict[tuple, MatchWidget] = {}
        self.rebuild()

    def rebuild(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.match_widgets.clear()

        for category in ["adulto", "niño"]:
            cat_groups = [g for g in self.tournament.groups if g.category == category]
            if not cat_groups:
                continue
            
            cat_label = QLabel(f"{' ADULTOS' if category == 'adulto' else '👦 NIÑOS'}")
            cat_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 8px;")
            self.main_layout.addWidget(cat_label)

            for g in cat_groups:
                box = QGroupBox(f"Grupo {g.name}")
                v = QVBoxLayout(box)
                v.setSpacing(12)
                
                rounds: Dict[int, List[GroupMatch]] = {}
                for m in g.matches:
                    rounds.setdefault(m.round_idx, []).append(m)
                
                for r_idx in sorted(rounds.keys()):
                    ronda_label = QLabel(f"Ronda {r_idx + 1}")
                    ronda_label.setStyleSheet("font-weight: bold; font-size: 13px;")
                    v.addWidget(ronda_label)
                    
                    for i, m in enumerate(rounds[r_idx]):
                        p1 = self.tournament.get_player(m.player1_id)
                        p2 = self.tournament.get_player(m.player2_id)
                        
                        mw = MatchWidget(
                            name1=p1.name if p1 else "?",
                            name2=p2.name if p2 else "?",
                            result=m.result,
                            modes=3,
                            editable=not m.locked,
                            on_change=lambda val, gg=g, mm=m: self._on_result(gg, mm, val),
                        )
                        v.addWidget(mw)
                        self.match_widgets[(g.name, r_idx, i)] = mw
                
                self.main_layout.addWidget(box)
            
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            self.main_layout.addWidget(separator)
        
        self.main_layout.addStretch()

    def _on_result(self, group: Group, match: GroupMatch, value):
        match.result = value
        parent = self.parent()
        if parent is not None and hasattr(parent, "refresh_standings"):
            parent.refresh_standings()

    def refresh_all(self):
        for g in self.tournament.groups:
            rounds: Dict[int, List[GroupMatch]] = {}
            for m in g.matches:
                rounds.setdefault(m.round_idx, []).append(m)
            
            for r_idx in sorted(rounds.keys()):
                for i, m in enumerate(rounds[r_idx]):
                    key = (g.name, r_idx, i)
                    if key not in self.match_widgets:
                        continue
                    
                    mw = self.match_widgets[key]
                    p1 = self.tournament.get_player(m.player1_id)
                    p2 = self.tournament.get_player(m.player2_id)
                    mw.set_names(p1.name if p1 else "?", p2.name if p2 else "?")
                    mw.set_result(m.result, emit=False)
                    mw.set_editable(not m.locked)