from ursina import *

# -------------------- ESTADO DE USOS --------------------
usos = {
    "50": False,
    "llamar": False,
    "cambiar": False
}

def mostrar_ayudas(func_llamar, func_cambiar, func_50, volver_callback):

    # CAPA OSCURA SEMITRANSPARENTE DE FONDO
    capa_fondo = Entity(
        parent=camera.ui,
        model='quad',
        scale=(2, 2),
        color=color.rgba(10, 10, 40, 180),   # ⭐ Fondo estilo millonario
        z=-1
    )

    # CUADRO PRINCIPAL (AZUL OSCURO)
    fondo = Entity(
        parent=capa_fondo,
        model='quad',
        scale=(1.2, 1.2),
        color=color.rgb(20, 30, 80),         # ⭐ Cuadro azul elegante
        z=-2
    )

    # BORDE DORADO
    borde = Entity(
        parent=fondo,
        model='quad',
        scale=1.05,
        color=color.rgb(200, 160, 20),       # ⭐ Dorado
        z=-3
    )

    # TÍTULO
    titulo = Text(
        "AYUDAS",
        parent=fondo,
        y=0.35,
        scale=1.6,
        color=color.rgb(255, 215, 0),        # ⭐ Dorado
        z=-4
    )

    # separación de botones
    separacion = 0.13

    # ------------- BOTONES -------------
    texto_50 = "50 / 50" + (" (USADA)" if usos["50"] else "")
    btn_50 = Button(
        parent=fondo,
        text=texto_50,
        scale=(0.35, 0.075),
        color=color.rgb(30/255, 70/255, 180/255),       # ⭐ Azul intenso
        text_color=color.white,
        y=0.15,
        z=-5
    )
    btn_50.on_click = lambda: ejecutar(fondo, capa_fondo, "50", func_50)

    texto_llamar = "Llamar Amigo" + (" (USADA)" if usos["llamar"] else "")
    btn_llamar = Button(
        parent=fondo,
        text=texto_llamar,
        scale=(0.35, 0.075),
        color=color.rgb(150/255, 210/255, 1),      # ⭐ Amarillo oro
        text_color=color.black,
        y=0.15 - separacion,
        z=-5
    )
    btn_llamar.on_click = lambda: ejecutar(fondo, capa_fondo, "llamar", func_llamar)

    texto_cambiar = "Cambiar Pregunta" + (" (USADA)" if usos["cambiar"] else "")
    btn_cambiar = Button(
        parent=fondo,
        text=texto_cambiar,
        scale=(0.35, 0.075),
        color=color.rgb(1, 0, 150/255),        # ⭐ Verde suave
        text_color=color.white,
        y=0.15 - separacion * 2,
        z=-5
    )
    btn_cambiar.on_click = lambda: ejecutar(fondo, capa_fondo, "cambiar", func_cambiar)

    btn_volver = Button(
        parent=fondo,
        text="Cerrar",
        scale=(0.35, 0.075),
        color=color.rgb(150, 70, 150),        # ⭐ Rojo oscuro
        text_color=color.white,
        y=0.15 - separacion * 3,
        z=-5
    )
    btn_volver.on_click = lambda: cerrar(fondo, capa_fondo, volver_callback)


# -------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------
def ejecutar(fondo, capa, tipo, funcion):
    if usos[tipo]:
        print("❌ Ya usaste esta ayuda.")
        return
    usos[tipo] = True
    fondo.disable()
    capa.disable()
    funcion()

def cerrar(fondo, capa, callback):
    fondo.disable()
    capa.disable()
    callback()

