# tablero.py — CORREGIDO: dado negativo retrocede el valor exacto del dado
from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from jugador import Jugador1, Jugador2
from dado import Dado3D
import importlib
import traceback

# Importar la tienda (asegúrate de tener trampa.py en el mismo directorio)
try:
    from trampa import abrir_tienda_trampas
except Exception:
    def abrir_tienda_trampas(tablero, jugador_actual):
        print("[aviso] abrir_tienda_trampas no encontrada. Instala trampa.py")

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

        # -------------------------
        # BOTÓN PARA ABRIR TIENDA (llama a trampa.abrir_tienda_trampas)
        # -------------------------
        self.boton_tienda = Button(
            parent=camera.ui,
            text="TIENDA",
            scale=0.10,
            color=color.gold,
            y=-0.28,
            on_click=lambda: abrir_tienda_trampas(self, 1 if self.turno_jugador1 else 2)
        )

        # PUNTAJES
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

        try:
            self.mover_a_casilla(self.jugador1, self.pos_j1)
            self.mover_a_casilla(self.jugador2, self.pos_j2)
        except Exception as e:
            print("Error inicial mover_a_casilla:", e)

    # -------------------------
    # Añadido: mover_directo requerido por trampa.py
    # -------------------------
    def mover_directo(self, jugador, nueva_pos):
        """Mueve instantáneamente (sin animación) el jugador a nueva_pos."""
        try:
            n = int(nueva_pos)
        except:
            return
        n = max(1, min(100, n))
        x, y, z = self.casilla_a_pos(n)
        try:
            jugador.position = Vec3(x, 0.2, z)
            jugador.posicion = n
        except Exception:
            jugador.x = x
            jugador.y = 0.2
            jugador.z = z
            jugador.posicion = n

        if jugador is self.jugador1:
            self.pos_j1 = n
        elif jugador is self.jugador2:
            self.pos_j2 = n

    # ======================================================
    # ----- LÓGICA DEL DADO -----
    # ======================================================
    def lanzar_dado(self):
        print("Lanzando dado...")
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
        print(f"➡ Dado sacó {numero}")

        try:
            import preguntas
            if hasattr(preguntas, "actualizar_valor_dado"):
                preguntas.actualizar_valor_dado(numero)
        except:
            pass

        if self.current_roll_player is None:
            self.current_roll_player = 1 if self.turno_jugador1 else 2

        player_idx = self.current_roll_player
        player_entity = self.jugador1 if player_idx == 1 else self.jugador2
        rival_entity = self.jugador2 if player_idx == 1 else self.jugador1

        # comprobar bloqueo por firewall ANTES de planear movimiento
        if getattr(player_entity, "bloqueado", False):
            print(f"⚠ Jugador {player_idx} está BLOQUEADO (firewall). No avanza este turno.")
            player_entity.bloqueado = False
            self.boton_dado.enable()
            self.turno_jugador1 = not self.turno_jugador1
            self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"
            self.current_roll_player = None
            return

        current_pos = self.pos_j1 if player_idx == 1 else self.pos_j2

        # -----------------------------
        # DADO NEGATIVO (RETROCEDE EXACTAMENTE EL VALOR DEL DADO)
        # -----------------------------
        if getattr(player_entity, "dado_negativo", False):
            destino = max(1, current_pos - numero)
            print(f"↩ Dado negativo aplicado: Jugador {player_idx} retrocede {numero} casillas → {destino}")
            player_entity.dado_negativo = False
        else:
            destino = min(100, current_pos + numero)

        self.pending_move = {"player": player_idx, "steps": int(numero), "dest": int(destino)}
        invoke(self._hacer_pregunta, self.turno_jugador1, delay=0.8)

    # -----------------------------------------------------
    # resto del código se mantiene exactamente igual
    # -----------------------------------------------------
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
            except Exception:
                x, y, z = self.casilla_a_pos(destino)
                jugador_entity.position = Vec3(x, 0.2, z)
                jugador_entity.posicion = destino

            if getattr(jugador_entity, "sql_inyeccion", False):
                try:
                    extra_dest = min(100, jugador_entity.posicion + 1)
                    print(f"🔀 SQL activo: Jugador {idx} avanza +1 adicional a {extra_dest}")
                    try:
                        jugador_entity.mover_a_casilla(extra_dest)
                    except Exception:
                        x2, y2, z2 = self.casilla_a_pos(extra_dest)
                        jugador_entity.position = Vec3(x2, 0.2, z2)
                        jugador_entity.posicion = extra_dest
                except Exception as e:
                    print("Error aplicando SQL extra:", e)
                finally:
                    try: jugador_entity.sql_inyeccion = False
                    except: pass

            if jugador_entity is self.jugador1:
                self.pos_j1 = int(getattr(jugador_entity, "posicion", destino))
            else:
                self.pos_j2 = int(getattr(jugador_entity, "posicion", destino))

            self.pending_move = None
            self.boton_dado.enable()

        if self.pending_move is None:
            return

        player_idx = int(self.pending_move.get("player"))
        player_entity = self.jugador1 if player_idx == 1 else self.jugador2

        if getattr(player_entity, "zero_day", False):
            print(f"✨ Zero-day activo para Jugador {player_idx}: respuesta automática.")
            try: player_entity.zero_day = False
            except: pass
            mover_confirmado(player_entity)
            self.turno_jugador1 = not turno_bool
            self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"
            self.current_roll_player = None
            return

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
        except Exception as e:
            print("Error mostrando pregunta:", e)
            nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True

        self.pos_j1 = int(nuevo_p1)
        self.pos_j2 = int(nuevo_p2)
        self.turno_jugador1 = not turno_bool
        self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"
        self.current_roll_player = None

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


if __name__ == "__main__":
    print("=== Iniciando juego ===")
    app = Ursina()
    Sky(color=color.gray)
    Tablero()
    app.run()
