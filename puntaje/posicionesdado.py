from ursina import *

app = Ursina()

d = Entity(model='models/dado.glb', scale=50)

def input(key):
    if key == '1':
        d.rotation = (0, 0, 0)
        print("Cara 1 arriba:", d.rotation)
    if key == '2':
        d.rotation_x += 90
        print("Probando rotación:", d.rotation)
    if key == '3':
        d.rotation_x -= 90
        print("Probando rotación:", d.rotation)
    if key == '4':
        d.rotation_y += 90
        print("Probando rotación:", d.rotation)
    if key == '5':
        d.rotation_y -= 90
        print("Probando rotación:", d.rotation)
    if key == '6':
        d.rotation_z += 90
        print("Probando rotación:", d.rotation)

app.run()
