# puntaje.py

TABLA_PUNTAJE = {
    1: 100, 2: 100, 3: 50, 4: 100, 5: 100,
    6: 200, 7: 200, 8: 300, 9: 100, 10: 100,
    11: 100, 12: 100, 13: 100, 14: 100, 15: 200,
    16: 200, 17: 300, 18: 100, 19: 100, 20: 100,
    21: 100, 22: 50, 23: 200, 24: 200, 25: 500
}

# -----------------------------------
#   PUNTAJE GLOBAL DE AMBOS JUGADORES
# -----------------------------------
puntaje_jugador1 = 0
puntaje_jugador2 = 0


def obtener_puntaje(num):
    """
    Hace que las casillas 26+ repitan la tabla desde el 1.
    Ejemplo:
        26 -> 1
        27 -> 2
        50 -> 25
        51 -> 1
    """
    num_real = ((num - 1) % 25) + 1
    return TABLA_PUNTAJE.get(num_real, 0)


def sumar_puntaje_jugador(jugador, pregunta_num):
    global puntaje_jugador1, puntaje_jugador2

    puntos = obtener_puntaje(pregunta_num)

    if jugador == 1:
        puntaje_jugador1 += puntos
        print(f"[SUMA] Jugador 1 ganó {puntos} puntos (casilla {pregunta_num} → ciclo). Total = {puntaje_jugador1}")
        return puntaje_jugador1

    else:
        puntaje_jugador2 += puntos
        print(f"[SUMA] Jugador 2 ganó {puntos} puntos (casilla {pregunta_num} → ciclo). Total = {puntaje_jugador2}")
        return puntaje_jugador2
