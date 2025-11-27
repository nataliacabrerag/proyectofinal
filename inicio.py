from ursina import *

import sys
import subprocess
import os
from pathlib import Path


app = Ursina()

# --- CONFIGURACIÓN DE LA VENTANA ---
window.fullscreen = False
window.borderless = False
window.title = 'Juego de Estructuras'
camera.orthographic = True
camera.fov = 9




# --- FONDO QUE OCUPA TODA LA PANTALLA ---
def ajustar_fondo():
    aspecto = window.aspect_ratio
    fondo.scale = (aspecto * 9, 9)

fondo = Entity(model='quad', texture='inicio.png')
ajustar_fondo()
window.on_resize = ajustar_fondo

# --- FUNCIONES PARA CADA BOTÓN ---
def abrir_tablero():
    print(" Iniciando el tablero 3D...")
    ruta_tablero = os.path.join(os.getcwd(), "tablero.py")
    if os.path.exists(ruta_tablero):
        subprocess.Popen([sys.executable, ruta_tablero])
        app.userExit()
    else:
        print(" No se encontró 'tablero.py'.")

def abrir_creditos():
    print(" Mostrando créditos...")
    ruta_cred = os.path.join(os.getcwd(), "creditos.py")
    if os.path.exists(ruta_cred):
        subprocess.Popen([sys.executable, ruta_cred])
        app.userExit()
    else:
        print(" Archivo 'creditos.py' no encontrado.")

def salir():
    print(" Cerrando el juego...")
    app.userExit()

# --- TEXTO DEBUG ---
texto_debug = Text(position=(-0.87, 0.45), color=color.yellow, scale=1.5)
def update():
    texto_debug.text = f"x={mouse.x:.2f}, y={mouse.y:.2f}"

# --- ABRIR INSTRUCCIONES ---
def abrir_instrucciones():
    print(" Mostrando instrucciones...")

    carpeta_instrucciones = Path("images")

    nombres = [
        "instrucciones1.png",
        "instrucciones2.png",
        "instrucciones3.png",
        "instrucciones4.png",
        "instrucciones5.png",
        "instrucciones6.png",
    ]

    disponibles = []
    for nombre in nombres:
        ruta = carpeta_instrucciones / nombre
        if ruta.exists():
            try:
                tex = load_texture(str(ruta))
                if tex:
                    disponibles.append(tex)
                    print(f" Cargada: {ruta.name}")
                else:
                    print(f" No se pudo cargar textura de {ruta.name}")
            except Exception as e:
                print(f" Error cargando {ruta.name}: {e}")
        else:
            print(f"No existe: {ruta.name}")

    if not disponibles:
        print(f" No se encontraron imágenes válidas en {carpeta_instrucciones}")
        return

    previous_app_input = app.input
    fondo.disable()

    indice = 0

    fondo_instrucciones = Entity(
        parent=camera.ui,
        model='quad',
        texture=disponibles[indice],
        scale=(window.aspect_ratio * 1.6, 1.0),
        y=0
    )

    texto_aviso = Text(
        "Haz clic en la pantalla o usa los botones →",
        parent=camera.ui,
        y=-0.38,
        origin=(0, 0),
        color=color.white,
        scale=0.6
    )

    btn_siguiente = Button(
        parent=camera.ui,
        text="Siguiente",
        scale=(0.18, 0.09),
        x=0.45,
        y=-0.38
    )
    btn_fin = Button(
        parent=camera.ui,
        text="Fin",
        scale=(0.12, 0.09),
        x=0.65,
        y=-0.38,
        color=color.azure
    )

    def siguiente_instruccion():
        nonlocal indice
        indice += 1
        if indice < len(disponibles):
            fondo_instrucciones.texture = disponibles[indice]
        else:
            cerrar_instrucciones()

    def cerrar_instrucciones():
        fondo_instrucciones.disable()
        texto_aviso.disable()
        btn_siguiente.disable()
        btn_fin.disable()
        fondo.enable()
        app.input = previous_app_input
        print(" Instrucciones finalizadas. Volviendo al menú...")

    btn_siguiente.on_click = lambda: siguiente_instruccion()
    btn_fin.on_click = lambda: cerrar_instrucciones()

    def input_instrucciones(key):
        if key == 'left mouse down':
            siguiente_instruccion()
        elif key == 'escape':
            cerrar_instrucciones()

    app.input = input_instrucciones

# --- DETECCIÓN DE CLICS EN EL MENÚ PRINCIPAL ---
def input(key):
    if key == 'left mouse down':
        x = mouse.position.x
        y = mouse.position.y
        print(f"Clic en: x={x:.2f}, y={y:.2f}")

        # EMPEZAR
        if -0.1 < x < 0.2 and 0.0 < y < 0.1:
            abrir_tablero()
            return

        # INSTRUCCIONES
        if 0.11 < x < 0.40 and -0.15 < y < -0.05:
            abrir_instrucciones()
            return

        # CRÉDITOS
        if -0.1 < x < 0.2 and -0.2 < y < -0.1:
            abrir_creditos()
            return

        # SALIR
        if -0.1 < x < 0.2 and -0.3 < y < -0.2:
            salir()
            return

        print("Clic fuera de los botones.")

    if key == 'escape':
        salir()

app.run()