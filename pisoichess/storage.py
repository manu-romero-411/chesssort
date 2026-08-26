"""Persistencia en CSV dentro de ~/.config/pisoichess."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from .models import Tournament


CONFIG_DIR = Path.home() / ".config" / "pisoichess"
STATE_FILE = CONFIG_DIR / "state.json"
PLAYERS_FILE = CONFIG_DIR / "players.csv"
STANDINGS_DIR = CONFIG_DIR / "standings"


def ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STANDINGS_DIR.mkdir(parents=True, exist_ok=True)


def save_tournament(t: Tournament) -> None:
    ensure_config_dir()
    # Estado completo como JSON (ligero y legible)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(t.to_dict(), f, ensure_ascii=False, indent=2)

    # Exportar CSV de jugadores
    if t.players:
        import pandas as pd
        df = pd.DataFrame([p.to_dict() for p in t.players])
        df.to_csv(PLAYERS_FILE, index=False, encoding="utf-8")

    # Exportar CSV de clasificaciones por grupo
    for g in t.groups:
        df = t.group_standings(g)
        df.to_csv(STANDINGS_DIR / f"group_{g.name}.csv",
                  index=False, encoding="utf-8")


def load_tournament() -> Optional[Tournament]:
    ensure_config_dir()
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        return Tournament.from_dict(d)
    except Exception as e:
        print(f"Error cargando torneo: {e}")
        return None


def clear_tournament() -> None:
    ensure_config_dir()
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    if PLAYERS_FILE.exists():
        PLAYERS_FILE.unlink()
    for f in STANDINGS_DIR.glob("*.csv"):
        f.unlink()