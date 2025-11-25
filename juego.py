# juego_completo.py
from ursina import *
from random import randint, choice

# ---------------------------
#  Clase Dado3D (simplificada)
# ---------------------------
class Dado3D(Entity):
    def __init__(self, position=(0,1,0), scale=0.6, **kwargs):
        super().__init__(
            model='cube',
            position=position,
            scale=scale,
            collider=None,
            **kwargs
        )
        # rotaciones simbólicas por cara (no hace falta exactitud)
        self.rotaciones = {
            1: Vec3(90, 90, 0),
            2: Vec3(90, 180, 0),
            3: Vec3(0, 180, 0),
            4: Vec3(0, 0, 0),
            5: Vec3(90, 0, 0),
            6: Vec3(90, -90, 0)
        }
        self.resultado_lanzado = None
        self.callback_externo = None
        self.texto_aviso = None

    def lanzar(self, callback=None):
        """Aniama (simple) y devuelve el número mediante callback."""
        self.callback_externo = callback
        resultado = randint(1,6)
        self.resultado_lanzado = resultado
        rot_final = self.rotaciones[resultado]

        print("\n=======================")
        print("🎲 DADO LANZADO")
        print(f"→ Número generado: {resultado}")
        print(f"→ Rotación final asignada: {rot_final}")
        print("=======================\n")

        self.animate_rotation(Vec3(self.rotation_x + 1080,
                                   self.rotation_y + 1080,
                                   self.rotation_z + 1080),
                              duration=0.8, curve=curve.linear)
        invoke(self.animate_rotation, rot_final, duration=0.4, curve=curve.out_expo, delay=0.8)

        def mostrar_aviso():
            if self.texto_aviso:
                destroy(self.texto_aviso)
            self.texto_aviso = Text(text=f"Resultado: {resultado}", scale=1.2, y=0.3, background=True, color=color.yellow)
            invoke(self.ocultar_aviso, delay=1.5)

        invoke(mostrar_aviso, delay=1.2)
        invoke(self._finish_roll, delay=1.3)
        return resultado

    def _finish_roll(self):
        valor = self.resultado_lanzado
        print("\n=======================")
        print("🎯 DADO FINALIZADO")
        print(f"→ Cara final: {valor}")
        print("→ Enviando valor al callback...")
        print("=======================\n")
        if self.callback_externo:
            self.callback_externo(valor)
        else:
            print("⚠ No hay callback asignado")

    def ocultar_aviso(self):
        if self.texto_aviso:
            destroy(self.texto_aviso)
            self.texto_aviso = None


# ---------------------------
#  Jugadores
# ---------------------------
class JugadorBase(Entity):
    def __init__(self, nombre, color_jugador, tablero, offset_x=0, offset_z=0, scale_tuple=(0.2,0.2,0.2)):
        super().__init__()
        self.nombre = nombre
        self.model = 'sphere'
        self.color = color_jugador
        self.scale = scale_tuple
        self.tablero = tablero
        self.pos_offset_x = offset_x
        self.pos_offset_z = offset_z
        self.posicion = 1
        # colocar en casilla 1
        self.mover_a_casilla(1)

    def mover_a_casilla(self, num):
        num = max(1, min(100, int(num)))
        self.posicion = num
        x, y, z = self.tablero.casilla_a_pos(num)
        # aplicar offset para no solaparse
        self.position = Vec3(x + self.pos_offset_x, 0.2, z + self.pos_offset_z)
        print(f"[{self.nombre}] mover_a_casilla -> casilla {num} -> pos {self.position}")

    def avanzar(self, pasos):
        pasos = int(pasos)
        print(f"[{self.nombre}] avanzar: pasos={pasos} desde casilla {self.posicion}")
        nueva = self.posicion + pasos
        if nueva > 100:
            nueva = 100
        self.mover_a_casilla(nueva)


class Jugador1(JugadorBase):
    def __init__(self, tablero):
        super().__init__('Jugador1', color.azure, tablero, offset_x=-0.18, offset_z=0, scale_tuple=(0.25,0.25,0.25))


class Jugador2(JugadorBase):
    def __init__(self, tablero):
        super().__init__('Jugador2', color.orange, tablero, offset_x=0.18, offset_z=0, scale_tuple=(0.2,0.2,0.2))


# ---------------------------
#  Tablero
# ---------------------------
class Tablero(Entity):
    def __init__(self, cell_size=0.5):
        super().__init__()
        self.cell_size = cell_size
        # tablero visual (puede ser solo un plano)
        self.model = Entity(model='quad', scale=(5,5), color=color.gray, rotation_x=90, y=0)
        # El origen de la cuadrícula se centra en el plano; casillas de 10x10
        # No necesita modelo 3D extra
    def casilla_a_pos(self, num):
        """Convierte número de 1..100 a coordenadas x,z (centro de casilla)"""
        num = max(1, min(100, int(num)))
        fila = (num - 1) // 10
        col = (num - 1) % 10
        if fila % 2 == 1:
            col = 9 - col
        offset = (self.cell_size * 9) / 2
        x = col * self.cell_size - offset
        z = fila * self.cell_size - offset
        return (x, 0, z)


