# tablero.py — CORREGIDO: dado negativo aplicado correctamente, tienda de trampas añadida en esquina inferior derecha
from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from jugador import Jugador1, Jugador2
from dado import Dado3D
import importlib
import traceback
from trampa import abrir_tienda_trampas
import puntaje  # <-- agregado: módulo fuente de la verdad para los puntajes


CELL_SIZE = 0.93
MOVIMIENTO_MULTIPLIER = 2.5
INTENTOS_MODULOS = ["preguntas"]

mostrar_pregunta = None
errores_import = []
for modname in INTENTOS_MODULOS:
    try:
        mod = importlib.import_module(modname)
        if hasattr(mod, "mostrar_pregunta"):
            mostrar_pregunta = getattr(mod, "mostrar_pregunta")
            modulo_ok = modname
            break
        for attr in dir(mod):
            if attr.lower() == "mostrar_pregunta":
                mostrar_pregunta = getattr(mod, attr)
                modulo_ok = modname
                break
        if mostrar_pregunta:
            break
    except Exception as e:
        errores_import.append((modname, str(e)))

if mostrar_pregunta is None:
    def mostrar_pregunta(turno, j1, j2, p1, p2, texto_turno, boton_dado, mover_confirmado, tablero=None):
        print("STUB mostrar_pregunta: confirmando movimiento automáticamente.")
        jugador_entity = j1 if turno else j2
        mover_confirmado(jugador_entity)
        return p1, p2, True


