from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from jugador import Jugador1, Jugador2
from dado import Dado3D
import importlib
import traceback
from trampa import abrir_tienda_trampas
import puntaje  


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
                p.inmunidad = False
            if not hasattr(p, "puntaje_congelado"):
                p.puntaje_congelado = False
            if not hasattr(p, "ayuda"):
                p.ayuda = None
            if not hasattr(p, "posicion"):
                p.posicion = 1
            if not hasattr(p, "actualizar_posicion"):
                def _actualizar_posicion_local(self_obj=p):
                    try:
                        if hasattr(self_obj, "mover_a_casilla"):
                            self_obj.mover_a_casilla(self_obj.posicion)
                        else:
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

        self.manual_move = None
        self.texto_manual = None  

        self.texto_turno = Text(parent=camera.ui, text="Turno: Jugador 1", y=.45, origin=(0,0), scale=1.2,
                                background=True, background_color=color.black)

        self.boton_dado = Button(parent=camera.ui, text="TIRAR DADO", scale=0.15,
                                 color=color.azure, y=-0.45, on_click=self.lanzar_dado)

        self.boton_tienda = Button(
            parent=camera.ui,
            text="TIENDA TRAMPAS",
            scale=0.2,
            color=color.orange,
            x=0.7,
            y=-0.45,
            on_click=self.abrir_tienda_trampas
        )

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

        self.actualizar_puntaje_ui()

        try:
            self.mover_a_casilla(self.jugador1, self.pos_j1)
            self.mover_a_casilla(self.jugador2, self.pos_j2)
        except Exception as e:
            print("Error inicial mover_a_casilla:", e)

    def actualizar_puntaje_ui(self):
        try:
            self.puntaje_j1 = int(getattr(puntaje, "puntaje_jugador1", 0))
            self.puntaje_j2 = int(getattr(puntaje, "puntaje_jugador2", 0))

            self.texto_puntaje_j1.text = f"Puntaje Jugador 1: {self.puntaje_j1}"
            self.texto_puntaje_j2.text = f"Puntaje Jugador 2: {self.puntaje_j2}"
        except Exception as e:
            print("Error actualizar_puntaje_ui:", e)

    # ======================================================
    # ----- LÓGICA DEL DADO -----
    # ======================================================
    def lanzar_dado(self):
        print("Lanzando dado...")

        jugador_actual = self.jugador1 if self.turno_jugador1 else self.jugador2

        if getattr(jugador_actual, "bloqueado", False):
            if getattr(jugador_actual, "inmunidad", False):
                jugador_actual.inmunidad = False
                jugador_actual.bloqueado = False
                print("[INMUNIDAD] Cortafuegos consumido — se anuló el bloqueo")
                self.texto_aviso.text = "Tu cortafuegos anuló la trampa"
                self.texto_aviso.enabled = True
                invoke(lambda: setattr(self.texto_aviso, "enabled", False), delay=2)
            else:
                jugador_actual.bloqueado = False

                self.texto_aviso.text = "No puedes tirar el dado este turno (FIREWALL)"
                self.texto_aviso.enabled = True
                invoke(lambda: setattr(self.texto_aviso, "enabled", False), delay=2)

                self.turno_jugador1 = not self.turno_jugador1
                self.texto_turno.text = "Turno: Jugador 1" if self.turno_jugador1 else "Turno: Jugador 2"

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

        # SQL Injection
        if getattr(jugador_entity, "sql_inyeccion", False):
            numero += 1
            jugador_entity.sql_inyeccion = False
            print(f"[SQL Injection] Jugador {player_idx} avanza 1 casilla extra.")

        # PHISHING
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

            try:
                self.actualizar_puntaje_ui()
            except:
                pass

        # TURBO
        if getattr(jugador_entity, "turbo", False):
            jugador_entity.turbo = False
            numero = numero * 2
            print(f"[TURBO] Jugador {player_idx} duplica tirada → nuevo número: {numero}")

        # DADO NEGATIVO (rival)
        if getattr(rival_entity, "dado_negativo", False):
            if getattr(rival_entity, "inmunidad", False):
                print(f"[INMUNIDAD] Rival protegido del Dado Negativo")
                rival_entity.dado_negativo = False
                rival_entity.inmunidad = False
            else:
                destino = current_pos - numero
                if destino < 1:
                    destino = 1
                print(f"[Dado Negativo] Jugador {player_idx} retrocede {numero} → {destino}")
                rival_entity.dado_negativo = False

                self.pending_move = {"player": player_idx, "steps": -numero, "dest": int(destino)}
                invoke(self._hacer_pregunta, self.turno_jugador1, delay=0.8)
                return
        else:
            destino = current_pos + numero
            if destino > 100:
                destino = 100

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
            # Nota: ahora creamos un movimiento MANUAL y NO movemos al jugador instantáneamente.
            moved_flag["called"] = True

            if jugador_entity is self.jugador1:
                idx = 1
            elif jugador_entity is self.jugador2:
                idx = 2
            else:
                return

            # Determinar destino y pasos
            if nueva_pos is None:
                if not self.pending_move or self.pending_move.get("player") != idx:
                    return
                destino = int(self.pending_move.get("dest"))
                pasos = int(self.pending_move.get("steps"))
            else:
                destino = max(1, min(100, int(nueva_pos)))
                # calcular pasos relativos desde la posición actual
                actual = self.pos_j1 if idx == 1 else self.pos_j2
                pasos = destino - actual

            # Preparar movimiento manual (paso por paso)
            direccion = 1 if pasos >= 0 else -1
            pasos_restantes = abs(int(pasos))

            # Si no hay pasos (p.e. 0), no activamos modo manual, hacemos movimiento normal
            if pasos_restantes == 0:
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
                # terminar como antes
                self.boton_dado.enable()
                try:
                    if getattr(jugador_entity, "puntaje_congelado", False):
                        print(f"[RANSOMWARE] Jugador {idx} tiene puntaje congelado")
                        jugador_entity.puntaje_congelado = False
                    self.actualizar_puntaje_ui()
                except Exception as e:
                    print("Error actualizando puntaje UI:", e)
                return

            # guardar manual_move en el tablero
            self.manual_move = {
                "player": idx,
                "steps_left": pasos_restantes,
                "direction": direccion,
                "target": destino
            }

            # limpiar pending_move (ya no la usaremos)
            self.pending_move = None

            # mostrar instrucción UI breve
            try:
                if self.texto_manual:
                    try: self.texto_manual.disable()
                    except: pass
                if idx == 1:
                    tecla = "W" if direccion == 1 else "S"
                else:
                    tecla = "UP" if direccion == 1 else "DOWN"
                self.texto_manual = Text(parent=camera.ui,
                                        text=f"Movimiento manual Jugador {idx}: pulsa {tecla} {self.manual_move['steps_left']} veces",
                                        y=-0.32, scale=1, background=True,
                                        background_color=color.rgba(0,0,0,180))
            except Exception:
                pass

            # NOTA: NO habilitamos el boton_dado aquí. Se habilitará cuando termine el movimiento manual.
            # Además actualizar UI de puntaje se hará cuando termine el movimiento para respetar 'puntaje_congelado' etc.

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

        try:
            self.actualizar_puntaje_ui()
        except Exception as e:
            print("Error puntaje final pregunta:", e)

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

    def abrir_tienda_trampas(self):
        jugador_actual = 1 if self.turno_jugador1 else 2
        abrir_tienda_trampas(self, jugador_actual)