# ---------------------------
#  Preguntas (muy simple)
# ---------------------------
PREGUNTAS = [
    {"pregunta":"¿Color de cielo en un día claro?", "opciones":["Verde","Azul","Rojo","Negro"], "correcta":"B"},
    {"pregunta":"2+2 = ?", "opciones":["3","4","5","6"], "correcta":"B"},
    {"pregunta":"La tierra es ...", "opciones":["plana","esférica","cúbica","triangular"], "correcta":"B"},
    {"pregunta":"¿Qué es agua?", "opciones":["Hidrógeno","Oxígeno","H2O","Nitrógeno"], "correcta":"C"},
]

def seleccionar_pregunta_aleatoria():
    return choice(PREGUNTAS)


# ---------------------------
#  Juego principal
# ---------------------------
class Juego(Ursina):
    def __init__(self):
        super().__init__(borderless=False)
        window.title = "Juego - mover según dado"
        Sky(color=color.light_gray)
        print("=== INICIANDO JUEGO ===")

        # tablero y jugadores
        self.tablero = Tablero(cell_size=0.5)
        self.j1 = Jugador1(self.tablero)
        self.j2 = Jugador2(self.tablero)

        # botón de tirar (usa el dado 3D)
        self.btn_dado = Button(text="🎲 Tirar dado", scale=(0.24,0.1), y=-0.45, color=color.azure, on_click=self.tirar_dado)
        self.texto = Text("", y=-0.32, scale=1.3)

        # estado
        self.turno = 1  # 1 o 2
        self.ultimo_valor_dado = None
        self.dado_entity = None

        print("✔ Juego listo. Haz click en 'Tirar dado'")

    def tirar_dado(self):
        # crear/usar dado
        if not self.dado_entity:
            self.dado_entity = Dado3D(position=(0,1.2,0), scale=0.5)
        # desactivar botón mientras procesa
        self.btn_dado.disable()
        self.texto.text = "Tirando..."
        # lanzar dado y pasar callback
        self.dado_entity.lanzar(callback=self._dado_termino)

    def _dado_termino(self, valor):
        # callback del dado: valor es 1..6
        self.ultimo_valor_dado = int(valor)
        self.texto.text = f"Salió: {valor} — mostrando pregunta..."
        print(f"[JUEGO] dado terminó con valor {valor} (turno jugador {self.turno})")

        # mostrar pregunta breve en UI; la pregunta manejará mover en caso de acierto
        self.mostrar_pregunta(lambda acierto: self._procesar_respuesta_pregunta(acierto))

    def mostrar_pregunta(self, callback_on_answer):
        """Muestra pregunta simple en pantalla; llama callback_on_answer(acierto:bool)"""
        pregunta = seleccionar_pregunta_aleatoria()
        # limpiar UI previa
        self.limpiar_pregunta_ui()

        # label pregunta
        self.ui_text_pregunta = Text(parent=camera.ui, text=pregunta["pregunta"], y=0.35, scale=1.2, background=True, background_color=color.black, color=color.white, wordwrap=40)

        # crear botones A..D
        letras = ["A","B","C","D"]
        posiciones = [Vec3(-0.5,0.15,1), Vec3(0.5,0.15,1), Vec3(-0.5,-0.05,1), Vec3(0.5,-0.05,1)]
        self.ui_botones = []
        for i, opcion in enumerate(pregunta["opciones"]):
            b = Button(parent=camera.ui, text=f"{letras[i]}. {opcion}", position=posiciones[i], scale=(0.9,0.1), color=color.azure, text_color=color.white)
            def make_onclick(letra):
                def onclick():
                    acierto = (letra == pregunta["correcta"])
                    # feedback visual
                    if acierto:
                        b.color = color.green
                    else:
                        b.color = color.red
                    # llamar callback externo
                    invoke(callback_on_answer, acierto, delay=0.3)
                return onclick
            b.on_click = make_onclick(letras[i])
            self.ui_botones.append(b)

    def limpiar_pregunta_ui(self):
        for n in ('ui_text_pregunta','ui_botones'):
            if hasattr(self, n):
                attr = getattr(self, n)
                if isinstance(attr, list):
                    for w in attr:
                        try: w.disable()
                        except: pass
                else:
                    try: attr.disable()
                    except: pass
        # limpieza simple: eliminar atributos para evitar reusar referencias
        if hasattr(self, 'ui_text_pregunta'): delattr = setattr(self, 'ui_text_pregunta', None)
        if hasattr(self, 'ui_botones'): delattr = setattr(self, 'ui_botones', None)

    def _procesar_respuesta_pregunta(self, acierto):
        """Callback al responder la pregunta. Si acierto: mover según ultimo_valor_dado"""
        print(f"[JUEGO] Resultado pregunta: {'acertó' if acierto else 'falló'}")
        # habilitar botón dado de nuevo al final del flujo
        def continuar():
            self.turno = 2 if self.turno == 1 else 1
            self.btn_dado.enable()
            self.texto.text = ""
            self.limpiar_pregunta_ui()

        if acierto:
            pasos = self.ultimo_valor_dado or 1
            jugador = self.j1 if self.turno == 1 else self.j2
            print(f"[JUEGO] Moviendo {jugador.nombre} {pasos} casillas (valor dado)")
            jugador.avanzar(pasos)
            invoke(continuar, delay=0.2)
        else:
            # no avanza; sólo limpiar y pasar turno
            invoke(continuar, delay=0.6)


# -------------------------------------------------------
#  Ejecutar
# -------------------------------------------------------
if __name__ == '__main__':
    juego = Juego()
    juego.run()
