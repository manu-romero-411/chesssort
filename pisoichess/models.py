"""Lógica del torneo, apoyada en pandas/numpy."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict

import numpy as np
import pandas as pd


@dataclass
class Player:
    id: int
    name: str
    category: str  # "adulto" | "niño"

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "category": self.category}


@dataclass
class GroupMatch:
    round_idx: int
    player1_id: int
    player2_id: int
    result: Optional[int] = None
    locked: bool = False

    def to_dict(self) -> dict:
        return {
            "round_idx": self.round_idx,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "result": self.result,
            "locked": self.locked,
        }


@dataclass
class Group:
    name: str
    category: str
    player_ids: List[int]
    matches: List[GroupMatch] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "player_ids": self.player_ids,
            "matches": [m.to_dict() for m in self.matches],
        }


@dataclass
class KnockoutMatch:
    round_name: str
    slot: int
    category: str
    p1_id: Optional[int] = None
    p2_id: Optional[int] = None
    results: List[Optional[int]] = field(default_factory=lambda: [None, None, None])
    winner_id: Optional[int] = None
    locked: bool = False

    def to_dict(self) -> dict:
        return {
            "round_name": self.round_name,
            "slot": self.slot,
            "category": self.category,
            "p1_id": self.p1_id,
            "p2_id": self.p2_id,
            "results": self.results,
            "winner_id": self.winner_id,
            "locked": self.locked,
        }


@dataclass
class Tournament:
    players: List[Player] = field(default_factory=list)
    groups: List[Group] = field(default_factory=list)
    knockout: List[KnockoutMatch] = field(default_factory=list)
    started: bool = False
    groups_confirmed: bool = False
    knockout_start_phase: str = "cuartos"
    next_player_id: int = 1
    n_groups_adultos: int = 1
    n_groups_ninos: int = 1
    selected_adultos: List[int] = field(default_factory=list)
    selected_ninos: List[int] = field(default_factory=list)

    PHASE_ORDER = ["octavos", "cuartos", "semis"]

    def add_player(self, name: str, category: str) -> Player:
        p = Player(self.next_player_id, name.strip(), category)
        self.next_player_id += 1
        self.players.append(p)
        return p

    def get_player(self, pid: int) -> Optional[Player]:
        for p in self.players:
            if p.id == pid:
                return p
        return None

    def setup_groups(self, n_groups_adultos: int, n_groups_ninos: int) -> None:
        self.groups = []
        self.n_groups_adultos = n_groups_adultos
        self.n_groups_ninos = n_groups_ninos

        adultos = [p for p in self.players if p.category == "adulto"]
        ninos = [p for p in self.players if p.category == "niño"]
        
        random.shuffle(adultos)
        random.shuffle(ninos)

        if adultos and n_groups_adultos > 0:
            for i in range(n_groups_adultos):
                group_name = f"A-{chr(ord('A') + i)}"
                self.groups.append(Group(
                    name=group_name,
                    category="adulto",
                    player_ids=[],
                    matches=[]
                ))
            for idx, p in enumerate(adultos):
                group_idx = idx % n_groups_adultos
                self.groups[group_idx].player_ids.append(p.id)

        if ninos and n_groups_ninos > 0:
            for i in range(n_groups_ninos):
                group_name = f"N-{chr(ord('A') + i)}"
                self.groups.append(Group(
                    name=group_name,
                    category="niño",
                    player_ids=[],
                    matches=[]
                ))
            for idx, p in enumerate(ninos):
                group_idx = idx % n_groups_ninos
                self.groups[n_groups_adultos + group_idx].player_ids.append(p.id)

        for g in self.groups:
            g.matches = self._round_robin(g.player_ids)

    @staticmethod
    def _round_robin(player_ids: List[int]) -> List[GroupMatch]:
        ids = list(player_ids)
        n = len(ids)
        if n < 2:
            return []
        
        if n % 2 == 1:
            ids.append(-1)
            n += 1
        
        matches: List[GroupMatch] = []
        fixed = ids[0]
        rotating = ids[1:]
        
        for r in range(n - 1):
            pairings = [(fixed, rotating[0])]
            for i in range(1, n // 2):
                pairings.append((rotating[i], rotating[-i]))
            
            for a, b in pairings:
                if a == -1 or b == -1:
                    continue
                matches.append(GroupMatch(round_idx=r, player1_id=a, player2_id=b))
            
            rotating = [rotating[-1]] + rotating[:-1]
        
        return matches

    def group_standings(self, group: Group) -> pd.DataFrame:
        rows = []
        for pid in group.player_ids:
            p = self.get_player(pid)
            rows.append({
                "Jugador": p.name if p else "?",
                "PJ": 0, "PG": 0, "PT": 0, "PP": 0, "Pts": 0,
            })
        
        df = pd.DataFrame(rows)
        
        for m in group.matches:
            if m.result is None:
                continue
            
            p1 = self.get_player(m.player1_id)
            p2 = self.get_player(m.player2_id)
            
            if p1 is None or p2 is None:
                continue
            
            try:
                i1 = df[df["Jugador"] == p1.name].index[0]
                i2 = df[df["Jugador"] == p2.name].index[0]
            except IndexError:
                continue
            
            df.at[i1, "PJ"] += 1
            df.at[i2, "PJ"] += 1
            
            if m.result == 1:
                df.at[i1, "PG"] += 1
                df.at[i1, "Pts"] += 2
                df.at[i2, "PP"] += 1
            elif m.result == 2:
                df.at[i2, "PG"] += 1
                df.at[i2, "Pts"] += 2
                df.at[i1, "PP"] += 1
            elif m.result == 0:
                df.at[i1, "PT"] += 1
                df.at[i2, "PT"] += 1
                df.at[i1, "Pts"] += 1
                df.at[i2, "Pts"] += 1

        df = df.sort_values(by=["Pts", "PG", "PJ"], ascending=[False, False, False])
        df = df.reset_index(drop=True)
        return df

    def get_top2_per_group(self, category: str) -> Dict[str, List[int]]:
        result = {}
        for g in self.groups:
            if g.category != category:
                continue
            df = self.group_standings(g)
            top2 = df.head(2)["Jugador"].tolist()
            ids = []
            for name in top2:
                for p in self.players:
                    if p.name == name:
                        ids.append(p.id)
                        break
            result[g.name] = ids
        return result

    def all_group_matches_played(self) -> bool:
        for g in self.groups:
            for m in g.matches:
                if m.result is None:
                    return False
        return True

    def build_knockout(self, start_phase: str,
                       selected_adultos: List[int],
                       selected_ninos: List[int]) -> None:
        self.knockout_start_phase = start_phase
        self.knockout = []
        self.selected_adultos = selected_adultos
        self.selected_ninos = selected_ninos
        
        for cat, selected in [("adulto", selected_adultos), ("niño", selected_ninos)]:
            if len(selected) < 2:
                continue
            
            sizes = {"octavos": 16, "cuartos": 8, "semis": 4, "final": 2}
            target = sizes.get(start_phase, 8)
            
            if len(selected) > target:
                if len(selected) > 8:
                    start_phase_eff = "octavos"
                    target = 16
                elif len(selected) > 4:
                    start_phase_eff = "cuartos"
                    target = 8
                elif len(selected) > 2:
                    start_phase_eff = "semis"
                    target = 4
                else:
                    start_phase_eff = "final"
                    target = 2
            else:
                start_phase_eff = start_phase
            
            bracket_input = selected + [None] * (target - len(selected))
            self._build_bracket_for_category(cat, bracket_input, start_phase_eff)

    def _build_bracket_for_category(self, category: str,
                                    initial_ids: List[Optional[int]],
                                    start_phase: str) -> None:
        # Caso especial: empezar directamente en final
        if start_phase == "final":
            self.knockout.append(KnockoutMatch(
                round_name="final", slot=0, category=category,
                p1_id=initial_ids[0] if len(initial_ids) > 0 else None,
                p2_id=initial_ids[1] if len(initial_ids) > 1 else None,
            ))
            return
        
        # Flujo normal para otras fases
        idx = self.PHASE_ORDER.index(start_phase)
        phases = self.PHASE_ORDER[idx:]
        current_round = initial_ids
        
        for phase in phases:
            n_slots = len(current_round) // 2
            for s in range(n_slots):
                self.knockout.append(KnockoutMatch(
                    round_name=phase, slot=s, category=category,
                    p1_id=current_round[2 * s],
                    p2_id=current_round[2 * s + 1],
                ))
            current_round = [None] * n_slots

        # Tras semifinales: 3er puesto y final
        if "semis" in phases:
            for s in range(2):
                self.knockout.append(KnockoutMatch(
                    round_name="3er_puesto", slot=s, category=category,
                ))
            self.knockout.append(KnockoutMatch(
                round_name="final", slot=0, category=category,
            ))

    def compute_knockout_winner(self, m: KnockoutMatch) -> None:
        if m.p1_id is None or m.p2_id is None:
            m.winner_id = None
            return
        
        is_best_of_two = m.round_name in ("semis", "3er_puesto", "final")
        
        if not is_best_of_two:
            r = m.results[0]
            if r == 1:
                m.winner_id = m.p1_id
            elif r == 2:
                m.winner_id = m.p2_id
            else:
                m.winner_id = None
        else:
            pts1 = pts2 = 0
            for r in m.results[:2]:
                if r == 1:
                    pts1 += 2
                elif r == 2:
                    pts2 += 2
                elif r == 0:
                    pts1 += 1
                    pts2 += 1
            
            if pts1 > pts2:
                m.winner_id = m.p1_id
            elif pts2 > pts1:
                m.winner_id = m.p2_id
            else:
                r3 = m.results[2]
                if r3 == 1:
                    m.winner_id = m.p1_id
                elif r3 == 2:
                    m.winner_id = m.p2_id
                else:
                    m.winner_id = None

    def propagate_knockout(self) -> None:
        for cat in ("adulto", "niño"):
            for phase in self.PHASE_ORDER:
                matches = [m for m in self.knockout 
                          if m.round_name == phase and m.category == cat]
                winners = [m.winner_id for m in matches]
                
                idx = self.PHASE_ORDER.index(phase)
                if idx + 1 < len(self.PHASE_ORDER):
                    next_phase = self.PHASE_ORDER[idx + 1]
                    next_matches = [m for m in self.knockout 
                                   if m.round_name == next_phase and m.category == cat]
                    for i, nm in enumerate(next_matches):
                        if nm.locked:
                            continue
                        nm.p1_id = winners[2 * i] if 2 * i < len(winners) else None
                        nm.p2_id = winners[2 * i + 1] if 2 * i + 1 < len(winners) else None
                        self.compute_knockout_winner(nm)
                else:
                    # Tras semis: 3er puesto y final
                    losers = []
                    for mm in matches:
                        if mm.winner_id is None:
                            losers.append(None)
                        else:
                            loser = mm.p2_id if mm.winner_id == mm.p1_id else mm.p1_id
                            losers.append(loser)
                    
                    third = [m for m in self.knockout 
                            if m.round_name == "3er_puesto" and m.category == cat]
                    for i, tm in enumerate(third):
                        if not tm.locked:
                            tm.p1_id = losers[2 * i] if 2 * i < len(losers) else None
                            tm.p2_id = losers[2 * i + 1] if 2 * i + 1 < len(losers) else None
                            self.compute_knockout_winner(tm)
                    
                    final = [m for m in self.knockout 
                            if m.round_name == "final" and m.category == cat]
                    if final:
                        fm = final[0]
                        if not fm.locked:
                            fm.p1_id = winners[0] if len(winners) > 0 else None
                            fm.p2_id = winners[1] if len(winners) > 1 else None
                            self.compute_knockout_winner(fm)

    def to_dict(self) -> dict:
        return {
            "players": [p.to_dict() for p in self.players],
            "groups": [g.to_dict() for g in self.groups],
            "knockout": [k.to_dict() for k in self.knockout],
            "started": self.started,
            "groups_confirmed": self.groups_confirmed,
            "knockout_start_phase": self.knockout_start_phase,
            "next_player_id": self.next_player_id,
            "n_groups_adultos": self.n_groups_adultos,
            "n_groups_ninos": self.n_groups_ninos,
            "selected_adultos": self.selected_adultos,
            "selected_ninos": self.selected_ninos,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Tournament":
        t = cls()
        t.players = [Player(**p) for p in d.get("players", [])]
        t.started = d.get("started", False)
        t.groups_confirmed = d.get("groups_confirmed", False)
        t.knockout_start_phase = d.get("knockout_start_phase", "cuartos")
        t.next_player_id = d.get("next_player_id", 1)
        t.n_groups_adultos = d.get("n_groups_adultos", 1)
        t.n_groups_ninos = d.get("n_groups_ninos", 1)
        t.selected_adultos = d.get("selected_adultos", [])
        t.selected_ninos = d.get("selected_ninos", [])
        
        for gd in d.get("groups", []):
            matches = [GroupMatch(**m) for m in gd.get("matches", [])]
            t.groups.append(Group(
                name=gd["name"],
                category=gd["category"],
                player_ids=gd["player_ids"],
                matches=matches,
            ))
        
        t.knockout = [KnockoutMatch(**k) for k in d.get("knockout", [])]
        return t