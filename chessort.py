#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import random
def print_group_table(group, group_number):
    str = "Jugadores                       PTS   J   G   E   P\n"
    for i in group:
        size = len(i)
        hyphens = " "
        for j in range(0, 30 - size):
            hyphens += "-"
        str = str + f"{i}{hyphens} 0     0   0   0   0\n"
    return str

import random

def seleccionar_matches_por_ronda(result, matches_per_round, max_retries=12):
    """
    result: lista de tuplas/pairs [(a,b), (c,d), ...]
    matches_per_round: número deseado de matches en la ronda
    max_retries: cuántas veces reintentar si no se alcanza el número deseado
    Devuelve: lista de matches seleccionados para la ronda
    """
    if matches_per_round < 0:
        return []

    for attempt in range(max_retries):
        pool = result[:]             # copia inmutable del original
        random.shuffle(pool)        # barajar para aleatoriedad rápida
        used = set()
        matches = []

        for pair in pool:
            a, b = pair
            if a in used or b in used:
                continue
            matches.append(pair)
            used.add(a); used.add(b)
            if len(matches) >= matches_per_round:
                break

        if len(matches) >= matches_per_round:
            return matches

    # Si llegamos aquí, no se pudo formar la cantidad pedida
    # Devolvemos lo máximo posible (o lanzar excepción según preferencia)
    return matches

def print_matches(group):
    rounds = len(group) - 1
    matches_per_round = len(group) // 2
    first_idx = {}
    for i, s in enumerate(group):
        first_idx.setdefault(s, i)

    result = []
    for a in group:
        for b in group:
            if first_idx[a] <= first_idx[b]:
                result.append((a, b))
    
    for i in result:
        if i[0] == i[1]:
            result.remove(i)

    final = []
    for i in range(0, rounds):
        matches = seleccionar_matches_por_ronda(result, matches_per_round)
        for j in matches:
            result.remove(j)

        final.append(matches)

    return final
                        

def main():
    parser = argparse.ArgumentParser(description="Leer jugadores de un .txt y agruparlos para un torneo de ajedrez")
    parser.add_argument("ruta", help="Ruta (absoluta o relativa) al archivo .txt")
    parser.add_argument("-n", "--grupo", type=int, required=True,
                        help="Número de jugadores por grupo (entero positivo)")
    
    args = parser.parse_args()
    persons_per_group = args.grupo

    path = Path(args.ruta)

    if not path.exists():
        print(f"Error: el archivo no existe: {path}", file=sys.stderr)
        sys.exit(1)

    if not path.is_file():
        print(f"Error: la ruta no es un archivo: {path}", file=sys.stderr)
        sys.exit(1)

    if persons_per_group <= 0:
        print("Error: el número de jugadores por grupo debe ser un entero positivo", file=sys.stderr)
        sys.exit(1)

    lines = []

    with open(path) as f:
        for line in f:
            if line.strip() != "":
                lines.append(line.strip())
    f.close()

    if len(lines) == 0:
        print("Error: el archivo está vacío", file=sys.stderr)
        sys.exit(1)

    lines = random.sample(lines, len(lines))     
    
    if persons_per_group > len(lines) // 2:
        print("Error: el número de jugadores por grupo no puede ser mayor que la mitad del número total de jugadores", file=sys.stderr)
        sys.exit(1)

    num_groups = (len(lines)) // persons_per_group  # Redondeo hacia arriba
    groups = []

    for i in range(0, num_groups):
        current_group = []
        for j in range(0, persons_per_group):
            current_group.append(lines[-1])
            lines.pop()

        groups.append(current_group)

    for i in range(0, len(lines)):
        groups[i % num_groups].append(lines[i])
        lines.pop(i)

    it = 1
    print_group_table_str = ""
    for i in groups:
        print_group_table_str += print_group_table(i, it) + "\n"
        matches = print_matches(i)
        it2 = 0
        for i in matches:
            print_group_table_str += f"\n\nRonda {str(it2 + 1)}:\n"
            for j in i:
                print_group_table_str += f"{j[0]} [] vs [] {j[1]}\n"
            it2 += 1
        print_group_table_str += "\n==============================\n\n"
        it += 1
        

    print(print_group_table_str)


if __name__ == "__main__":
    main()