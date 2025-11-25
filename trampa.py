# trampa.py
from ursina import *

def abrir_tienda_trampas(tablero, jugador_actual):
    """
    tablero: instancia del Tablero
    jugador_actual: 1 o 2
    """

    # Identificar jugador y rival
    jugador = tablero.jugador1 if jugador_actual == 1 else tablero.jugador2
    rival   = tablero.jugador2 if jugador_actual == 1 else tablero.jugador1

    # Obtener puntaje actual
    puntaje = tablero.puntaje_j1 if jugador_actual == 1 else tablero.puntaje_j2

    # PRECIOS
    precios = {
        "robar": 5,
        "intercambiar": 8,
        "dado_neg": 6,
        "perder_ayuda": 4
    }

    # --- Ventana ---
    tienda = WindowPanel(
        title="🛒 Tienda de Trampas",
        content=[],
        popup=True
    )

    # Texto informativo
    info = Text(f"Puntaje disponible: {puntaje}", scale=1, color=color.yellow)
    tienda.content.append(info)
    tienda.content.append(Text("Selecciona una trampa:", scale=1))

    # -----------------------------------------------------
    # ACCIONES DE CADA TRAMPA
    # -----------------------------------------------------

    def comprar_trampa(tipo):
        nonlocal puntaje

        costo = precios[tipo]

        if puntaje < costo:
            print("❌ No tienes suficiente puntaje.")
            info.text = f"Puntaje disponible: {puntaje} (INSUFICIENTE)"
            info.color = color.red
            return

        # Pagar
        puntaje -= costo
        info.text = f"Puntaje disponible: {puntaje}"
        info.color = color.yellow

        # Actualizar puntaje del tablero
        if jugador_actual == 1:
            tablero.puntaje_j1 = puntaje
            tablero.texto_puntaje_j1.text = f"Puntaje Jugador 1: {puntaje}"
        else:
            tablero.puntaje_j2 = puntaje
            tablero.texto_puntaje_j2.text = f"Puntaje Jugador 2: {puntaje}"

        # --------------------------
        #   EFECTOS DE LAS TRAMPAS
        # --------------------------

        if tipo == "robar":
            if rival.ayudas > 0:
                rival.ayudas -= 1
                jugador.ayudas += 1
                print("🟢 Robaste una ayuda al rival.")
            else:
                print("⚠ El rival no tiene ayudas para robar.")

        elif tipo == "intercambiar":
            # Intercambiar posiciones
            pos_j = jugador.posicion
            pos_r = rival.posicion

            tablero.mover_directo(jugador, pos_r)
            tablero.mover_directo(rival, pos_j)

            print("🟢 Intercambiaste posiciones con el rival.")

        elif tipo == "dado_neg":
            jugador.dado_negativo = True
            print("🟢 Tu próximo dado será NEGATIVO.")

        elif tipo == "perder_ayuda":
            if jugador.ayudas > 0:
                jugador.ayudas -= 1
                print("🟢 Perdiste una ayuda voluntariamente (trampa).")
            else:
                print("⚠ No tienes ayudas para perder.")

    # -----------------------------------------------------
    # BOTONES DE LA TIENDA
    # -----------------------------------------------------

    tienda.content.append(Button(
        text=f"Robar ayuda ({precios['robar']} pts)",
        color=color.azure,
        on_click=lambda: comprar_trampa("robar")
    ))

    tienda.content.append(Button(
        text=f"Intercambiar posiciones ({precios['intercambiar']} pts)",
        color=color.orange,
        on_click=lambda: comprar_trampa("intercambiar")
    ))

    tienda.content.append(Button(
        text=f"Dado negativo ({precios['dado_neg']} pts)",
        color=color.magenta,
        on_click=lambda: comprar_trampa("dado_neg")
    ))

    tienda.content.append(Button(
        text=f"Perder ayuda ({precios['perder_ayuda']} pts)",
        color=color.red,
        on_click=lambda: comprar_trampa("perder_ayuda")
    ))

    # Botón cerrar
    tienda.content.append(Button(text="Cerrar", color=color.gray, on_click=tienda.close))
