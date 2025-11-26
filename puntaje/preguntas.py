from ursina import *
import random
from estructuras import (
    cargar_preguntas,
    seleccionar_pregunta_aleatoria,
    validar_respuesta,
    avanzar_posicion
)

try:
    from ayudas import mostrar_ayudas
except Exception:
    def mostrar_ayudas(*args, **kwargs):
        print("mostrar_ayudas no disponible")


# -------------------- VARIABLES --------------------
preguntas = cargar_preguntas()
pregunta_actual = None
texto_pregunta = None
botones_opciones = []
resultado_texto = None
btn_salir = None
btn_ayuda = None

ultimo_valor_dado = 1

# Temporizador
temporizador_texto = None
tiempo_restante = 60


# -------------------- ACTUALIZAR VALOR DADO --------------------
def actualizar_valor_dado(valor):
    global ultimo_valor_dado
    try:
        ultimo_valor_dado = int(round(float(valor)))
    except:
        ultimo_valor_dado = 1
    print(f"\n🎲 VALOR DEL DADO RECIBIDO: {ultimo_valor_dado}")


# -------------------- TEMPORIZADOR --------------------
def actualizar_temporizador(btn_tirar):
    global tiempo_restante, temporizador_texto
    if tiempo_restante > 0:
        tiempo_restante -= 1
        if temporizador_texto:
            temporizador_texto.text = f"Tiempo: {tiempo_restante}s"
        invoke(actualizar_temporizador, btn_tirar, delay=1)
    else:
        print("⏰ ¡Tiempo agotado!")
        limpiar_pregunta(btn_tirar)


# -------------------- AYUDAS --------------------
def usar_50_50():
    if not pregunta_actual:
        return

    correcta = pregunta_actual["correcta"]
    incorrectos = [b for b in botones_opciones if b.letra != correcta]

    if len(incorrectos) >= 2:
        for b in random.sample(incorrectos, 2):
            b.disable()


def usar_llamar_amigo():
    if not pregunta_actual:
        return

    pista = random.choice([
        f"Creo que podría ser la {pregunta_actual['correcta']}",
        f"Yo elegiría la {pregunta_actual['correcta']}",
        "Mmm... no estoy seguro, pero suena lógico.",
        f"Diría que la correcta es la {pregunta_actual['correcta']}."
    ])

    Text(
        parent=camera.ui,
        text=f"📞 Amigo: {pista}",
        y=-0.6,
        scale=1,
        color=color.yellow,
        background=True,
        background_color=color.black,
        z=1
    )


def usar_cambiar_pregunta(turno, j1, j2, p1, p2, texto_turno, btn_tirar, mover):
    mostrar_pregunta(turno, j1, j2, p1, p2, texto_turno, btn_tirar, mover)


# ------------------------------------------
#            MOSTRAR PREGUNTA
# ------------------------------------------
def mostrar_pregunta(turno_j1, j1, j2, pos_j1, pos_j2,
                     texto_turno, btn_tirar, mover_a_casilla,
                     tablero=None):

    global pregunta_actual, texto_pregunta, botones_opciones
    global resultado_texto, btn_ayuda, btn_salir, temporizador_texto, tiempo_restante

    limpiar_pregunta(btn_tirar)

    btn_tirar.disable()
    if hasattr(btn_tirar, "visible"):
        btn_tirar.visible = False

    pregunta_actual = seleccionar_pregunta_aleatoria(preguntas)
    if not pregunta_actual:
        return pos_j1, pos_j2, turno_j1

    texto_pregunta = Text(
        parent=camera.ui,
        text=pregunta_actual["pregunta"],
        position=(0, 0.28),
        origin=(0, 0),
        scale=1.2,
        color=color.white,
        wordwrap=40,
        background=True,
        background_color=color.rgb(120, 90, 130),
        z=1
    )

    # TEMPORIZADOR
    tiempo_restante = 90
    temporizador_texto = Text(
        parent=camera.ui,
        text=f"Tiempo: {tiempo_restante}s",
        position=(0.5, 0.35),
        scale=1,
        color=color.white,
        background=True,
        background_color=color.black,
        z=1
    )
    actualizar_temporizador(btn_tirar)

    # -----------------------
    # CREAR BOTONES OPCIONES
    # -----------------------
    botones_opciones.clear()
    letras = ["A", "B", "C", "D"]
    posiciones = [
        Vec3(-0.5, 0.15, 1),
        Vec3(0.5, 0.15, 1),
        Vec3(-0.5, -0.05, 1),
        Vec3(0.5, -0.05, 1),
    ]

    # ⚫ COLOR NEGRO FORZADO (NO PUEDE SER SOBREESCRITO)
    NEGRO_FUERZA = color.rgba(0, 0, 0, 255)

    for i, opcion in enumerate(pregunta_actual["opciones"]):

        b = Button(
            parent=camera.ui,
            text=f"{letras[i]}. {opcion}",
            position=posiciones[i],
            scale=(0.9, 0.1),
            color=NEGRO_FUERZA,
            text_color=color.white,
            z=1
        )

        # 🚫 Proteger color para que NUNCA cambie a blanco
        b.colorize = False
        if hasattr(b, "model"):
            b.model.colorize = False
            b.model.color = NEGRO_FUERZA
            b.model.color32 = NEGRO_FUERZA

        b.default_color = NEGRO_FUERZA
        b.highlight_color = NEGRO_FUERZA
        b.pressed_color = NEGRO_FUERZA
        b.disabled_color = NEGRO_FUERZA

        b.mode = 'raw'  # 🔒 Protege totalmente el color

        b.letra = letras[i]
        b.on_click = lambda btn=b: responder(
            btn.letra, turno_j1,
            j1, j2,
            pos_j1, pos_j2,
            texto_turno, btn_tirar, mover_a_casilla,
            tablero
        )
        botones_opciones.append(b)

    # Botón ayudas
    btn_ayuda = Button(
        parent=camera.ui,
        text="Ayuda",
        position=Vec3(-0.3, -0.35, 1),
        scale=(0.3, 0.08),
        color=color.azure,
        text_color=color.black,
        z=1
    )
    btn_ayuda.on_click = lambda: mostrar_ayudas(
        usar_llamar_amigo,
        lambda: usar_cambiar_pregunta(turno_j1, j1, j2, pos_j1, pos_j2,
                                      texto_turno, btn_tirar, mover_a_casilla),
        usar_50_50,
        volver_callback=lambda: None
    )

    # Botón salir
    btn_salir = Button(
        parent=camera.ui,
        text="Salir",
        position=Vec3(0.3, -0.35, 1),
        scale=(0.3, 0.08),
        color=color.rgb(220, 0, 180),
        text_color=color.white,
        z=1
    )
    btn_salir.on_click = application.quit

    return pos_j1, pos_j2, turno_j1


