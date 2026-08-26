"""Widget de eliminatorias con layout vertical (adultos arriba, niños abajo)."""
from typing import Dict

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QGroupBox, QComboBox, QPushButton,
)

from ..models import Tournament, KnockoutMatch
from .widgets import MatchWidget


class EliminationWidget(QWidget):
    def __init__(self, tournament: Tournament, parent=None):
        super().__init__(parent)
        self.tournament = tournament
        self.match_widgets: Dict[int, Dict] = {}
        self._build_ui()
        self.rebuild()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Fase inicial:"))
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(["octavos", "cuartos", "semis", "final"])
        idx = self.phase_combo.findText(self.tournament.knockout_start_phase)
        if idx >= 0:
            self.phase_combo.setCurrentIndex(idx)
        self.phase_combo.setEnabled(not self.tournament.knockout)
        ctrl.addWidget(self.phase_combo)

        self.rebuild_btn = QPushButton("Generar bracket")
        self.rebuild_btn.clicked.connect(self._on_rebuild)
        self.rebuild_btn.setEnabled(not self.tournament.knockout)
        ctrl.addWidget(self.rebuild_btn)

        ctrl.addStretch()
        root.addLayout(ctrl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.container = QWidget()
        self.v_layout = QVBoxLayout(self.container)
        self.v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.setSpacing(24)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll)

    def _on_rebuild(self):
        phase = self.phase_combo.currentText()
        self.tournament.build_knockout(
            phase,
            self.tournament.selected_adultos,
            self.tournament.selected_ninos
        )
        self.rebuild()

    def rebuild(self):
        while self.v_layout.count():
            item = self.v_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.match_widgets.clear()

        if not self.tournament.knockout:
            lbl = QLabel("Pulsa 'Generar bracket' para crear la fase eliminatoria.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("padding: 40px;")
            self.v_layout.addWidget(lbl)
            return

        col_order = (
            [p for p in self.tournament.PHASE_ORDER
             if any(m.round_name == p for m in self.tournament.knockout)]
            + ["3er_puesto", "final"]
        )

        # Adultos primero, luego niños (vertical)
        for cat in ("adulto", "niño"):
            cat_matches = [m for m in self.tournament.knockout if m.category == cat]
            if not cat_matches:
                continue
            
            cat_label = QLabel(f"{'👨 ADULTOS' if cat == 'adulto' else '👦 NIÑOS'}")
            cat_label.setStyleSheet("font-weight: bold; font-size: 16px; padding: 8px;")
            self.v_layout.addWidget(cat_label)

            # Contenedor horizontal para las rondas
            rounds_container = QWidget()
            h_layout = QHBoxLayout(rounds_container)
            h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            h_layout.setSpacing(20)

            for phase in col_order:
                matches = [m for m in cat_matches if m.round_name == phase]
                if not matches:
                    continue
                
                col = QGroupBox(self._phase_display_name(phase))
                v = QVBoxLayout(col)
                v.setSpacing(12)
                matches.sort(key=lambda m: m.slot)
                
                for m in matches:
                    self._add_match_column(v, m)
                
                v.addStretch()
                h_layout.addWidget(col)

            h_layout.addStretch()
            self.v_layout.addWidget(rounds_container)

        self.v_layout.addStretch()

    def _phase_display_name(self, phase: str) -> str:
        return {
            "octavos": "Octavos",
            "cuartos": "Cuartos",
            "semis": "Semifinales",
            "3er_puesto": "3er Puesto",
            "final": "Final",
        }.get(phase, phase)

    def _add_match_column(self, parent_layout: QVBoxLayout, m: KnockoutMatch):
        p1 = self.tournament.get_player(m.p1_id) if m.p1_id is not None else None
        p2 = self.tournament.get_player(m.p2_id) if m.p2_id is not None else None
        is_best_of_two = m.round_name in ("semis", "3er_puesto", "final")
        editable = not m.locked and m.p1_id is not None and m.p2_id is not None

        frame = QGroupBox()
        v = QVBoxLayout(frame)
        v.setSpacing(8)

        v.addWidget(QLabel("Partido 1"))
        mw1 = MatchWidget(
            name1=p1.name if p1 else "—",
            name2=p2.name if p2 else "—",
            result=m.results[0] if is_best_of_two else m.results[0],
            modes=3 if is_best_of_two else 3,
            editable=editable,
            on_change=lambda val, mm=m, idx=0: self._on_result(mm, idx, val),
        )
        v.addWidget(mw1)

        widgets = {"mw1": mw1}

        if is_best_of_two:
            v.addWidget(QLabel("Partido 2"))
            mw2 = MatchWidget(
                name1=p1.name if p1 else "—",
                name2=p2.name if p2 else "—",
                result=m.results[1],
                modes=3,
                editable=editable,
                on_change=lambda val, mm=m, idx=1: self._on_result(mm, idx, val),
            )
            v.addWidget(mw2)
            widgets["mw2"] = mw2

            mw3 = MatchWidget(
                name1=p1.name if p1 else "—",
                name2=p2.name if p2 else "—",
                result=m.results[2],
                modes=2,
                editable=False,
                on_change=lambda val, mm=m, idx=2: self._on_result(mm, idx, val),
                clear_callback=lambda mm=m: self._clear_match(mm),
            )
            mw3.setVisible(False)
            v.addWidget(mw3)
            widgets["mw3"] = mw3
            
            self._update_tiebreak_state(m, mw1, mw2, mw3)

        self.match_widgets[id(m)] = widgets
        parent_layout.addWidget(frame)

    def _update_tiebreak_state(self, m: KnockoutMatch, mw1, mw2, mw3):
        pts1 = pts2 = 0
        for r in (m.results[0], m.results[1]):
            if r == 1:
                pts1 += 2
            elif r == 2:
                pts2 += 2
            elif r == 0:
                pts1 += 1
                pts2 += 1
        
        tied = (m.results[0] is not None and m.results[1] is not None and pts1 == pts2)
        mw3.setVisible(tied)
        mw3.set_editable(tied and not m.locked)
        
        if not tied and len(m.results) > 2:
            m.results[2] = None
            mw3.set_result(None, emit=False)

    def _on_result(self, m: KnockoutMatch, idx: int, value):
        m.results[idx] = value
        self.tournament.compute_knockout_winner(m)
        self.tournament.propagate_knockout()
        
        if id(m) in self.match_widgets:
            widgets = self.match_widgets[id(m)]
            if "mw3" in widgets:
                self._update_tiebreak_state(m, widgets["mw1"], widgets["mw2"], widgets["mw3"])
        
        self.rebuild()
        parent = self.window()
        if hasattr(parent, "refresh_standings"):
            parent.refresh_standings()

    def _clear_match(self, m: KnockoutMatch):
        m.results = [None, None, None]
        m.winner_id = None
        self.tournament.propagate_knockout()
        self.rebuild()