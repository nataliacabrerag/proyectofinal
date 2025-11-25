from ursina import Entity, invoke

# ============================================================
#  jugador.py - mueve paso a paso según valor del dado
# ============================================================

class JugadorBase(Entity):
    def __init__(self, modelo, tablero, escala_tuple, pos_offset, rot, **kwargs):
        super().__init__(**kwargs)

        # escala y offsets
        self.scale = escala_tuple
        self.pos_x, self.pos_y, self.pos_z = pos_offset
        self.rot_x, self.rot_y, self.rot_z = rot

        self.model = modelo
        self.rotation = (self.rot_x, self.rot_y, self.rot_z)

        # referencia al tablero y casilla actual (1..100)
        self.tablero = tablero
        self.posicion = 1
        self.posicion_inicial = 1

        # bandera para evitar movimientos concurrentes
        self._moving = False

        # colocar en la casilla 1 con offsets (sin animación)
        self._colocar_en_casilla(1)

    def _colocar_en_casilla(self, num):
        x, y, z = self.tablero.casilla_a_pos(num)
        self.x = x + self.pos_x
        self.y = self.pos_y
        self.z = z + self.pos_z
        self.posicion = int(max(1, min(100, int(num))))

    def mover_a_casilla(self, num, step_delay=0.14):
        """
        Mueve paso a paso desde la casilla actual hasta 'num'.
        Si cae 6 en el dado se harán 6 movimientos (uno por casilla).
        """
        try:
            num = int(num)
        except:
            return
        num = max(1, min(100, num))

        inicio = int(self.posicion)
        if inicio == num:
            return

        # Evitar superponer movimientos
        if self._moving:
            return
        self._moving = True

        pasos = abs(num - inicio)
        direccion = 1 if num > inicio else -1

        def mover_directo(casilla, es_ultimo):
            x, y, z = self.tablero.casilla_a_pos(casilla)
            self.x = x + self.pos_x
            self.y = self.pos_y
            self.z = z + self.pos_z
            self.posicion = casilla
            if es_ultimo:
                self._moving = False

        # programar cada casilla con un pequeño delay para que se vea el paso a paso
        for i in range(1, pasos + 1):
            casilla_obj = inicio + direccion * i
            es_ultimo = (i == pasos)
            delay = step_delay * (i - 1)
            invoke(mover_directo, casilla_obj, es_ultimo, delay=delay)

    def avanzar(self, pasos):
        """
        Avanza 'pasos' desde la casilla actual (llamado por el tablero).
        """
        try:
            pasos = int(pasos)
        except:
            pasos = 0
        nueva = self.posicion + pasos
        nueva = max(1, min(100, nueva))
        self.posicion_inicial = self.posicion
        self.mover_a_casilla(nueva)

    def regresar_a_posicion_inicial(self):
        self.mover_a_casilla(self.posicion_inicial)


class Jugador1(JugadorBase):
    def __init__(self, modelo, tablero, **kwargs):
        super().__init__(
            modelo=modelo,
            tablero=tablero,
            escala_tuple=(0.05, 0.05, 0.05),
            pos_offset=(1.5, 0.35, 2.9),
            rot=(270, 0, 0),
            **kwargs
        )


class Jugador2(JugadorBase):
    def __init__(self, modelo, tablero, **kwargs):
        super().__init__(
            modelo=modelo,
            tablero=tablero,
            escala_tuple=(0.017, 0.017, 0.017),
            pos_offset=(2, 1.5, 3),
            rot=(0, 180, 0),
            **kwargs
        )