from ursina import *
import random

def abrir_tienda_trampas(tablero, jugador_actual):

    # ---------------------------------------------------------
    # Ocultar botones del tablero
    # ---------------------------------------------------------
    if hasattr(tablero, 'ui_general'):
        tablero.ui_general.disable()

    if hasattr(tablero, 'boton_dado'):
        tablero.boton_dado.enabled = False
    if hasattr(tablero, 'boton_tienda'):
        tablero.boton_tienda.enabled = False

    # Jugadores
    jugador = tablero.jugador1 if jugador_actual == 1 else tablero.jugador2
    rival   = tablero.jugador2 if jugador_actual == 1 else tablero.jugador1
    puntaje = tablero.puntaje_j1 if jugador_actual == 1 else tablero.puntaje_j2

    # Proteger atributos
    for obj in (jugador, rival):
        if not hasattr(obj, 'ayudas'): obj.ayudas = 0
        if not hasattr(obj, 'bloqueado'): obj.bloqueado = False
        if not hasattr(obj, 'ddos'): obj.ddos = False
        if not hasattr(obj, 'sql_inyeccion'): obj.sql_inyeccion = False
        if not hasattr(obj, 'zero_day'): obj.zero_day = False
        if not hasattr(obj, 'dado_negativo'): obj.dado_negativo = False

    # Precios
    precios = {
        "firewall": 7,
        "sql": 6,
        "phishing": 5,
        "ddos": 6,
        "ransom": 9,
        "zero_day": 10,
        "robar": 5,
        "intercambiar": 8,
        "dado_neg": 6,
        "perder_ayuda": 4,
    }

    # ---------------------------------------------------------
    # UI contenedor central
    # ---------------------------------------------------------
    ui = Entity(parent=camera.ui)

    info = Text(
        f"Puntaje disponible: {puntaje}",
        scale=1.3,
        color=color.yellow,
        y=.38,
        parent=ui
    )

    # ---------------------------------------------------------
    # CIERRA TIENDA Y REACTIVA EL TABLERO
    # ---------------------------------------------------------
    def cerrar_tienda():
        ui.disable()
        if hasattr(tablero, 'ui_general'):
            tablero.ui_general.enable()
        tablero.boton_dado.enabled = True
        tablero.boton_tienda.enabled = True

    # ---------------------------------------------------------
    # Función comprar
    # ---------------------------------------------------------
    def comprar_trampa(tipo):
        nonlocal puntaje
        costo = precios[tipo]

        if puntaje < costo:
            info.text = f"Puntaje: {puntaje} (insuficiente)"
            info.color = color.red
            return

        # Cobrar puntos
        puntaje -= costo
        info.text = f"Puntaje disponible: {puntaje}"
        info.color = color.yellow

        if jugador_actual == 1:
            tablero.puntaje_j1 = puntaje
            tablero.texto_puntaje_j1.text = f"Puntaje Jugador 1: {puntaje}"
        else:
            tablero.puntaje_j2 = puntaje
            tablero.texto_puntaje_j2.text = f"Puntaje Jugador 2: {puntaje}"

        # ----------- Lógica de trampas --------------
        if tipo == "firewall":
            rival.bloqueado = True

        elif tipo == "sql":
            jugador.sql_inyeccion = True

        elif tipo == "phishing":
            if random.random() < 0.5 and rival.ayudas > 0:
                rival.ayudas -= 1
                jugador.ayudas += 1

        elif tipo == "ddos":
            rival.ddos = True

        elif tipo == "ransom":
            new_pos = max(0, rival.posicion - 2)
            tablero.mover_a_casilla(rival, new_pos)

        elif tipo == "zero_day":
            jugador.zero_day = True

        elif tipo == "robar":
            if rival.ayudas > 0:
                rival.ayudas -= 1
                jugador.ayudas += 1

        elif tipo == "intercambiar":
            p1 = jugador.posicion
            p2 = rival.posicion
            tablero.mover_a_casilla(jugador, p2)
            tablero.mover_a_casilla(rival, p1)

        elif tipo == "dado_neg":
            jugador.dado_negativo = True

        elif tipo == "perder_ayuda":
            if jugador.ayudas > 0:
                jugador.ayudas -= 1

        # ✔ Cerrar tienda automáticamente después de comprar
        cerrar_tienda()

    # ---------------------------------------------------------
    # Botones en 2 COLUMNAS con fondo negro real
    # ---------------------------------------------------------
    botones = [
        ("Firewall - Rival no avanza", "firewall"),
        ("Inyección SQL - Avanza +1", "sql"),
        ("Phishing - 50% robar ayuda", "phishing"),
        ("DDoS - Rival sin ayudas", "ddos"),
        ("Ransomware - Rival -2 casillas", "ransom"),
        ("Exploit Zero-Day - Auto win", "zero_day"),
        ("Robar ayuda", "robar"),
        ("Intercambiar posiciones", "intercambiar"),
        ("Dado negativo", "dado_neg"),
        ("Perder ayuda propia", "perder_ayuda"),
    ]

    x_positions = [-0.35, 0.35]
    y = 0.15

    for i, (texto, tipo) in enumerate(botones):
        columna = i % 2
        fila = i // 2

        pos_x = x_positions[columna]
        pos_y = y - (fila * 0.11)

        Entity(
            parent=ui,
            model="quad",
            color=color.black,
            scale=(0.58, 0.075),
            x=pos_x,
            y=pos_y,
        )

        btn = Button(
            parent=ui,
            text=f"{texto} ({precios[tipo]} pts)",
            model='quad',
            texture=None,
            disable_texture=True,
            color=color.black,
            highlight_color=color.black,
            pressed_color=color.black,
            text_color=color.white,
            scale=(0.55, 0.07),
            x=pos_x,
            y=pos_y,
            on_click=lambda t=tipo: comprar_trampa(t)
        )

        if hasattr(btn, 'graphic'):
            btn.graphic.color = color.black

    # ---------------------------------------------------------
    # Cerrar tienda con ESCAPE
    # ---------------------------------------------------------
    def input(key):
        if key == "escape":
            cerrar_tienda()

    ui.input = input
