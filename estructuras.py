import random
import os

# --------------------
# Lógica y manejo de preguntas (sin dependencias gráficas)
# --------------------

def cargar_preguntas(ruta="preguntas.txt"):
    """
    Lee preguntas desde un archivo. Cada linea:
    pregunta;opA;opB;opC;opD;RESPUESTA_CORRECTA;imagen_opcional
    Retorna lista de dicts: {pregunta, opciones:list, correcta:str, imagen: str|None}
    """
    preguntas = []
    if not os.path.exists(ruta):
        print(f"⚠️ No existe {ruta}. Crea el archivo con preguntas.")
        return preguntas

    with open(ruta, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            partes = [p.strip() for p in linea.split(";")]
            # tolerancia: permitir líneas con o sin campo imagen
            if len(partes) >= 6:
                pregunta_text = partes[0]
                opciones = partes[1:5]
                correcta = partes[5].upper() if partes[5] else ""
                imagen = partes[6] if len(partes) >= 7 and partes[6] else None
                preguntas.append({
                    "pregunta": pregunta_text,
                    "opciones": opciones,
                    "correcta": correcta,
                    "imagen": imagen
                })
            else:
                # línea mal formada — la ignoramos
                print("Línea de pregunta ignorada (formato incorrecto):", linea)
    return preguntas


def seleccionar_pregunta_aleatoria(preguntas):
    """Devuelve (pregunta_dict) o None si no hay preguntas."""
    if not preguntas:
        return None
    return random.choice(preguntas)


def validar_respuesta(pregunta_dict, letra_seleccionada):
    """
    letra_seleccionada: 'A'|'B'|'C'|'D' (mayúscula o minúscula aceptada)
    Retorna True si acertó, False si no.
    """
    if not pregunta_dict:
        return False
    if not letra_seleccionada:
        return False
    return letra_seleccionada.strip().upper() == pregunta_dict.get("correcta", "").strip().upper()


def avanzar_posicion(pos_actual, pasos=1, max_pos=100):
    """Avanza la posición dentro de los límites del tablero."""
    nueva = pos_actual + pasos
    if nueva > max_pos:
        nueva = max_pos
    if nueva < 1:
        nueva = 1
    return nueva


# --------------------
# Tirar dado (lógica simple por si la necesitas)
# --------------------
def tirar_dado():
    """
    Simula tirar un dado de 6 caras y devuelve un número del 1 al 6.
    """
    resultado = random.randint(1, 6)
    print(f"🎲 Dado lanzado: {resultado}")
    return resultado


# --------------------
# Cambiar turno (opción B: función disponible)
# --------------------
def cambiar_turno(turno_actual: bool) -> bool:
    """Recibe True (jugador 1) o False (jugador 2) y retorna el opuesto."""
    return not turno_actual