# ======================================================================
#  🔥 INPUT GLOBAL NECESARIO PARA TECLAS A/B/C/D EN RESPUESTAS
#  y MOVIMIENTO MANUAL (W/S para J1, UP/DOWN para J2)
# ======================================================================
teclas_validas = {"a": "A", "b": "B", "c": "C", "d": "D"}

def _buscar_tablero_instancia():
    """
    Busca y retorna la primera instancia de Tablero en scene.entities (o None).
    """
    try:
        for ent in scene.entities:
            if isinstance(ent, Tablero):
                return ent
    except:
        pass
    return None


def _procesar_input_preguntas(key):
    """
    Lógica original para A/B/C/D -- encapsulada aquí para mantenerla limpia.
    """
    try:
        # print("TECLA:", key)
        pass
    except:
        pass

    k = key.lower()

    # Importar módulo de preguntas
    try:
        import preguntas
    except:
        return

    # Si no hay pregunta activa, ignorar
    if not hasattr(preguntas, "pregunta_actual"):
        return
    if preguntas.pregunta_actual is None:
        return

    # Solo procesamos A/B/C/D
    if k in teclas_validas:
        letra = teclas_validas[k]

        # Buscar botón con la letra correcta
        for b in preguntas.botones_opciones:
            if getattr(b, "letra", None) == letra:
                try:
                    b.on_click()
                except:
                    try:
                        if callable(b.on_click):
                            b.on_click()
                    except:
                        pass
                break


