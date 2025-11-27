from ursina import *
import puntaje 


def mostrar_mensaje_centrado(texto, color_texto=color.white, duracion=4, tam=2):
    """Muestra un mensaje en el centro de la pantalla y se borra solo."""
    mensaje = Text(
        text=texto,
        origin=(0, 0),
        scale=tam,
        color=color_texto,
        parent=camera.ui
    )
    destroy(mensaje, delay=duracion)


def abrir_tienda_trampas(tablero, jugador_actual):

    puntos_actuales = puntaje.puntaje_jugador1 if jugador_actual == 1 else puntaje.puntaje_jugador2

    # Validación mínimo 700 puntos
    if puntos_actuales < 700:
        mostrar_mensaje_centrado(
            f"No tienes los 700 puntos necesarios.\nPuntos actuales: {puntos_actuales}",
            color_texto=color.red,
            duracion=5,
            tam=2.2
        )
        return

    if hasattr(tablero, 'boton_dado'):
        tablero.boton_dado.enabled = False
    if hasattr(tablero, 'boton_tienda'):
        tablero.boton_tienda.enabled = False

    jugador = tablero.jugador1 if jugador_actual == 1 else tablero.jugador2
    rival   = tablero.jugador2 if jugador_actual == 1 else tablero.jugador1

    # UI tienda
    ui = Entity(parent=camera.ui)

    info = Text(
        f"Tienda de trampas - Puntaje disponible: {puntos_actuales}",
        scale=1.2,
        color=color.yellow,
        y=.38,
        parent=ui
    )

    # Precios (Intercambiar posiciones y Turbo eliminados)
    precios = {
        "Firewall": 7,
        "Phishing": 5,
        "DDoS": 6,
        "Ransomware": 9,
        "Zero-Day": 10,
        "Robar ayuda": 5,
        "Resbalón": 6,
        "Avanzar 10": 8
    }

    # Restar puntaje
    def restar_puntaje_modulo(jugador_idx, puntos):
        if jugador_idx == 1:
            puntaje.puntaje_jugador1 = max(0, puntaje.puntaje_jugador1 - puntos)
            return puntaje.puntaje_jugador1
        else:
            puntaje.puntaje_jugador2 = max(0, puntaje.puntaje_jugador2 - puntos)
            return puntaje.puntaje_jugador2

    # Función de compra
    def comprar_trampa(tipo):
        precio = precios.get(tipo, 0)
        nuevo_puntaje = restar_puntaje_modulo(jugador_actual, precio)

        # Actualiza UI del tablero
        if jugador_actual == 1:
            tablero.puntaje_j1 = nuevo_puntaje
            try:
                tablero.texto_puntaje_j1.text = f"Puntaje Jugador 1: {nuevo_puntaje}"
            except:
                pass
        else:
            tablero.puntaje_j2 = nuevo_puntaje
            try:
                tablero.texto_puntaje_j2.text = f"Puntaje Jugador 2: {nuevo_puntaje}"
            except:
                pass

        info.text = f"Tienda - Puntaje disponible: {nuevo_puntaje}"

        # =====================================================
        # ===================   TRAMPAS   =====================
        # =====================================================

        # FIREWALL (NO INMEDIATA)
        if tipo == "Firewall":
            rival.bloqueado = True
            info.text = "Firewall activado: el rival pierde su próximo turno"
            print("[TRAMPA] Firewall activado")

        # PHISHING
        elif tipo == "Phishing":
            if jugador_actual == 1:
                robados = min(500, puntaje.puntaje_jugador2)
                puntaje.puntaje_jugador2 -= robados
                puntaje.puntaje_jugador1 += robados
            else:
                robados = min(500, puntaje.puntaje_jugador1)
                puntaje.puntaje_jugador1 -= robados
                puntaje.puntaje_jugador2 += robados

            try:
                tablero.actualizar_puntaje_ui()
            except:
                pass

            info.text = f"PHISHING: Robaste {robados} puntos"
            mostrar_mensaje_centrado(f"Robaste {robados} puntos", color_texto=color.green, duracion=3, tam=1.6)
            print(f"[PHISHING] Robaste {robados} puntos")

        # DDoS (INMEDIATA) - Retrocede rival 3 y actualiza tablero
        elif tipo == "DDoS":
            try:
                rival.posicion = max(1, int(getattr(rival, "posicion", 1)) - 3)

                tablero.mover_a_casilla(rival, rival.posicion)

                if jugador_actual == 1:
                    tablero.pos_j2 = rival.posicion
                else:
                    tablero.pos_j1 = rival.posicion

            except Exception:
                pass

            info.text = "DDoS: El rival retrocede 3 casillas"
            mostrar_mensaje_centrado("Rival -3 casillas", color_texto=color.orange, duracion=3, tam=1.6)
            print("[DDoS] Rival retrocede 3 casillas")

        # RANSOMWARE
        elif tipo == "Ransomware":
            perdidos = 300
            if jugador_actual == 1:
                puntaje.puntaje_jugador2 = max(0, puntaje.puntaje_jugador2 - perdidos)
            else:
                puntaje.puntaje_jugador1 = max(0, puntaje.puntaje_jugador1 - perdidos)

            tablero.actualizar_puntaje_ui()
            info.text = f"Ransomware: El rival pierde {perdidos} puntos"
            mostrar_mensaje_centrado(f"Rival -{perdidos} puntos", color_texto=color.orange, duracion=3, tam=1.6)
            print(f"[RANSOMWARE] Rival pierde {perdidos} puntos")

        # Zero-Day (INMEDIATA) - Avanza 4 y actualiza tablero
        elif tipo == "Zero-Day":
            try:
                jugador.posicion = int(getattr(jugador, "posicion", 1)) + 4

                tablero.mover_a_casilla(jugador, jugador.posicion)

                if jugador_actual == 1:
                    tablero.pos_j1 = jugador.posicion
                else:
                    tablero.pos_j2 = jugador.posicion

            except Exception:
                pass

            info.text = "Zero-Day: Avanzas 4 casillas"
            mostrar_mensaje_centrado("Avanzas 4 casillas", color_texto=color.green, duracion=3, tam=1.6)
            print("[Zero-Day] Avanzaste 4 casillas")

        # Avanzar 10 (INMEDIATA)
        elif tipo == "Avanzar 10":
            try:
                jugador.posicion = int(getattr(jugador, "posicion", 1)) + 10

                tablero.mover_a_casilla(jugador, jugador.posicion)

                if jugador_actual == 1:
                    tablero.pos_j1 = jugador.posicion
                else:
                    tablero.pos_j2 = jugador.posicion

            except Exception:
                pass

            info.text = "Avanzas 10 casillas"
            mostrar_mensaje_centrado("Avanzas 10 casillas", color_texto=color.green, duracion=3, tam=1.6)
            print("[Avanzar 10] Avanzaste 10 casillas")

        # Robar ayuda
        elif tipo == "Robar ayuda":
            if hasattr(rival, "ayuda") and rival.ayuda is not None:
                jugador.ayuda = rival.ayuda
                rival.ayuda = None
                info.text = "Robaste la ayuda del rival"
                mostrar_mensaje_centrado("Robaste una ayuda", color_texto=color.green, duracion=3, tam=1.6)
                print("[Robar ayuda] Ayuda robada")
            else:
                info.text = "El rival no tenía ayuda que robar"
                print("[Robar ayuda] No había ayuda")

        # Resbalón (INMEDIATA) - Retrocede rival 2
        elif tipo == "Resbalón":
            try:
                rival.posicion = max(1, int(getattr(rival, "posicion", 1)) - 2)

                tablero.mover_a_casilla(rival, rival.posicion)

                if jugador_actual == 1:
                    tablero.pos_j2 = rival.posicion
                else:
                    tablero.pos_j1 = rival.posicion

            except Exception:
                pass

            info.text = "Resbalón: el rival retrocede 2 casillas"
            mostrar_mensaje_centrado("Rival -2 casillas", color_texto=color.orange, duracion=3, tam=1.6)
            print("[Resbalón] Rival retrocede 2 casillas")

        # Sin efecto
        else:
            info.text = f"Trampa '{tipo}' seleccionada (sin efecto implementado)"
            print(f"[TRAMPA] {tipo} no implementada completamente")

        try:
            tablero.actualizar_puntaje_ui()
        except:
            pass

        # Cerrar tienda
        ui.disable()
        if hasattr(tablero, 'boton_dado'):
            tablero.boton_dado.enabled = True
        if hasattr(tablero, 'boton_tienda'):
            tablero.boton_tienda.enabled = True

    # Botones
    botones = list(precios.keys())
    x_positions = [-0.35, 0.35]
    y = 0.15

    for i, tipo in enumerate(botones):
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

        Button(
            parent=ui,
            text=f"{tipo} ({precios[tipo]} pts)",
            model='quad',
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

    # Cerrar con ESC
    def input(key):
        if key == "escape":
            ui.disable()
            if hasattr(tablero, 'boton_dado'):
                tablero.boton_dado.enabled = True
            if hasattr(tablero, 'boton_tienda'):
                tablero.boton_tienda.enabled = True

    ui.input = input