class Tablero(Entity):
    def __init__(self):

        super().__init__()
        print("Cargando tablero...")

        self.modelo = Entity(
            model="models/tablero.obj",
            texture="models/tablero.png",
            scale=0.1,
            rotation_x=270,
            rotation_y=180,
        )

        DirectionalLight(y=2, z=3)
        AmbientLight(color=color.rgba(120, 120, 120, 255))

        camera.position = (0, 5, -18)
        camera.rotation_x = 55
        EditorCamera()

        print("Cargando jugadores...")
        self.jugador1 = Jugador1(modelo="models/jugador1.obj", tablero=self)
        self.jugador2 = Jugador2(modelo="models/jugador2.obj", tablero=self)
        print(f"Jugadores colocados: id1={id(self.jugador1)}, id2={id(self.jugador2)}")

        # ---------------------------------------------------------
        # Asegurar atributos de trampas en los objetos jugador
        # (si el jugador ya los tiene, no los sobreescribimos)
        # ---------------------------------------------------------
        for p in (self.jugador1, self.jugador2):
            if not hasattr(p, "bloqueado"):
                p.bloqueado = False
            if not hasattr(p, "sql_inyeccion"):
                p.sql_inyeccion = False
            if not hasattr(p, "dado_negativo"):
                p.dado_negativo = False
            if not hasattr(p, "phishing"):
                p.phishing = False
            if not hasattr(p, "turbo"):
                p.turbo = False
            if not hasattr(p, "inmunidad"):
                p.inmunidad = False    # "corta fuegos" → inmunidad una trampa
            if not hasattr(p, "puntaje_congelado"):
                p.puntaje_congelado = False
            if not hasattr(p, "ayuda"):
                p.ayuda = None
            # asegurar posicion (si jugador ya maneja esto en su clase, no lo tocamos)
            if not hasattr(p, "posicion"):
                p.posicion = 1
            # método auxiliar para actualizar posición en caso de que no exista
            if not hasattr(p, "actualizar_posicion"):
                def _actualizar_posicion_local(self_obj=p):
                    try:
                        # si existe mover_a_casilla la usamos
                        if hasattr(self_obj, "mover_a_casilla"):
                            self_obj.mover_a_casilla(self_obj.posicion)
                        else:
                            # intentar setear position directamente (fallback)
                            x, y, z = self.casilla_a_pos(self_obj.posicion) if hasattr(self, "casilla_a_pos") else (0, 0, 0)
                            self_obj.position = Vec3(x, 0.2, z)
                    except Exception:
                        pass
                p.actualizar_posicion = _actualizar_posicion_local

        self.pos_j1 = 1
        self.pos_j2 = 1
        self.turno_jugador1 = True
        self.pending_move = None
        self.roll_count = 0
        self.current_roll_player = None

        self.texto_turno = Text(parent=camera.ui, text="Turno: Jugador 1", y=.45, origin=(0,0), scale=1.2,
                                background=True, background_color=color.black)

        self.boton_dado = Button(parent=camera.ui, text="TIRAR DADO", scale=0.15,
                                 color=color.azure, y=-0.45, on_click=self.lanzar_dado)

        # ----------------------------
        # BOTÓN TIENDA TRAMPAS EN ESQUINA INFERIOR DERECHA
        # ----------------------------
        self.boton_tienda = Button(
            parent=camera.ui,
            text="TIENDA TRAMPAS",
            scale=0.15,
            color=color.orange,
            x=0.75,
            y=-0.45,
            on_click=self.abrir_tienda_trampas
        )

        # PUNTAJES (mantengo atributos para compatibilidad UI, pero la fuente real es puntaje.puntaje_jugador*)
        self.puntaje_j1 = 0
        self.puntaje_j2 = 0

        self.texto_puntaje_j1 = Text(
            parent=camera.ui,
            text=f"Puntaje Jugador 1: {self.puntaje_j1}",
            origin=(-1, 0.5),
            x=-0.87,
            y=0.47,
            scale=1.0,
            background=True,
            background_color=color.rgba(0,0,0,150)
        )

        self.texto_puntaje_j2 = Text(
            parent=camera.ui,
            text=f"Puntaje Jugador 2: {self.puntaje_j2}",
            origin=(-1, 1.5),
            x=-0.87,
            y=0.40,
            scale=1.0,
            background=True,
            background_color=color.rgba(0,0,0,150)
        )

        self.dado = None
        self._pos_cache = {}

        # ---------------------------------------------------
        # TEXTO DE AVISO (AGREGADO PARA FIREWALL)
        # ---------------------------------------------------
        self.texto_aviso = Text(
            parent=camera.ui,
            text="",
            y=0.25,
            scale=1.2,
            color=color.red,
            background=True,
            background_color=color.rgba(0, 0, 0, 180),
        )
        self.texto_aviso.enabled = False

        # Asegurarnos de iniciar la UI sincronizada con puntaje.py
        self.actualizar_puntaje_ui()

        try:
            self.mover_a_casilla(self.jugador1, self.pos_j1)
            self.mover_a_casilla(self.jugador2, self.pos_j2)
        except Exception as e:
            print("Error inicial mover_a_casilla:", e)

    # -------------------------------------------------------
    # Método agregado: sincronizar UI con puntaje.py
    # -------------------------------------------------------
    def actualizar_puntaje_ui(self):
        """
        Sincroniza self.puntaje_j1/2 y los textos con los valores reales en puntaje.py.
        Llamar esto siempre que quieras forzar la UI a reflejar la 'fuente de la verdad'.
        """
        try:
            # obtener puntajes reales desde el módulo puntaje
            self.puntaje_j1 = int(getattr(puntaje, "puntaje_jugador1", 0))
            self.puntaje_j2 = int(getattr(puntaje, "puntaje_jugador2", 0))

            # actualizar textos (si existen)
            if hasattr(self, "texto_puntaje_j1") and self.texto_puntaje_j1:
                self.texto_puntaje_j1.text = f"Puntaje Jugador 1: {self.puntaje_j1}"
            if hasattr(self, "texto_puntaje_j2") and self.texto_puntaje_j2:
                self.texto_puntaje_j2.text = f"Puntaje Jugador 2: {self.puntaje_j2}"
        except Exception as e:
            print("Error actualizar_puntaje_ui:", e)

    # ======================================================
    # ----- LÓGICA DEL DADO -----
    # ======================================================
    def lanzar_dado(self):
        print("Lanzando dado...")

        # ---------------------------------------------------
        # FIREWALL: si el jugador está bloqueado, pierde turno
        # ---------------------------------------------------
        jugador_actual = self.jugador1 if self.turno_jugador1 else self.jugador2

        if getattr(jugador_actual, "bloqueado", False):
            # Si el jugador tiene INMUNIDAD, consumimos inmunidad en lugar de hacerle perder el turno
            if getattr(jugador_actual, "inmunidad", False):
                jugador_actual.inmunidad = False
                jugador_actual.bloqueado = False
                print("[INMUNIDAD] Cortafuegos consumido — se anuló el bloqueo")
                self.texto_aviso.text = "Tu cortafuegos anuló la trampa"
                self.texto_aviso.enabled = True
                invoke(lambda: setattr(self.texto_aviso, "enabled", False), delay=2)
            else:
                jugador_actual.bloqueado = False  # consumir firewall

                # mensaje en pantalla
                self.texto_aviso.text = "No puedes tirar el dado este turno (FIREWALL)"
                self.texto_aviso.enabled = True

                # ocultar después de 2 segundos
                invoke(lambda: setattr(self.texto_aviso, "enabled", False), delay=2)

                # pasar turno
                self.turno_jugador1 = not self.turno_jugador1
                self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"

                # reactivar botón
                self.boton_dado.enabled = True
                return

        if self.dado is None:
            self.dado = Dado3D(position=(0,1,0), scale=50)

        self.boton_dado.disable()
        self.roll_count += 1
        self.current_roll_player = 1 if self.turno_jugador1 else 2

        self.dado.lanzar(callback=self.despues_del_dado)

    def despues_del_dado(self, numero):
        try:
            numero = int(round(float(numero)))
        except:
            numero = 1

        if self.current_roll_player is None:
            self.current_roll_player = 1 if self.turno_jugador1 else 2

        player_idx = self.current_roll_player
        current_pos = self.pos_j1 if player_idx == 1 else self.pos_j2
        jugador_entity = self.jugador1 if player_idx == 1 else self.jugador2
        rival_entity = self.jugador2 if player_idx == 1 else self.jugador1

        # =========================
        # Aplicar trampas activas
        # =========================

        # SQL Injection (ya existente)
        if getattr(jugador_entity, "sql_inyeccion", False):
            numero += 1
            jugador_entity.sql_inyeccion = False
            print(f"[SQL Injection] Jugador {player_idx} avanza 1 casilla extra.")

        # -------------------------------------------------
        # PHISHING si se marca como flag (por compatibilidad)
        # (Algunas versiones de trampa.py ya roban inmediatamente; si se dejó como flag,
        #  lo procesamos aquí por seguridad)
        # -------------------------------------------------
        if getattr(jugador_entity, "phishing", False):
            print(f"[PHISHING] Jugador {player_idx} activa phishing: robo de 500 puntos")
            jugador_entity.phishing = False

            if player_idx == 1:
                robados = min(500, puntaje.puntaje_jugador2)
                puntaje.puntaje_jugador2 -= robados
                puntaje.puntaje_jugador1 += robados
            else:
                robados = min(500, puntaje.puntaje_jugador1)
                puntaje.puntaje_jugador1 -= robados
                puntaje.puntaje_jugador2 += robados

            print(f"[PHISHING] Robados: {robados} pts | J1={puntaje.puntaje_jugador1} | J2={puntaje.puntaje_jugador2}")

            try:
                self.actualizar_puntaje_ui()
            except:
                pass

        # -------------------------------------------------
        # TURBO: duplica la tirada (flag aplicada previamente)
        # -------------------------------------------------
        if getattr(jugador_entity, "turbo", False):
            jugador_entity.turbo = False
            numero = numero * 2
            print(f"[TURBO] Jugador {player_idx} duplica tirada → nuevo número: {numero}")

        # -------------------------------------------------
        # Dado Negativo: si el **rival** tiene activo dado_negativo
        # Si el rival tiene INMUNIDAD (cortafuegos), anulamos el efecto.
        # -------------------------------------------------
        if getattr(rival_entity, "dado_negativo", False):
            # si rival tiene inmunidad, se protege
            if getattr(rival_entity, "inmunidad", False):
                print(f"[INMUNIDAD] Rival protegida del Dado Negativo (Jugador {player_idx})")
                rival_entity.dado_negativo = False
                rival_entity.inmunidad = False
            else:
                destino = current_pos - numero
                if destino < 1:
                    destino = 1
                print(f"[Dado Negativo] Jugador {player_idx} retrocede {numero} → {destino}")
                rival_entity.dado_negativo = False
                # ajustar destino para el jugador actual (retroceder)
                self.pending_move = {"player": player_idx, "steps": -numero, "dest": int(destino)}
                invoke(self._hacer_pregunta, self.turno_jugador1, delay=0.8)
                return
        else:
            destino = current_pos + numero
            if destino > 100:
                destino = 100

        # Si llegamos aquí, no hubo dado_negativo que ya retornó
        try:
            import preguntas
            if hasattr(preguntas, "actualizar_valor_dado"):
                preguntas.actualizar_valor_dado(numero)
        except:
            pass

        self.pending_move = {"player": player_idx, "steps": numero, "dest": int(destino)}
        invoke(self._hacer_pregunta, self.turno_jugador1, delay=0.8)

    def _hacer_pregunta(self, turno_bool):
        moved_flag = {"called": False}

        def mover_confirmado(jugador_entity, nueva_pos=None, retroceder=False):
            moved_flag["called"] = True

            if jugador_entity is self.jugador1:
                idx = 1
            elif jugador_entity is self.jugador2:
                idx = 2
            else:
                return

            if nueva_pos is None:
                if not self.pending_move or self.pending_move.get("player") != idx:
                    return
                destino = int(self.pending_move.get("dest"))
            else:
                destino = max(1, min(100, int(nueva_pos)))

            try:
                jugador_entity.mover_a_casilla(destino)
            except:
                x, y, z = self.casilla_a_pos(destino)
                jugador_entity.position = Vec3(x, 0.2, z)
                jugador_entity.posicion = destino

            if idx == 1:
                self.pos_j1 = destino
            else:
                self.pos_j2 = destino

            self.pending_move = None
            self.boton_dado.enable()

            # -------------------------------------------------------
            # Sincronizar UI de puntajes con el módulo puntaje.py
            # Esto evita que la UI deje de mostrar acumulaciones
            # si otras partes del código (ej: preguntas, trampa) modifican puntaje.puntaje_jugador*
            # -------------------------------------------------------
            try:
                # Si el jugador tenía "puntaje_congelado" (Ransomware), informamos y consumimos la bandera.
                if getattr(jugador_entity, "puntaje_congelado", False):
                    print(f"[RANSOMWARE] Jugador {idx} tiene puntaje congelado: no sumará este turno.")
                    jugador_entity.puntaje_congelado = False
                    # Nota: la lógica exacta para "congelar" la suma de puntos ocurre en el módulo de preguntas/puntaje.
                    # Aquí lo notificamos y consumimos la bandera para que no se repita.
                    # Si necesitas bloquear la función puntaje.sumar_puntaje_jugador directamente,
                    # hay que instrumentar ese módulo para comprobar esta bandera.
                self.actualizar_puntaje_ui()
            except Exception as e:
                print("Error actualizando puntaje UI en mover_confirmado:", e)

        try:
            result = mostrar_pregunta(
                turno_bool, self.jugador1, self.jugador2,
                self.pos_j1, self.pos_j2, self.texto_turno, self.boton_dado,
                mover_confirmado, tablero=self
            )
            if result is None:
                nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True
            else:
                nuevo_p1, nuevo_p2, cambiar_turno = result
        except:
            nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True

        self.pos_j1 = int(nuevo_p1)
        self.pos_j2 = int(nuevo_p2)

        try:
            self.mover_a_casilla(self.jugador1, self.pos_j1)
            self.mover_a_casilla(self.jugador2, self.pos_j2)
        except:
            pass

        self.turno_jugador1 = not turno_bool
        self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"
        self.current_roll_player = None

        # También sincronizamos puntaje aquí por si algún flujo saltó mover_confirmado
        try:
            self.actualizar_puntaje_ui()
        except Exception as e:
            print("Error actualizando puntaje UI al final de _hacer_pregunta:", e)

    def mover_a_casilla(self, jugador, nueva_pos):
        try:
            nueva_pos = int(nueva_pos)
        except:
            nueva_pos = 1
        nueva_pos = max(1, min(100, nueva_pos))

        if hasattr(jugador, "mover_a_casilla"):
            try:
                jugador.mover_a_casilla(nueva_pos)
            except:
                x, y, z = self.casilla_a_pos(nueva_pos)
                jugador.position = Vec3(x, 0.2, z)
                jugador.posicion = nueva_pos
        else:
            x, y, z = self.casilla_a_pos(nueva_pos)
            jugador.position = Vec3(x, 0.2, z)
            jugador.posicion = nueva_pos

        if jugador is self.jugador1:
            self.pos_j1 = nueva_pos
        elif jugador is self.jugador2:
            self.pos_j2 = nueva_pos

    def casilla_a_pos(self, num):
        num = max(1, min(100, int(num)))
        fila = (num - 1) // 10
        col = (num - 1) % 10
        if fila % 2 == 1:
            col = 9 - col
        offset = (CELL_SIZE * 9) / 2
        x = col * CELL_SIZE - offset
        z = fila * CELL_SIZE - offset

        x += (x * (MOVIMIENTO_MULTIPLIER - 1))
        z += (z * (MOVIMIENTO_MULTIPLIER - 1))
        return (x, 0, z)

    # ======================================================
    # ----- ABRIR TIENDA TRAMPAS -----
    # ======================================================
    def abrir_tienda_trampas(self):
        jugador_actual = 1 if self.turno_jugador1 else 2
        abrir_tienda_trampas(self, jugador_actual)


if __name__ == "__main__":
    print("=== Iniciando juego ===")
    app = Ursina()
    Sky(color=color.gray)
    Tablero()
    app.run()
