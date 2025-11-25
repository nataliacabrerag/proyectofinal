from ursina import *

app = Ursina()

dado = Entity(
    model='models/dado.glb',
    scale=50,
    rotation=(0,0,0)
)

Text("Usa las teclas para rotar:\n"
     "W/S = Rotar X\n"
     "A/D = Rotar Y\n"
     "Q/E = Rotar Z\n"
     "ESPACIO = imprimir rotación actual",
     origin=(0,0),
     scale=1.2,
     y=.4
)

def input(key):
    if key == 'w':
        dado.rotation_x += 10
    if key == 's':
        dado.rotation_x -= 10

    if key == 'a':
        dado.rotation_y += 10
    if key == 'd':
        dado.rotation_y -= 10

    if key == 'q':
        dado.rotation_z += 10
    if key == 'e':
        dado.rotation_z -= 10

    if key == 'space':
        print("\n>>> Rotación actual:", dado.rotation)

app.run()
