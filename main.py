#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from pisoichess.models import Tournament
from pisoichess.storage import load_tournament, save_tournament
from pisoichess.ui.setup_window import SetupWindow
from pisoichess.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Pisoichess")

    # Cargar torneo previo si existe; si no, crear uno vacío
    tournament = load_tournament()
    if tournament is None:
        tournament = Tournament()

    if tournament.started:
        # Si ya hay torneo iniciado, ir directo a la ventana principal
        win = MainWindow(tournament)
        win.show()
    else:
        # Ventana inicial de configuración
        win = SetupWindow(tournament)
        win.show()

    ret = app.exec()
    # Guardar al salir (solo si hay algo que guardar)
    if tournament.players or tournament.started:
        save_tournament(tournament)
    sys.exit(ret)


if __name__ == "__main__":
    main()