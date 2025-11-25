# tablero_debug.py — reemplaza tu tablero.py por este para depuración
from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from jugador import Jugador1, Jugador2
from dado import Dado3D
import importlib
import traceback

# Ajustable: tamaño "real" de UNA casilla en unidades de mundo
CELL_SIZE = 0.93

# Ajustable: multiplicador de distancia de movimiento de los muñecos
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
        print("⚠ STUB mostrar_pregunta: confirmando movimiento automáticamente.")
        jugador_entity = j1 if turno else j2
        mover_confirmado(jugador_entity)
        return p1, p2, True


class Tablero(Entity):
    def __init__(self):
        super().__init__()
        print("✔ Cargando tablero...")

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

        print("✔ Cargando jugadores...")
        self.jugador1 = Jugador1(modelo="models/jugador1.obj", tablero=self)
        self.jugador2 = Jugador2(modelo="models/jugador2.obj", tablero=self)
        print(f"✔ Jugadores colocados: id1={id(self.jugador1)}, id2={id(self.jugador2)}")

        self.pos_j1 = 1
        self.pos_j2 = 1
        self.turno_jugador1 = True
        self.pending_move = None
        self.roll_count = 0
        self.current_roll_player = None

        # UI: turno y botón dado
        self.texto_turno = Text(parent=camera.ui, text="Turno: Jugador 1", y=.45, origin=(0,0), scale=1.2, background=True, background_color=color.black)
        self.boton_dado = Button(parent=camera.ui, text="TIRAR DADO", scale=0.15, color=color.azure, y=-0.45, on_click=self.lanzar_dado)

        # ============================================================
        # === PUNTAJES EN ESQUINA SUPERIOR IZQUIERDA (CORREGIDO) ====
        # ============================================================
        self.puntaje_j1 = 0
        self.puntaje_j2 = 0

        self.texto_puntaje_j1 = Text(
            parent=camera.ui,
            text=f"Puntaje Jugador 1: {self.puntaje_j1}",
            origin=(-0.5, 0.5),
            x=-0.87,
            y=0.47,
            scale=1.0,
            background=True,
            background_color=color.rgba(0,0,0,150)
        )

        self.texto_puntaje_j2 = Text(
            parent=camera.ui,
            text=f"Puntaje Jugador 2: {self.puntaje_j2}",
            origin=(-0.5, 0.5),
            x=-0.87,
            y=0.40,
            scale=1.0,
            background=True,
            background_color=color.rgba(0,0,0,150)
        )
        # ============================================================

        self.dado = None
        self._pos_cache = {}

        try:
            self.mover_a_casilla(self.jugador1, self.pos_j1)
            self.mover_a_casilla(self.jugador2, self.pos_j2)
        except Exception as e:
            print("Error inicial mover_a_casilla:", e)

    def lanzar_dado(self):
        print("\n🎲 Lanzando dado...")
        if self.dado is None:
            self.dado = Dado3D(position=(0,1,0), scale=50)
        self.boton_dado.disable()
        self.roll_count += 1

        # --- CORRECCIÓN: asignar el roll al jugador cuyo turno es actual ---
        self.current_roll_player = 1 if self.turno_jugador1 else 2
        print(f"Roll #{self.roll_count} -> candidato a mover: Jugador {self.current_roll_player} (basado en turno actual)")

        self.dado.lanzar(callback=self.despues_del_dado)

    def despues_del_dado(self, numero):
        # Asegurarse que 'numero' es int
        try:
            numero = int(round(float(numero)))
        except Exception:
            numero = 1
        print(f"➡ Dado sacó {numero}")

        # Actualizar valor en el módulo de preguntas (si existe) para que use ese valor
        try:
            import preguntas
            if hasattr(preguntas, "actualizar_valor_dado"):
                preguntas.actualizar_valor_dado(numero)
        except Exception:
            pass

        if self.current_roll_player is None:
            # fallback: usar el turno actual si por alguna razón no está definido
            self.current_roll_player = 1 if self.turno_jugador1 else 2

        player_idx = self.current_roll_player
        current_pos = self.pos_j1 if player_idx == 1 else self.pos_j2
        destino = current_pos + numero
        if destino > 100:
            destino = 100

        # Guardar pasos explícitos y destino (debug)
        self.pending_move = {"player": player_idx, "steps": int(numero), "dest": int(destino)}
        print(f"Pending move guardado: player={player_idx}, steps={self.pending_move['steps']}, dest={self.pending_move['dest']}")
        # PASAR tablero=self a mostrar_pregunta más abajo
        invoke(self._hacer_pregunta, self.turno_jugador1, delay=0.8)

    def _hacer_pregunta(self, turno_bool):
        print("\n>>> MOSTRAR PREGUNTA (turno_bool):", "Jugador 1" if turno_bool else "Jugador 2")
        moved_flag = {"called": False}

        def mover_confirmado(jugador_entity, nueva_pos=None, retroceder=False):
            moved_flag["called"] = True
            print("\n--- mover_confirmado llamado ---")
            print(f"Jugador entity id: {id(jugador_entity)} - repr: {repr(jugador_entity)}")

            if jugador_entity is self.jugador1:
                idx = 1
            elif jugador_entity is self.jugador2:
                idx = 2
            else:
                print("mover_confirmado: jugador desconocido")
                return

            # print estado actual de ambos jugadores antes de mover
            print("\nESTADO ANTES DE MOVER (AMBOS JUGADORES):")
            for n, p in ((1,self.jugador1),(2,self.jugador2)):
                print(f" Jugador {n}: id={id(p)}, posicion={getattr(p,'posicion',None)}, position={getattr(p,'position',None)}")

            if nueva_pos is None:
                if not self.pending_move or self.pending_move.get("player") != idx:
                    print("mover_confirmado: no hay pending_move válido para este jugador. Ignorando movimiento.")
                    return
                destino = int(self.pending_move.get("dest"))
                pasos = int(self.pending_move.get("steps"))
            else:
                destino = int(max(1, min(100, int(nueva_pos))))
                actual_tmp = getattr(jugador_entity, "posicion", None)
                if actual_tmp is None:
                    actual_tmp = (self.pos_j1 if idx == 1 else self.pos_j2)
                pasos = max(0, destino - actual_tmp)

            # Extra chequeo: si la pending_move indica otro jugador, no aplicarla
            if nueva_pos is None and idx != self.current_roll_player:
                print(f"mover_confirmado: idx {idx} no coincide con current_roll_player {self.current_roll_player}. Ignorado.")
                return

            # DEBUG: coordenadas para casilla actual y destino
            actual_num = getattr(jugador_entity, "posicion", None)
            if actual_num is None:
                actual_num = (self.pos_j1 if idx == 1 else self.pos_j2)
            x_act, y_act, z_act = self.casilla_a_pos(actual_num)
            x_des, y_des, z_des = self.casilla_a_pos(destino)

            print("\n--- DETALLE MOVIMIENTO ---")
            print(f" idx: {idx}")
            print(f" pasos (dado): {pasos}")
            print(f" actual_num (casilla): {actual_num} -> coords casilla: x={x_act}, z={z_act}")
            print(f" destino (casilla): {destino} -> coords casilla: x={x_des}, z={z_des}")
            # mostrar offsets del jugador (si existen)
            pos_x = getattr(jugador_entity, "pos_x", None)
            pos_y = getattr(jugador_entity, "pos_y", None)
            pos_z = getattr(jugador_entity, "pos_z", None)
            print(f" offsets jugador: pos_x={pos_x}, pos_y={pos_y}, pos_z={pos_z}")

            # chequear duplicados de coordenadas (redondeadas)
            key_dest = (round(x_des,4), round(y_des,4), round(z_des,4))
            if key_dest in self._pos_cache and self._pos_cache[key_dest] != destino:
                print(f"⚠ Coordenadas destino duplicadas: casilla {self._pos_cache[key_dest]} y {destino} -> {key_dest}")
            else:
                self._pos_cache[key_dest] = destino

            # Hacer el movimiento usando mover_a_casilla del jugador (respeta offsets)
            try:
                if hasattr(jugador_entity, "mover_a_casilla"):
                    jugador_entity.mover_a_casilla(destino)
                else:
                    x, y, z = self.casilla_a_pos(destino)
                    jugador_entity.position = Vec3(x, getattr(jugador_entity,'y',0.2), z)
                    jugador_entity.posicion = destino
            except Exception as e:
                print("Error moviendo entidad en mover_confirmado:", e)
                try:
                    x, y, z = self.casilla_a_pos(destino)
                    jugador_entity.position = Vec3(x, 0.2, z)
                    jugador_entity.posicion = destino
                except:
                    pass

            # estado después
            print("\nESTADO DESPUÉS DE MOVER (AMBOS JUGADORES):")
            for n, p in ((1,self.jugador1),(2,self.jugador2)):
                print(f" Jugador {n}: id={id(p)}, posicion={getattr(p,'posicion',None)}, position={getattr(p,'position',None)}")

            # actualizar lógica tablero
            if idx == 1:
                self.pos_j1 = destino
            else:
                self.pos_j2 = destino

            if self.pending_move and self.pending_move.get("player") == idx:
                self.pending_move = None

            self.boton_dado.enable()
            print("--- mover_confirmado finalizado ---\n")

        # ejecutar mostrar_pregunta (ahora pasando tablero=self)
        try:
            result = mostrar_pregunta(
                turno_bool, self.jugador1, self.jugador2,
                self.pos_j1, self.pos_j2, self.texto_turno, self.boton_dado, mover_confirmado,
                tablero=self
            )
            if result is None:
                nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True
            else:
                try:
                    nuevo_p1, nuevo_p2, cambiar_turno = result
                except:
                    nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True
        except Exception as e:
            print("Error llamando mostrar_pregunta:", e)
            nuevo_p1, nuevo_p2, cambiar_turno = self.pos_j1, self.pos_j2, True

        try:
            nuevo_p1_int = int(nuevo_p1)
        except:
            nuevo_p1_int = self.pos_j1
        try:
            nuevo_p2_int = int(nuevo_p2)
        except:
            nuevo_p2_int = self.pos_j2

        if turno_bool:
            self.pos_j1 = nuevo_p1_int
        else:
            self.pos_j2 = nuevo_p2_int

        # sincronizar vista si fuera necesario
        if getattr(self.jugador1, "posicion", None) != self.pos_j1:
            try:
                self.mover_a_casilla(self.jugador1, self.pos_j1)
            except Exception as e:
                print("Error sync j1:", e)
        if getattr(self.jugador2, "posicion", None) != self.pos_j2:
            try:
                self.mover_a_casilla(self.jugador2, self.pos_j2)
            except Exception as e:
                print("Error sync j2:", e)

        self.turno_jugador1 = not turno_bool
        self.texto_turno.text = ("Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2")
        if not self.boton_dado.enabled:
            self.boton_dado.enable()
        self.current_roll_player = None

    def mover_a_casilla(self, jugador, nueva_pos):
        try:
            nueva_pos = int(nueva_pos)
        except:
            nueva_pos = 1
        nueva_pos = max(1, min(100, nueva_pos))

        print(f"[mover_a_casilla] llamado para jugador id={id(jugador)} nueva_pos={nueva_pos}")
        if hasattr(jugador, "mover_a_casilla"):
            try:
                jugador.mover_a_casilla(nueva_pos)
            except Exception as e:
                print("Error jugador.mover_a_casilla:", e)
                x, y, z = self.casilla_a_pos(nueva_pos)
                jugador.position = Vec3(x, getattr(jugador,'y',0.2), z)
                jugador.posicion = nueva_pos
        else:
            x, y, z = self.casilla_a_pos(nueva_pos)
            jugador.position = Vec3(x, getattr(jugador,'y',0.2), z)
            jugador.posicion = nueva_pos

        if jugador is self.jugador1:
            self.pos_j1 = nueva_pos
        elif jugador is self.jugador2:
            self.pos_j2 = nueva_pos

        print(f"[mover_a_casilla] terminado jugador id={id(jugador)} posicion ahora={jugador.posicion} x={getattr(jugador,'x',None)} z={getattr(jugador,'z',None)} position={getattr(jugador,'position',None)}")

    def casilla_a_pos(self, num):
        num = max(1, min(100, int(num)))
        fila = (num - 1) // 10
        col = (num - 1) % 10
        if fila % 2 == 1:
            col = 9 - col
        offset = (CELL_SIZE * 9) / 2
        x = col * CELL_SIZE - offset
        z = fila * CELL_SIZE - offset
        
        # Aplicar multiplicador solo a la distancia entre casillas, no a la posición inicial
        distancia_x = (x - 0) * (MOVIMIENTO_MULTIPLIER - 1)
        distancia_z = (z - 0) * (MOVIMIENTO_MULTIPLIER - 1)
        x = x + distancia_x
        z = z + distancia_z
        return (x, 0, z)


if __name__ == "__main__":
    print("=== Iniciando juego (debug) ===")
    app = Ursina()
    Sky(color=color.gray)
    Tablero()
    app.run()