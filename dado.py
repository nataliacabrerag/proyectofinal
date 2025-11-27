from ursina import *
from random import randint

class Dado3D(Entity):

    def __init__(self, position=(0, 1, 0), scale=100, **kwargs):
        super().__init__(
            model="models/dado.glb",
            position=position,
            scale=scale,
            collider=None,
            **kwargs
        )

        # → tus rotaciones EXACTAS, no las cambio
        self.rotaciones = {
            1: Vec3(90, 90, 0),
            2: Vec3(90, 180, 0),
            3: Vec3(0, 180, 0),
            4: Vec3(0, 0, 0),
            5: Vec3(90, 0, 0),
            6: Vec3(90, -90, 0)
        }

        self.resultado_lanzado = None
        self.texto_aviso = None
        self.callback_externo = None


    def lanzar(self, callback=None):

        # guardamos el callback del tablero
        self.callback_externo = callback

        # escogemos el número que queremos mostrar
        resultado = randint(1, 6)
        self.resultado_lanzado = resultado
        rot_final = self.rotaciones[resultado]

        print("\n=======================")
        print("🎲 DADO LANZADO")
        print(f"→ Número generado: {resultado}")
        print(f"→ Rotación final asignada: {rot_final}")
        print("=======================\n")

        # animación loca inicial
        self.animate_rotation(
            Vec3(self.rotation_x + 1080,
                 self.rotation_y + 1080,
                 self.rotation_z + 1080),
            duration=4,
            curve=curve.linear
        )

        # animación final exacta
        invoke(
            self.animate_rotation,
            rot_final,
            duration=1.5,
            curve=curve.out_expo,
            delay=4
        )

        # mostrar mensaje en pantalla
        def mostrar_aviso():
            self.texto_aviso = Text(
                text=f"Resultado: {resultado}",
                scale=1.5,
                origin=(0, 0),
                y=.3,
                background=True,
                color=color.yellow
            )
            invoke(self.ocultar_aviso, delay=1)

        invoke(mostrar_aviso, delay=5.2)

        # procesar turno DESPUÉS de que el dado cae
        invoke(self._finish_roll, delay=5.2)

        return resultado


    def _finish_roll(self):
        """Esto garantiza que el valor 100% final del dado
        es lo que se envía al tablero."""
        
        valor = self.resultado_lanzado

        print("\n=======================")
        print("🎯 DADO FINALIZADO")
        print(f"→ Cara final: {valor}")
        print(f"→ Rotación final real del modelo: {self.rotation}")
        print("→ Enviando valor al callback...")
        print("=======================\n")

        # llamar al callback del tablero
        if self.callback_externo:
            self.callback_externo(valor)
        else:
            print("⚠ ERROR: NO hay callback asignado")


    def ocultar_aviso(self):
        if self.texto_aviso:
            destroy(self.texto_aviso)
            self.texto_aviso = None