def _procesar_input_movimiento_manual(key):
    """
    Si existe un movimiento manual pendiente en el Tablero, procesa teclas:
      - Jugador1: 'w' (adelante), 's' (atrás)
      - Jugador2: 'up'/'up arrow' (adelante), 'down'/'down arrow' (atrás)
    Cada pulsación mueve 1 casilla y reduce steps_left en 1. Cuando steps_left == 0,
    se finaliza el movimiento (se habilita el boton del dado y se actualiza UI).
    """
    tablero = _buscar_tablero_instancia()
    if tablero is None:
        return

    mm = getattr(tablero, "manual_move", None)
    if not mm:
        return

    k = key.lower()

    player = mm.get("player")
    direction = int(mm.get("direction", 1))
    # keys permitidas para avance/retroceso según jugador
    if player == 1:
        avanzar_key = "w"
        retro_key = "s"
    else:
        # soportar variaciones 'up' y 'up arrow'
        avanzar_key_options = ("up", "up arrow")
        retro_key_options = ("down", "down arrow")
        # detect en k
        if k in avanzar_key_options:
            avanzar = True
        elif k in retro_key_options:
            avanzar = False
        else:
            avanzar = None

    # determinar si la pulsación corresponde a la dirección esperada
    accepted = False
    if player == 1:
        if direction == 1 and k == avanzar_key:
            accepted = True
        elif direction == -1 and k == retro_key:
            accepted = True
    else:
        if direction == 1 and k in ("up", "up arrow"):
            accepted = True
        elif direction == -1 and k in ("down", "down arrow"):
            accepted = True

    if not accepted:
        return  # ignorar otras teclas

    # procesar un paso
    try:
        pasos_restantes = int(mm.get("steps_left", 0))
    except:
        pasos_restantes = 0

    if pasos_restantes <= 0:
        # nada que hacer
        tablero.manual_move = None
        try:
            if tablero.texto_manual:
                tablero.texto_manual.disable()
                tablero.texto_manual = None
        except:
            pass
        return

    # mover el jugador una casilla en la dirección indicada
    if player == 1:
        actual = tablero.pos_j1
        nuevo = max(1, min(100, actual + direction))
        tablero.mover_a_casilla(tablero.jugador1, nuevo)
        tablero.pos_j1 = nuevo
    else:
        actual = tablero.pos_j2
        nuevo = max(1, min(100, actual + direction))
        tablero.mover_a_casilla(tablero.jugador2, nuevo)
        tablero.pos_j2 = nuevo

    # decrementar contador
    mm["steps_left"] = pasos_restantes - 1

    # actualizar texto_manual
    try:
        if tablero.texto_manual:
            try: tablero.texto_manual.disable()
            except: pass
        if mm["steps_left"] > 0:
            if player == 1:
                tecla = "W" if direction == 1 else "S"
            else:
                tecla = "UP" if direction == 1 else "DOWN"
            tablero.texto_manual = Text(parent=camera.ui,
                                       text=f"Movimiento manual Jugador {player}: pulsa {tecla} {mm['steps_left']} veces",
                                       y=5, x=0, scale=1, background=True,
                                       background_color=color.rgba(0,0,0,180))
        else:
            # movimiento completado
            # limpiar UI
            try:
                if tablero.texto_manual:
                    tablero.texto_manual.disable()
            except:
                pass
            tablero.manual_move = None

            # habilitar boton dado (vuelve a permitir tirar)
            try:
                tablero.boton_dado.enable()
            except:
                pass

            # sincronizar puntaje UI al finalizar el movimiento
            try:
                tablero.actualizar_puntaje_ui()
            except:
                pass

    except Exception as e:
        print("Error procesando movimiento manual:", e)
        # intentar finalizar igual
        try:
            if tablero.texto_manual:
                tablero.texto_manual.disable()
        except:
            pass
        tablero.manual_move = None
        try:
            tablero.boton_dado.enable()
        except:
            pass