# ------------------------------------------
#           RESPONDER PREGUNTA
# ------------------------------------------
from puntaje import sumar_puntaje_jugador

def responder(letra, turno_j1, j1, j2,
              pos_j1, pos_j2,
              texto_turno, btn_tirar, mover_a_casilla,
              tablero=None):

    global resultado_texto, ultimo_valor_dado, pregunta_actual

    correcta = pregunta_actual["correcta"]
    acierto = validar_respuesta(pregunta_actual, letra)

    for b in botones_opciones:
        if b.letra == correcta:
            b.color = color.green
        elif b.letra == letra:
            b.color = color.red

    if resultado_texto:
        resultado_texto.disable()

    resultado_texto = Text(
        parent=camera.ui,
        text="¡Correcto!" if acierto else "Incorrecto.",
        y=-0.45,
        scale=1,
        color=color.white,
        background=True,
        background_color=color.black,
        z=1
    )

    if acierto:
        if turno_j1:
            pos_j1 += ultimo_valor_dado
            mover_a_casilla(j1, pos_j1)

            if tablero is not None:
                p_total = sumar_puntaje_jugador(1, pos_j1)
                tablero.puntaje_j1 = p_total
                tablero.texto_puntaje_j1.text = f"Puntaje Jugador 1: {p_total}"

        else:
            pos_j2 += ultimo_valor_dado
            mover_a_casilla(j2, pos_j2)

            if tablero is not None:
                p_total = sumar_puntaje_jugador(2, pos_j2)
                tablero.puntaje_j2 = p_total
                tablero.texto_puntaje_j2.text = f"Puntaje Jugador 2: {p_total}"

    turno_j1 = not turno_j1
    texto_turno.text = "Turno: Jugador 1" if turno_j1 else "Turno: Jugador 2"

    invoke(limpiar_pregunta, btn_tirar, delay=2.5)

    return pos_j1, pos_j2, turno_j1


# ------------------------------------------
#           LIMPIAR PREGUNTA
# ------------------------------------------
def limpiar_pregunta(btn_tirar, limpiar_btn=True):
    global texto_pregunta, botones_opciones
    global resultado_texto, btn_ayuda, btn_salir, temporizador_texto

    if texto_pregunta:
        try: texto_pregunta.disable()
        except: pass

    for b in botones_opciones:
        try: b.disable()
        except: pass
    botones_opciones.clear()

    if resultado_texto:
        try: resultado_texto.disable()
        except: pass
        resultado_texto = None

    if btn_ayuda:
        try: btn_ayuda.disable()
        except: pass
        btn_ayuda = None

    if btn_salir:
        try: btn_salir.disable()
        except: pass
        btn_salir = None

    if temporizador_texto:
        try: temporizador_texto.disable()
        except: pass

    if limpiar_btn:
        try:
            btn_tirar.enable()
            if hasattr(btn_tirar, "visible"):
                btn_tirar.visible = True
        except:
            pass