def input(key):
    # 1) Primero procesar input relativo a preguntas (A/B/C/D)
    try:
        _procesar_input_preguntas(key)
    except Exception:
        pass

    # 2) Procesar movimiento manual si corresponde
    try:
        _procesar_input_movimiento_manual(key)
    except Exception:
        pass

    # (Nota: no añadimos otras funciones globales de input para evitar interferir con lo existente)


# ======================================================================

if __name__ == "__main__":
    print("=== Iniciando juego ===")
    app = Ursina()
    Sky(color=color.gray)
    Tablero()
    app.run()


#(1. Firewall (NO inmediata)

#Marca al rival como bloqueado: rival.bloqueado = True

#El rival pierde su próximo turno.

#No mueve casillas ni modifica puntos.

#Se activa cuando se compre, pero el efecto sucede en el turno del rival.

#✅ 2. Phishing

#Roba hasta 500 puntos del rival.

#Los suma al jugador que la compró.
#Reparte automáticamente según quién ejecute la trampa.

#Ejemplo:
#Rival tiene 340 → robas 340
#Rival tiene 1000 → robas 500

#✅ 3. DDoS (INMEDIATA)

#El rival retrocede 3 casillas inmediatamente.

#Usa:

#rival.actualizar_posicion() si existe

#o tablero.mover_a_casilla(rival, nueva_pos) como fallback

#Si está muy atrás, lo deja mínimo en casilla 1.

#✅ 4. Ransomware

#El rival pierde 300 puntos.

#No mueve casillas.

#No congela ni bloquea.

#✅ 5. Zero-Day (INMEDIATA)

#avanzas 4 casillas de inmediato.

#Usa la misma lógica de actualización que las otras trampas.

#✅ 6. Avanzar 10 (INMEDIATA)

#Avanzas 10 casillas inmediatamente.

#✅ 7. Robar ayuda

#Si el rival tiene una ayuda almacenada en rival.ayuda:

#Tú la recibes

#Al rival se le borra (rival.ayuda = None)

#Si no tiene ayuda, no hace nada.

#🔥 8. Intercambiar posiciones (INMEDIATA)

#INTERCAMBIA LAS POSICIONES REALES DE LOS JUGADORES.
#(Aunque ahora lo vamos a corregir como pediste.)

#Deja:

#Jugador1.posición = posición antigua del jugador2

#Jugador2.posición = posición antigua del jugador1

#PERO solo mueve el modelo visual, no actualiza correctamente pos_j1, pos_j2, o variables del tablero.
#🔧 Por eso “funciona pero no funciona”.

#✅ 9. Resbalón (INMEDIATA)

#El rival retrocede 2 casillas (mínimo casilla 1).

#✅ 10. Turbo (INMEDIATA)

#Avanzas 2 casillas inmediatamente.)