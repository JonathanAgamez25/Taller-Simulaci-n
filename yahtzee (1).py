"""
=============================================================================
  SIMULACIÓN YAHTZEE – MÉTODO DE MONTECARLO
=============================================================================

  ¿QUÉ ES EL MÉTODO DE MONTECARLO?
  ---------------------------------
  El método de Montecarlo es una técnica computacional que usa números
  aleatorios para estimar resultados de sistemas complejos. La idea central
  es: en lugar de calcular la probabilidad de forma matemática exacta,
  SIMULA el experimento miles de veces y observa la frecuencia de resultados.

  EJEMPLO CLÁSICO: Estimar π lanzando puntos aleatorios en un cuadrado.
  ESTE PROYECTO:   Simular Yahtzee N veces para analizar probabilidades
                   de ganar, distribución de puntajes, etc.

  DISTRIBUCIÓN USADA:
  -------------------
  Cada dado modela una variable aleatoria con distribución UNIFORME DISCRETA:
      X ~ Uniforme{1, 2, 3, 4, 5, 6}
      P(X = k) = 1/6 ≈ 0.1667   para todo k ∈ {1, 2, 3, 4, 5, 6}
      Media (μ) = (1+2+3+4+5+6)/6 = 3.5
      Varianza (σ²) = 35/12 ≈ 2.917

  Autor: Jonatan Avila- Jhan Moreno
  Fecha: 2025
  Curso: Simulación 
=============================================================================
"""

import random        # Módulo para generar números pseudoaleatorios (Mersenne Twister)
import time          # Para medir el tiempo de ejecución de la simulación
from collections import Counter  # Cuenta la frecuencia de cada valor en una lista


# =============================================================================
#  CONSTANTES DEL JUEGO
#  Definidas aquí arriba para que sean fáciles de modificar si se quiere
#  experimentar con variantes del juego (más dados, más lanzamientos, etc.)
# =============================================================================

NUM_DADOS        = 5   # Yahtzee clásico usa siempre 5 dados por turno
CARAS_DADO       = 6   # Dado estándar de 6 caras → valores posibles: 1, 2, 3, 4, 5, 6
MAX_LANZAMIENTOS = 3   # Cada turno permite hasta 3 lanzamientos en total
NUM_JUGADORES    = 2   # Esta simulación contempla exactamente 2 jugadores


# Lista de las 13 categorías de puntuación del Yahtzee.
# Cada jugador debe llenar TODAS las categorías exactamente una vez a lo largo
# de la partida, en el orden que prefiera (aquí lo decide la IA).
CATEGORIAS = [
    # ── Sección Superior (basada en valor numérico de los dados) ──────────
    "Unos",          # Suma de todos los dados que muestren el valor 1
    "Doses",         # Suma de todos los dados que muestren el valor 2
    "Treses",        # Suma de todos los dados que muestren el valor 3
    "Cuatros",       # Suma de todos los dados que muestren el valor 4
    "Cincos",        # Suma de todos los dados que muestren el valor 5
    "Seises",        # Suma de todos los dados que muestren el valor 6

    # ── Sección Inferior (combinaciones especiales) ───────────────────────
    "Trios",         # Al menos 3 dados con el mismo valor  → suma de esos 3
    "Poker",         # Al menos 4 dados con el mismo valor  → suma de esos 4
    "Full",          # Exactamente 3 de un valor + 2 de otro → 25 puntos fijos
    "Escalera Menor",# 4 dados formando una secuencia consecutiva → 30 puntos
    "Escalera Mayor",# 5 dados formando una secuencia consecutiva → 40 puntos
    "Yahtzee",       # Los 5 dados con el mismo valor → 50 puntos (¡lo máximo!)
    "Chance",        # Suma de todos los dados, sin condición especial
]


# =============================================================================
#  MÓDULO 1 – SIMULACIÓN MONTECARLO (Generación de Aleatoriedad)
#
#  Estas funciones son el NÚCLEO del método de Montecarlo:
#  simulan físicamente el lanzamiento de los dados mediante números
#  pseudoaleatorios con distribución uniforme.
# =============================================================================

def lanzar_dados(n=NUM_DADOS):
    """
    Simula el lanzamiento de 'n' dados físicos de 6 caras.

    CONEXIÓN CON MONTECARLO:
    ------------------------
    Esta función es la fuente de aleatoriedad de toda la simulación.
    random.randint(1, 6) genera un entero uniformemente distribuido
    en {1, 2, 3, 4, 5, 6}, replicando exactamente la distribución
    de un dado físico justo: P(X=k) = 1/6 para cada k.

    Con N=1000 partidas, esta función se llama aproximadamente:
        N × 13 turnos × 3 lanzamientos × 5 dados = 195,000 veces por jugador
    Lo que permite verificar la Ley de Grandes Números empíricamente.

    Args:
        n (int): Número de dados a lanzar. Por defecto 5 (regla del Yahtzee).

    Returns:
        list[int]: Lista de n enteros, cada uno entre 1 y 6.
    
    Ejemplo:
        >>> lanzar_dados()
        [3, 1, 5, 5, 2]  # resultado aleatorio
    """
    return [random.randint(1, CARAS_DADO) for _ in range(n)]


def relanzar_dados(dados_actuales, indices_guardar):
    """
    Vuelve a lanzar únicamente los dados que el jugador NO quiere conservar.

    En Yahtzee, entre lanzamientos el jugador puede "apartar" los dados
    que le convienen y relanzar solo los restantes. Esta función implementa
    exactamente esa mecánica.

    Args:
        dados_actuales (list[int]): Estado actual de los 5 dados [posición 0..4]
        indices_guardar (list[int]): Posiciones (0 a 4) de los dados a conservar.
                                     Los dados en estas posiciones NO se relanzarán.

    Returns:
        list[int]: Nueva lista de 5 dados. Los conservados mantienen su valor
                   y los demás se reemplazan con nuevos valores aleatorios.

    Ejemplo:
        dados = [3, 3, 1, 2, 6]
        indices_guardar = [0, 1]   # queremos conservar los dos 3's
        resultado posible → [3, 3, 4, 4, 2]  # posiciones 2,3,4 se relanzaron
    """
    nuevos_dados = dados_actuales.copy()  # Copiamos para no modificar el original

    for posicion in range(NUM_DADOS):
        # Si esta posición NO está en la lista de dados a guardar, la relanzamos
        if posicion not in indices_guardar:
            nuevos_dados[posicion] = random.randint(1, CARAS_DADO)

    return nuevos_dados


# =============================================================================
#  MÓDULO 2 – PUNTUACIÓN
#
#  Implementa las 13 reglas de puntuación del Yahtzee.
#  Estas funciones calculan cuántos puntos vale una combinación de dados
#  para una categoría específica.
# =============================================================================

def calcular_puntaje(dados, categoria):
    """
    Calcula los puntos que obtiene un jugador con unos dados dados en una categoría.

    TABLA DE PUNTUACIÓN COMPLETA:
    ┌─────────────────┬──────────────────────────────┬────────────────┐
    │ Categoría       │ Condición                    │ Puntos         │
    ├─────────────────┼──────────────────────────────┼────────────────┤
    │ Unos … Seises   │ Dados con ese valor           │ Suma de ellos  │
    │ Trios           │ ≥ 3 dados iguales             │ Valor × 3      │
    │ Poker           │ ≥ 4 dados iguales             │ Valor × 4      │
    │ Full            │ Tres de un valor + dos de otro│ 25 pts fijos   │
    │ Escalera Menor  │ 4 valores consecutivos        │ 30 pts fijos   │
    │ Escalera Mayor  │ 5 valores consecutivos        │ 40 pts fijos   │
    │ Yahtzee         │ Los 5 dados iguales           │ 50 pts fijos   │
    │ Chance          │ Cualquier combinación         │ Suma de los 5  │
    └─────────────────┴──────────────────────────────┴────────────────┘

    Args:
        dados (list[int]): Lista de 5 valores enteros (cada uno entre 1 y 6)
        categoria (str): Nombre de la categoría a evaluar (debe estar en CATEGORIAS)

    Returns:
        int: Puntaje obtenido. Retorna 0 si la combinación no cumple la condición.
    """
    # Counter cuenta cuántas veces aparece cada valor.
    # Ejemplo: dados=[3,3,3,5,2] → conteo = {3:3, 5:1, 2:1}
    conteo = Counter(dados)

    # ── Categorías numéricas (Unos, Doses, Treses, Cuatros, Cincos, Seises) ──
    # Estas categorías simplemente suman los dados que muestran el valor indicado.
    # Ejemplo: "Treses" con dados [3,3,1,3,5] → 3+3+3 = 9 puntos
    mapa_categoria_a_valor = {
        "Unos": 1, "Doses": 2, "Treses": 3,
        "Cuatros": 4, "Cincos": 5, "Seises": 6
    }
    if categoria in mapa_categoria_a_valor:
        valor_buscado = mapa_categoria_a_valor[categoria]
        # Suma únicamente los dados que tienen el valor de esta categoría
        return sum(dado for dado in dados if dado == valor_buscado)

    # ── Trios: Al menos 3 dados con el mismo valor ────────────────────────────
    # Puntúa la SUMA de esos 3 dados (no de los 5)
    # Ejemplo: [4,4,4,1,2] → Trios = 4+4+4 = 12 puntos
    if categoria == "Trios":
        for valor, cantidad in conteo.items():
            if cantidad >= 3:
                return valor * 3   # Suma de exactamente los 3 dados iguales
        return 0  # Ningún valor apareció 3 veces → 0 puntos

    # ── Poker: Al menos 4 dados con el mismo valor ───────────────────────────
    # Puntúa la SUMA de esos 4 dados (no de los 5)
    # Ejemplo: [2,2,2,2,5] → Poker = 2+2+2+2 = 8 puntos
    if categoria == "Poker":
        for valor, cantidad in conteo.items():
            if cantidad >= 4:
                return valor * 4   # Suma de exactamente los 4 dados iguales
        return 0

    # ── Full House: Exactamente 3 de un valor Y 2 de otro ────────────────────
    # El orden no importa. Siempre vale 25 puntos si se cumple la condición.
    # Ejemplo: [5,5,5,2,2] → Full = 25 puntos
    # NO válido: [5,5,5,5,2] (eso es Poker, no Full)
    if categoria == "Full":
        tiene_trio = any(cantidad == 3 for cantidad in conteo.values())
        tiene_par  = any(cantidad == 2 for cantidad in conteo.values())
        return 25 if (tiene_trio and tiene_par) else 0

    # ── Escalera Menor: 4 valores consecutivos entre los 5 dados ─────────────
    # Basta con que 4 de los 5 dados formen una secuencia.
    # Válidas: [1,2,3,4,X], [2,3,4,5,X], [3,4,5,6,X]
    # Ejemplo: [1,2,3,4,4] → los dados únicos son {1,2,3,4} → secuencia de 4 ✓
    if categoria == "Escalera Menor":
        valores_unicos = sorted(set(dados))  # set() elimina duplicados
        # Buscamos si existe alguna sub-secuencia de longitud 4
        for inicio in range(len(valores_unicos) - 3):
            segmento = valores_unicos[inicio : inicio + 4]
            secuencia_esperada = list(range(segmento[0], segmento[0] + 4))
            if segmento == secuencia_esperada:
                return 30
        return 0

    # ── Escalera Mayor: Los 5 dados forman una secuencia consecutiva ──────────
    # Solo hay dos posibilidades: {1,2,3,4,5} o {2,3,4,5,6}
    # Ejemplo: [1,2,3,4,5] → secuencia perfecta ✓ → 40 puntos
    if categoria == "Escalera Mayor":
        valores_unicos = sorted(set(dados))
        secuencia_esperada = list(range(min(dados), min(dados) + 5))
        # Condición: 5 valores únicos formando una secuencia sin saltos
        if len(valores_unicos) == 5 and valores_unicos == secuencia_esperada:
            return 40
        return 0

    # ── Yahtzee: Los 5 dados muestran exactamente el mismo valor ─────────────
    # Es la combinación más difícil y valiosa del juego.
    # Ejemplo: [6,6,6,6,6] → Yahtzee = 50 puntos
    # len(conteo) == 1 significa que solo existe UN valor distinto en los 5 dados
    if categoria == "Yahtzee":
        return 50 if len(conteo) == 1 else 0

    # ── Chance: Suma total de todos los dados, sin ninguna condición ──────────
    # Útil como categoría de "rescate" cuando no se tiene ninguna combinación.
    # Ejemplo: [4,3,6,2,5] → Chance = 4+3+6+2+5 = 20 puntos
    if categoria == "Chance":
        return sum(dados)

    # Si la categoría no reconocida, retornar 0 (no debería ocurrir)
    return 0


def mejor_categoria_disponible(dados, categorias_usadas):
    """
    Estrategia greedy de la IA: elige la categoría disponible con mayor puntaje.

    ESTRATEGIA GREEDY (voraz):
    --------------------------
    "Greedy" significa que la IA siempre toma la decisión que MAXIMIZA la
    ganancia INMEDIATA, sin planificar turnos futuros. Es simple pero efectiva.

    Proceso de decisión:
      1. Calcular el puntaje de cada categoría disponible con los dados actuales
      2. Elegir la que da más puntos
      3. Si ninguna da puntos (todas darían 0), elegir la primera disponible
         → Esto se llama "sacrificar" una categoría (estrategia de emergencia)

    Args:
        dados (list[int]): Los 5 dados del turno actual (ya en su forma final)
        categorias_usadas (dict): {nombre_categoria: bool} — True si ya fue usada

    Returns:
        tuple: (nombre_de_la_mejor_categoria, puntos_que_otorga)
               El segundo valor es 0 si se sacrificó una categoría.
    """
    mejor_categoria = None
    mayor_puntaje   = -1  # Iniciamos en -1 para que cualquier puntaje (incluso 0) gane

    # Recorremos todas las categorías del juego en orden
    for categoria in CATEGORIAS:
        # Solo consideramos categorías que AÚN NO han sido usadas
        if not categorias_usadas.get(categoria, False):
            puntos = calcular_puntaje(dados, categoria)
            if puntos > mayor_puntaje:
                mayor_puntaje   = puntos
                mejor_categoria = categoria

    # Caso especial: si TODAS las categorías disponibles darían 0 puntos,
    # elegimos la primera disponible como "sacrificio" (es inevitable).
    # Esto ocurre cuando los dados no encajan en ninguna combinación rentable.
    if mayor_puntaje <= 0:
        for categoria in CATEGORIAS:
            if not categorias_usadas.get(categoria, False):
                mejor_categoria = categoria
                mayor_puntaje   = 0
                break

    return mejor_categoria, mayor_puntaje


# =============================================================================
#  MÓDULO 3 – ESTRATEGIA DE LA IA (Decisión entre Lanzamientos)
#
#  Entre los hasta 3 lanzamientos de un turno, la IA debe decidir
#  qué dados conservar y cuáles relanzar. Esta función implementa
#  esa lógica con una estrategia greedy de prioridades.
# =============================================================================

def decidir_dados_a_guardar(dados):
    """
    Decide qué dados conservar antes de un relanzamiento, según la mejor
    combinación que ya se tenga (estrategia greedy por prioridad).

    JERARQUÍA DE DECISIONES (de mayor a menor prioridad):
    ──────────────────────────────────────────────────────
    Prioridad 1 — 4 o 5 iguales → guardar todos los iguales
                  Objetivo: convertirlos en Yahtzee (5 iguales)
                  Ejemplo: [3,3,3,3,1] → guardar [3,3,3,3], relanzar [1]

    Prioridad 2 — 3 iguales (trío) → guardar los 3
                  Objetivo: conseguir Poker (4 iguales) o Full House
                  Ejemplo: [5,5,5,2,4] → guardar [5,5,5], relanzar [2,4]

    Prioridad 3 — 2 pares → guardar ambos pares
                  Objetivo: conseguir Full House (par + trío)
                  Ejemplo: [4,4,2,2,6] → guardar [4,4,2,2], relanzar [6]

    Prioridad 4 — 1 par → guardar el par
                  Objetivo: conseguir trío o Full House
                  Ejemplo: [6,6,1,3,5] → guardar [6,6], relanzar [1,3,5]

    Prioridad 5 — 4+ valores consecutivos → guardar la secuencia
                  Objetivo: conseguir Escalera Menor o Mayor
                  Ejemplo: [1,2,3,4,6] → guardar [1,2,3,4], relanzar [6]

    Prioridad 6 — Sin combinación clara → guardar solo el dado más alto
                  Objetivo: maximizar puntos en "Chance" como último recurso
                  Ejemplo: [1,3,2,6,4] → guardar [6], relanzar el resto

    Args:
        dados (list[int]): Lista de 5 valores de dados a evaluar

    Returns:
        list[int]: Lista de ÍNDICES (posiciones 0 a 4) de los dados a conservar.
                   Si retorna [0,1,2,3,4], la IA no quiere relanzar ninguno.
    """
    conteo = Counter(dados)  # Frecuencia de cada valor
    frecuencia_maxima = max(conteo.values())

    # ── Prioridad 1: 4 o más dados iguales ────────────────────────────────────
    # Ya tenemos Poker o Yahtzee; guardamos todos los iguales y relanzamos el resto
    if frecuencia_maxima >= 4:
        valor_repetido = [v for v, c in conteo.items() if c == frecuencia_maxima][0]
        return [i for i, d in enumerate(dados) if d == valor_repetido]

    # ── Prioridad 2: Exactamente 3 dados iguales (trío) ───────────────────────
    if frecuencia_maxima == 3:
        valor_trio = [v for v, c in conteo.items() if c == 3][0]
        return [i for i, d in enumerate(dados) if d == valor_trio]

    # ── Prioridad 3: Dos pares distintos ──────────────────────────────────────
    # Buscamos todos los valores que aparecen exactamente 2 veces
    valores_en_par = [v for v, c in conteo.items() if c == 2]
    if len(valores_en_par) == 2:
        # Guardamos los 4 dados que forman los dos pares
        return [i for i, d in enumerate(dados) if d in valores_en_par]

    # ── Prioridad 4: Un solo par ───────────────────────────────────────────────
    if len(valores_en_par) == 1:
        valor_par = valores_en_par[0]
        return [i for i, d in enumerate(dados) if d == valor_par]

    # ── Prioridad 5: Buscar la secuencia consecutiva más larga ────────────────
    # Esto aplica cuando no hay pares ni grupos; buscamos escaleras potenciales
    valores_unicos = sorted(set(dados))

    # Encontramos la secuencia consecutiva más larga entre los valores únicos
    mejor_secuencia = _encontrar_mejor_secuencia(valores_unicos)

    if len(mejor_secuencia) >= 4:
        # Guardamos un dado por cada valor en la secuencia (sin duplicar)
        indices_guardados = []
        valores_ya_incluidos = set()
        for indice, dado in enumerate(dados):
            if dado in mejor_secuencia and dado not in valores_ya_incluidos:
                indices_guardados.append(indice)
                valores_ya_incluidos.add(dado)
        return indices_guardados

    # ── Prioridad 6: Sin combinación útil → guardar solo el dado más alto ─────
    # Como último recurso, conservamos el dado de mayor valor
    # para maximizar los puntos en la categoría "Chance"
    valor_maximo = max(dados)
    primer_indice_max = next(i for i, d in enumerate(dados) if d == valor_maximo)
    return [primer_indice_max]


def _encontrar_mejor_secuencia(valores_unicos):
    """
    Función auxiliar: encuentra la subsecuencia consecutiva más larga
    dentro de una lista de valores ordenados.

    Por ejemplo, en [1, 2, 3, 5, 6]:
      - Secuencia [1,2,3] tiene longitud 3
      - Secuencia [5,6]   tiene longitud 2
      → Retorna [1, 2, 3]

    Args:
        valores_unicos (list[int]): Lista de valores enteros ordenados y sin repetidos

    Returns:
        list[int]: La subsecuencia consecutiva más larga encontrada
    """
    if not valores_unicos:
        return []

    mejor_secuencia   = [valores_unicos[0]]
    secuencia_actual  = [valores_unicos[0]]

    for valor in valores_unicos[1:]:
        if valor == secuencia_actual[-1] + 1:
            # El valor actual es consecutivo al anterior → extendemos la secuencia
            secuencia_actual.append(valor)
        else:
            # La secuencia se rompió → comparamos con la mejor registrada
            if len(secuencia_actual) > len(mejor_secuencia):
                mejor_secuencia = secuencia_actual[:]
            secuencia_actual = [valor]  # Empezamos una nueva secuencia

    # Verificación final: la última secuencia podría ser la mejor
    if len(secuencia_actual) > len(mejor_secuencia):
        mejor_secuencia = secuencia_actual

    return mejor_secuencia


# =============================================================================
#  CLASE JUGADOR
#
#  Encapsula el estado completo de un jugador durante la partida:
#  su marcador, las categorías que ya usó, y su puntaje acumulado.
# =============================================================================

class Jugador:
    """
    Representa a un jugador en el juego Yahtzee.

    Cada jugador tiene un MARCADOR con las 13 categorías del juego.
    Durante la partida, debe ir llenando las categorías UNA por turno.
    Cuando todas están llenas, el juego termina para ese jugador.

    Attributes:
        nombre (str):              Nombre del jugador (para mostrar en pantalla)
        marcador (dict):           Diccionario {categoria: puntaje_obtenido | None}
                                   None significa que todavía no se ha usado esa categoría
        categorias_usadas (dict):  Diccionario {categoria: bool} → True si ya se usó
        puntaje_total (int):       Suma acumulada de todos los puntos del jugador
    """

    def __init__(self, nombre):
        """Inicializa un jugador con marcador vacío y 0 puntos."""
        self.nombre = nombre
        # Al inicio, ninguna categoría tiene puntos (None = sin usar)
        self.marcador = {categoria: None for categoria in CATEGORIAS}
        # Todas las categorías comienzan disponibles (False = no usada)
        self.categorias_usadas = {categoria: False for categoria in CATEGORIAS}
        self.puntaje_total = 0

    def registrar_puntaje(self, categoria, puntos):
        """
        Registra el puntaje obtenido en una categoría y actualiza el total.

        Esta acción es IRREVERSIBLE: una vez registrada, la categoría
        queda marcada como usada y no puede volver a utilizarse.

        Args:
            categoria (str): La categoría donde se registrarán los puntos
            puntos (int): Los puntos obtenidos (puede ser 0 si fue sacrificio)
        """
        self.marcador[categoria]         = puntos
        self.categorias_usadas[categoria] = True
        self.puntaje_total               += puntos

    def categorias_disponibles(self):
        """
        Retorna la lista de categorías que aún no han sido utilizadas.
        
        Returns:
            list[str]: Categorías disponibles en el orden original de CATEGORIAS
        """
        return [c for c in CATEGORIAS if not self.categorias_usadas[c]]

    def juego_terminado(self):
        """
        Verifica si el jugador ya completó todas sus 13 categorías.
        
        Returns:
            bool: True si todas las categorías fueron usadas, False si aún quedan
        """
        return all(self.categorias_usadas.values())


# =============================================================================
#  MÓDULO 4 – INTERFAZ DE TEXTO
#
#  Funciones que formatean y muestran la información del juego en consola.
#  Estas funciones son puramente de visualización, no afectan la lógica.
# =============================================================================

def separador(caracter="─", largo=60):
    """
    Imprime una línea horizontal como separador visual.
    
    Args:
        caracter (str): Carácter a repetir ("─" para divisor suave, "═" para fuerte)
        largo (int): Número de veces que se repite el carácter
    """
    print(caracter * largo)


def mostrar_dados(dados, titulo="Dados actuales"):
    """
    Muestra los dados de forma visual usando caracteres Unicode de dados.

    Los símbolos ⚀⚁⚂⚃⚄⚅ representan las 6 caras de un dado físico,
    haciendo la salida más intuitiva y fácil de leer.

    Args:
        dados (list[int]): Lista de valores de los dados (entre 1 y 6)
        titulo (str): Texto descriptivo a mostrar antes de los dados
    """
    # Diccionario que mapea cada valor numérico a su símbolo de dado
    simbolos_dado = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

    visualizacion_simbolos = " ".join([simbolos_dado[d] for d in dados])
    visualizacion_numeros  = " ".join([f"[{d}]" for d in dados])

    print(f"  {titulo}: {visualizacion_simbolos}  →  {visualizacion_numeros}")


def mostrar_marcador(jugador):
    """
    Muestra el marcador completo de un jugador con todas sus categorías.
    Las categorías ya usadas se marcan con ✓ y muestran sus puntos.
    Las pendientes se muestran como "---".

    Args:
        jugador (Jugador): El jugador cuyo marcador se quiere visualizar
    """
    separador()
    print(f"  📊 MARCADOR DE {jugador.nombre.upper()}")
    separador()

    for categoria in CATEGORIAS:
        valor = jugador.marcador[categoria]

        if valor is not None:
            estado = f"{valor:>3} pts"  # Alinea el número a la derecha
        else:
            estado = "  ---  "           # Categoría pendiente

        icono = "✓" if jugador.categorias_usadas[categoria] else " "
        print(f"  [{icono}] {categoria:<18} {estado}")

    separador()
    print(f"  TOTAL ACUMULADO: {jugador.puntaje_total} puntos")
    separador()


def mostrar_estado_juego(jugadores, turno_actual):
    """
    Muestra un resumen rápido del estado del juego al inicio de cada turno.
    Informa el puntaje actual y cuántas categorías le quedan a cada jugador.

    Args:
        jugadores (list[Jugador]): Lista de jugadores en la partida
        turno_actual (int): Número del turno que está por comenzar
    """
    print("\n" + "═" * 60)
    print(f"  📈 ESTADO DEL JUEGO – TURNO {turno_actual}")
    print("─" * 60)
    for jugador in jugadores:
        categorias_restantes = len(jugador.categorias_disponibles())
        print(f"  {jugador.nombre}: {jugador.puntaje_total} pts  "
              f"({categorias_restantes} categorías por llenar)")
    print("═" * 60)


def mostrar_puntajes_posibles(dados, jugador):
    """
    Muestra los puntajes que se obtendrían con los dados actuales
    para cada categoría que el jugador aún no ha usado.
    Útil para el modo interactivo y para entender las decisiones de la IA.

    Args:
        dados (list[int]): Los 5 dados actuales
        jugador (Jugador): El jugador en turno (para ver sus categorías disponibles)
    """
    print("\n  🎯 Puntajes posibles con estos dados:")
    for categoria in jugador.categorias_disponibles():
        pts = calcular_puntaje(dados, categoria)
        barra_visual = "█" * (pts // 5) if pts > 0 else "·"  # Barra proporcional
        print(f"     {categoria:<18} = {pts:>3} pts  {barra_visual}")


# =============================================================================
#  MÓDULO 5 – LÓGICA DEL TURNO
#
#  Coordina el flujo completo de un turno: lanzamiento inicial, decisiones
#  de relanzamiento, y registro del puntaje en el marcador.
# =============================================================================

def ejecutar_turno(jugador, num_turno, modo_auto=True, estadisticas=None):
    """
    Ejecuta un turno completo para un jugador.

    FLUJO DE UN TURNO EN YAHTZEE:
    ──────────────────────────────
    1. Lanzamiento inicial: Se lanzan TODOS los dados (obligatorio)
    2. Decisión de relanzamiento 1: ¿Qué dados guardar? Relanzar los demás
    3. Decisión de relanzamiento 2: ¿Qué dados guardar? Relanzar los demás
       (Los pasos 2 y 3 son opcionales; la IA puede elegir no relanzar si ya tiene buena combinación)
    4. Registro: Se elige la categoría donde anotar los puntos (irreversible)

    Modos de juego:
    ---------------
    - modo_auto=True:  La IA controla todo (usado en la simulación Montecarlo)
    - modo_auto=False: El jugador humano toma las decisiones (interactivo)

    Args:
        jugador (Jugador): El jugador que va a ejecutar el turno
        num_turno (int): Número del turno actual (para mostrar en pantalla)
        modo_auto (bool): Si True, la IA decide automáticamente
        estadisticas (dict | None): Si se proporciona, acumula datos del turno
                                    para el análisis Montecarlo posterior

    Returns:
        tuple: (categoria_elegida, puntos_obtenidos, dados_finales)
    """
    separador("─")
    print(f"\n  🎲 TURNO {num_turno} – {jugador.nombre.upper()}")
    separador("─")

    # ── Paso 1: Primer lanzamiento (siempre se lanzan los 5 dados) ────────────
    dados = lanzar_dados()
    print(f"\n  Lanzamiento 1 (inicial – todos los dados al aire):")
    mostrar_dados(dados)

    historial_lanzamientos = [dados.copy()]  # Guardamos el historial para estadísticas

    # ── Pasos 2 y 3: Relanzamientos opcionales ────────────────────────────────
    # MAX_LANZAMIENTOS = 3, por lo que el rango va de lanzamiento 2 al 3
    for numero_lanzamiento in range(2, MAX_LANZAMIENTOS + 1):

        if modo_auto:
            # La IA evalúa los dados y decide cuáles conservar
            indices_a_guardar = decidir_dados_a_guardar(dados)
        else:
            # Modo interactivo: el jugador humano decide
            mostrar_puntajes_posibles(dados, jugador)
            respuesta = input(f"\n  ¿Quieres relanzar dados? (s/n): ").strip().lower()
            if respuesta != 's':
                break  # El jugador elige no relanzar → termina los lanzamientos

            entrada = input("  Índices de dados a GUARDAR (0-4, separados por coma, o ENTER para relanzar todos): ")
            if entrada.strip():
                indices_a_guardar = [int(x.strip()) for x in entrada.split(",")]
            else:
                indices_a_guardar = []  # Relanzar todos

        # Optimización: si la IA quiere guardar TODOS los dados, no hay nada que relanzar
        if len(indices_a_guardar) == NUM_DADOS and modo_auto:
            print(f"  IA mantiene todos los dados — combinación óptima encontrada, no relanza.")
            break

        # Mostramos qué dados se conservan antes de relanzar
        dados_que_se_conservan = [dados[i] for i in indices_a_guardar]
        dados = relanzar_dados(dados, indices_a_guardar)

        print(f"\n  Lanzamiento {numero_lanzamiento} (relanzamiento):")
        if dados_que_se_conservan:
            print(f"  Dados conservados: {dados_que_se_conservan}")
        mostrar_dados(dados)
        historial_lanzamientos.append(dados.copy())

    # ── Paso 4: Selección de categoría y registro del puntaje ─────────────────
    if modo_auto:
        # La IA elige automáticamente la categoría que maximiza el puntaje inmediato
        categoria_elegida, puntos_obtenidos = mejor_categoria_disponible(
            dados, jugador.categorias_usadas
        )
    else:
        # El jugador humano elige la categoría manualmente
        mostrar_puntajes_posibles(dados, jugador)
        print("\n  Categorías disponibles:")
        disponibles = jugador.categorias_disponibles()
        for i, cat in enumerate(disponibles):
            pts_cat = calcular_puntaje(dados, cat)
            print(f"    {i}: {cat:<18} ({pts_cat} pts)")

        indice_elegido = int(input("  Elige el número de la categoría: "))
        categoria_elegida  = disponibles[indice_elegido]
        puntos_obtenidos   = calcular_puntaje(dados, categoria_elegida)

    # Registramos el puntaje en el marcador del jugador (acción irreversible)
    jugador.registrar_puntaje(categoria_elegida, puntos_obtenidos)

    print(f"\n  ✅ Categoría seleccionada: [{categoria_elegida}]  →  {puntos_obtenidos} puntos")
    print(f"  Puntaje acumulado de {jugador.nombre}: {jugador.puntaje_total} pts")

    # ── Registro de estadísticas para análisis Montecarlo ────────────────────
    # Estos datos se usarán después para calcular promedios, distribuciones, etc.
    if estadisticas is not None:
        estadisticas["lanzamientos"].append(len(historial_lanzamientos))
        estadisticas["puntos_por_turno"].append(puntos_obtenidos)
        estadisticas["categorias_elegidas"].append(categoria_elegida)
        estadisticas["dados_finales"].append(dados.copy())

    return categoria_elegida, puntos_obtenidos, dados


# =============================================================================
#  MÓDULO 6 – ANÁLISIS ESTADÍSTICO (Explotación de Resultados Montecarlo)
#
#  Después de simular el juego, analizamos los resultados aleatorios
#  acumulados. Esto es la "explotación" del método de Montecarlo:
#  extraer información probabilística de muchas repeticiones.
# =============================================================================

def analizar_estadisticas(estadisticas_jugadores, puntuaciones_finales):
    """
    Analiza y muestra los resultados estadísticos de una partida simulada.

    ESTO ES MONTECARLO EN ACCIÓN:
    ------------------------------
    Después de simular una partida (o muchas), analizamos la distribución
    de los dados para verificar que efectivamente sigan una distribución
    uniforme, y calculamos métricas de rendimiento de cada jugador.

    La verificación clave es la LEY DE GRANDES NÚMEROS:
    Con suficientes lanzamientos, la frecuencia observada de cada cara
    debería converger a 1/6 ≈ 0.1667. Si hay desviaciones grandes,
    indica un problema con el generador de números aleatorios.

    Args:
        estadisticas_jugadores (list[dict]): Lista de dicts con datos por jugador.
             Cada dict tiene: 'lanzamientos', 'puntos_por_turno',
                              'categorias_elegidas', 'dados_finales'
        puntuaciones_finales (list[int]): Puntaje final de cada jugador [j1, j2]
    """
    separador("═")
    print("\n  📊 ANÁLISIS ESTADÍSTICO – MÉTODO DE MONTECARLO")
    print("  (Explotación de los resultados aleatorios obtenidos)")
    separador("═")

    for indice, (stats, puntaje_final) in enumerate(
        zip(estadisticas_jugadores, puntuaciones_finales)
    ):
        nombre_jugador = f"Jugador {indice + 1}"
        puntos_por_turno  = stats["puntos_por_turno"]
        lanzamientos      = stats["lanzamientos"]

        print(f"\n  🎮 {nombre_jugador.upper()}")
        separador("─", 50)

        # Estadísticas de puntaje
        promedio_por_turno = sum(puntos_por_turno) / len(puntos_por_turno) if puntos_por_turno else 0
        maximo_por_turno   = max(puntos_por_turno) if puntos_por_turno else 0
        minimo_por_turno   = min(puntos_por_turno) if puntos_por_turno else 0

        print(f"  Puntaje final de la partida:    {puntaje_final} pts")
        print(f"  Promedio de puntos por turno:   {promedio_por_turno:.2f} pts")
        print(f"  Mayor puntaje en un turno:      {maximo_por_turno} pts")
        print(f"  Menor puntaje en un turno:      {minimo_por_turno} pts")

        # Estadísticas de lanzamientos
        promedio_lanzamientos = sum(lanzamientos) / len(lanzamientos) if lanzamientos else 0
        print(f"  Promedio de lanzamientos/turno: {promedio_lanzamientos:.2f}  "
              f"(máx posible: {MAX_LANZAMIENTOS})")

        # Categorías más frecuentes en esta partida
        contador_categorias = Counter(stats["categorias_elegidas"])
        print(f"\n  Categorías más usadas en esta partida:")
        for cat, cantidad in contador_categorias.most_common(5):
            barra = "█" * cantidad
            print(f"    {cat:<18} x{cantidad}  {barra}")

        # ── VERIFICACIÓN DE LA DISTRIBUCIÓN UNIFORME ─────────────────────────
        # Juntamos todos los dados finales de todos los turnos en una sola lista
        # y contamos cuántas veces apareció cada cara (1 al 6)
        todos_los_dados = [dado for sublista in stats["dados_finales"] for dado in sublista]
        distribucion_observada = Counter(todos_los_dados)
        total_dados_lanzados   = len(todos_los_dados)

        print(f"\n  Verificación de distribución uniforme ({total_dados_lanzados} dados registrados):")
        print(f"  Cara │ Freq.Obs.│ Freq.Esp.│ Diferencia")
        print(f"  ─────┼──────────┼──────────┼───────────")

        for cara in range(1, CARAS_DADO + 1):
            freq_observada = distribucion_observada.get(cara, 0) / total_dados_lanzados
            freq_esperada  = 1 / CARAS_DADO  # = 1/6 ≈ 0.1667
            diferencia     = freq_observada - freq_esperada
            signo          = "+" if diferencia >= 0 else "-"

            print(f"    [{cara}]  │  {freq_observada:.4f}  │  {freq_esperada:.4f}  │  "
                  f"{signo}{abs(diferencia):.4f}")

    # Nota de interpretación de los resultados
    print("\n  📌 INTERPRETACIÓN (Ley de Grandes Números):")
    print("  Con más turnos y simulaciones, la columna 'Diferencia' se acercará")
    print("  a 0.0000, confirmando la distribución uniforme discreta del dado.")
    print("  Esto es la base matemática que valida el Método de Montecarlo.")
    separador("═")


# =============================================================================
#  MÓDULO 7 – SIMULACIÓN MÚLTIPLE (Montecarlo Puro)
#
#  Este es el corazón del método de Montecarlo:
#  repetir el experimento N veces para estimar probabilidades y distribuciones
#  que serían muy difíciles de calcular analíticamente.
# =============================================================================

def simular_n_partidas(n=1000):
    """
    Ejecuta N partidas completas en modo silencioso y analiza los resultados.

    POR QUÉ REPETIR MUCHAS VECES (Método de Montecarlo):
    ───────────────────────────────────────────────────────
    Una sola partida de Yahtzee está dominada por la suerte.
    Al simular 1000 partidas, obtenemos estimaciones confiables de:
    - Probabilidad de ganar para cada jugador (~50% esperado)
    - Distribución típica de puntajes
    - Puntaje promedio, mínimo y máximo alcanzable

    Con N=1000 y ~13 turnos por jugador, se generan aproximadamente:
        1000 × 13 × 3 × 5 = 195,000 lanzamientos por jugador
    Suficientes para verificar la Ley de Grandes Números.

    Args:
        n (int): Número de partidas a simular (recomendado: 1000 o más)

    Returns:
        dict: Diccionario con estadísticas agregadas de las N simulaciones.
              Incluye victorias, puntajes (promedio, max, min, mediana) y empates.
    """
    print(f"\n  🔬 INICIANDO SIMULACIÓN MONTECARLO: {n} partidas...")
    print(f"  (Modo silencioso — sin mostrar detalles de cada partida)")

    victorias_por_jugador = [0, 0]
    empates               = 0
    puntajes_por_jugador  = [[], []]  # Lista de puntajes de cada partida, por jugador

    inicio_tiempo = time.time()

    for numero_partida in range(n):
        # ── Crear 2 jugadores temporales para esta partida ────────────────────
        j1 = Jugador("J1")
        j2 = Jugador("J2")
        jugadores_sim = [j1, j2]

        # ── Simular la partida completa en modo silencioso ────────────────────
        # Cada jugador juega hasta que no le queden categorías disponibles
        while not all(jugador.juego_terminado() for jugador in jugadores_sim):
            for jugador in jugadores_sim:
                if not jugador.juego_terminado():
                    # Lanzamiento inicial del turno
                    dados = lanzar_dados()

                    # Hasta 2 relanzamientos adicionales (total máx 3 lanzamientos)
                    for _ in range(MAX_LANZAMIENTOS - 1):
                        indices = decidir_dados_a_guardar(dados)
                        # Si la IA quiere guardar todos, no relanza
                        if len(indices) == NUM_DADOS:
                            break
                        dados = relanzar_dados(dados, indices)

                    # Seleccionar la mejor categoría y registrar el puntaje
                    categoria, puntos = mejor_categoria_disponible(
                        dados, jugador.categorias_usadas
                    )
                    jugador.registrar_puntaje(categoria, puntos)

        # ── Determinar el resultado de esta partida ────────────────────────────
        puntaje_j1 = j1.puntaje_total
        puntaje_j2 = j2.puntaje_total

        puntajes_por_jugador[0].append(puntaje_j1)
        puntajes_por_jugador[1].append(puntaje_j2)

        if puntaje_j1 > puntaje_j2:
            victorias_por_jugador[0] += 1
        elif puntaje_j2 > puntaje_j1:
            victorias_por_jugador[1] += 1
        else:
            empates += 1

    duracion_total = time.time() - inicio_tiempo

    # ── Calcular estadísticas agregadas de las N partidas ─────────────────────
    resultados = {}
    for i in range(2):
        pts = puntajes_por_jugador[i]
        puntajes_ordenados = sorted(pts)

        resultados[f"jugador_{i+1}"] = {
            "victorias":        victorias_por_jugador[i],
            "pct_victorias":    victorias_por_jugador[i] / n * 100,
            "puntaje_medio":    sum(pts) / n,
            "puntaje_max":      max(pts),
            "puntaje_min":      min(pts),
            "puntaje_mediana":  puntajes_ordenados[n // 2],
        }

    resultados["empates"]         = empates
    resultados["pct_empates"]     = empates / n * 100
    resultados["n_simulaciones"]  = n
    resultados["duracion_seg"]    = duracion_total

    print(f"  ✓ Simulación completada en {duracion_total:.2f} segundos.")
    return resultados


def mostrar_resultados_simulacion(resultados):
    """
    Muestra de forma legible los resultados de la simulación Montecarlo múltiple.

    Presenta las métricas estadísticas clave y la interpretación de resultados
    en el contexto del método de Montecarlo y la Ley de Grandes Números.

    Args:
        resultados (dict): Diccionario retornado por simular_n_partidas()
    """
    n = resultados["n_simulaciones"]
    separador("═")
    print(f"  🎰 RESULTADOS – SIMULACIÓN MONTECARLO ({n} partidas)")
    separador("═")

    for i in range(1, 3):
        datos = resultados[f"jugador_{i}"]
        print(f"\n  Jugador {i}:")
        print(f"    Victorias obtenidas:  {datos['victorias']} de {n}  "
              f"({datos['pct_victorias']:.1f}%)")
        print(f"    Puntaje promedio:     {datos['puntaje_medio']:.1f} pts")
        print(f"    Puntaje máximo:       {datos['puntaje_max']} pts")
        print(f"    Puntaje mínimo:       {datos['puntaje_min']} pts")
        print(f"    Mediana de puntaje:   {datos['puntaje_mediana']} pts")

    print(f"\n  Empates: {resultados['empates']}  ({resultados['pct_empates']:.1f}%)")
    print(f"  Tiempo total de simulación: {resultados['duracion_seg']:.2f} segundos")
    separador("═")

    # Interpretación en el contexto del método de Montecarlo
    pct_j1 = resultados['jugador_1']['pct_victorias']
    pct_j2 = resultados['jugador_2']['pct_victorias']

    print("\n  💡 INTERPRETACIÓN – MÉTODO DE MONTECARLO:")
    print(f"  Ambos jugadores usan la misma estrategia greedy, por lo que")
    print(f"  teóricamente deberían tener probabilidades de victoria ~50%.")
    print(f"  Resultado observado: J1={pct_j1:.1f}%  vs  J2={pct_j2:.1f}%")
    print(f"  La diferencia residual se debe a la variabilidad estadística")
    print(f"  inherente a una muestra finita de {n} partidas.")
    print(f"  Con N→∞, ambos porcentajes convergerían exactamente al 50%")
    print(f"  (asumiendo estrategia simétrica). Esto ilustra la LGN.")
    separador("═")


# =============================================================================
#  MÓDULO 8 – PARTIDA COMPLETA CON VISUALIZACIÓN
#
#  Coordina la ejecución de una partida completa mostrando todos los detalles
#  turno a turno. Esta es la "Parte 1" del programa.
# =============================================================================

def jugar_partida():
    """
    Ejecuta y visualiza una partida completa de Yahtzee entre 2 jugadores (IA vs IA).

    Esta partida sirve como DEMOSTRACIÓN DETALLADA del funcionamiento del juego
    y del método de Montecarlo en acción, mostrando cada lanzamiento, cada
    decisión de la IA, y cada registro de puntaje.

    Cuando todas las categorías de ambos jugadores están llenas,
    la partida termina y se muestran los resultados finales.

    Returns:
        tuple: (lista_de_jugadores, lista_de_estadisticas)
               Las estadísticas acumuladas sirven para el análisis posterior.
    """
    separador("═")
    print("  🎲 YAHTZEE – DEMOSTRACIÓN CON MÉTODO DE MONTECARLO")
    print("  Distribución de cada dado: Uniforme{1,2,3,4,5,6}")
    print("  Probabilidad de cada cara: P(X=k) = 1/6 para k ∈ {1,...,6}")
    separador("═")

    # Inicializar jugadores y sus diccionarios de estadísticas
    jugadores = [Jugador("Jugador 1"), Jugador("Jugador 2")]

    estadisticas = [
        {
            "lanzamientos":       [],   # Cuántos lanzamientos usó en cada turno
            "puntos_por_turno":   [],   # Puntos obtenidos en cada turno
            "categorias_elegidas":[],   # Qué categoría eligió en cada turno
            "dados_finales":      []    # Estado final de los dados en cada turno
        }
        for _ in jugadores
    ]

    turno_actual = 1

    # La partida continúa mientras algún jugador tenga categorías disponibles
    while not all(jugador.juego_terminado() for jugador in jugadores):
        mostrar_estado_juego(jugadores, turno_actual)

        # Cada jugador ejecuta su turno si aún le quedan categorías
        for indice, jugador in enumerate(jugadores):
            if not jugador.juego_terminado():
                ejecutar_turno(
                    jugador,
                    num_turno=turno_actual,
                    modo_auto=True,
                    estadisticas=estadisticas[indice]
                )
                time.sleep(0.05)  # Pequeña pausa para que la salida sea más legible

        turno_actual += 1

    return jugadores, estadisticas


def mostrar_resultado_final(jugadores, estadisticas):
    """
    Muestra el marcador final completo y el análisis estadístico de la partida.

    Args:
        jugadores (list[Jugador]): Los 2 jugadores al final de la partida
        estadisticas (list[dict]): Estadísticas acumuladas durante la partida
    """
    separador("═")
    print("\n  🏆 RESULTADO FINAL DE LA PARTIDA")
    separador("═")

    # Mostrar el marcador completo de cada jugador
    for jugador in jugadores:
        mostrar_marcador(jugador)

    # Determinar el ganador
    puntaje_j1 = jugadores[0].puntaje_total
    puntaje_j2 = jugadores[1].puntaje_total

    print("\n  RESUMEN DE PUNTAJES:")
    for jugador in jugadores:
        # Barra visual proporcional al puntaje (1 bloque cada 10 puntos)
        barra = "█" * (jugador.puntaje_total // 10)
        print(f"  {jugador.nombre}: {jugador.puntaje_total:>4} pts  {barra}")

    print()
    if puntaje_j1 > puntaje_j2:
        diferencia = puntaje_j1 - puntaje_j2
        print(f"  🥇 GANADOR: {jugadores[0].nombre}  (ganó por {diferencia} puntos)")
    elif puntaje_j2 > puntaje_j1:
        diferencia = puntaje_j2 - puntaje_j1
        print(f"  🥇 GANADOR: {jugadores[1].nombre}  (ganó por {diferencia} puntos)")
    else:
        print("  🤝 EMPATE — Ambos jugadores obtuvieron el mismo puntaje")

    separador("═")

    # Análisis estadístico de esta partida individual
    analizar_estadisticas(estadisticas, [j.puntaje_total for j in jugadores])


# =============================================================================
#  PUNTO DE ENTRADA DEL PROGRAMA
#
#  Cuando ejecutas este archivo con "python yahtzee.py", Python corre
#  el bloque if __name__ == "__main__". Aquí se coordinan las dos partes:
#    Parte 1: Una partida completa visualizada en detalle
#    Parte 2: 1000 partidas en modo silencioso para análisis estadístico
# =============================================================================

if __name__ == "__main__":
    print("\n" + "═" * 60)
    print("  MÉTODO DE MONTECARLO – SIMULACIÓN YAHTZEE")
    print("  Institución Universitaria | Simulación y Modelado – 2025")
    print("═" * 60)

    # Fijamos una semilla aleatoria para que los resultados sean REPRODUCIBLES.
    # Con seed=42, siempre se obtiene la misma secuencia de números aleatorios.
    # Para resultados diferentes cada ejecución, comenta o elimina esta línea.
    random.seed(42)

    # ── PARTE 1: Partida completa con visualización detallada ─────────────────
    print("\n  ► PARTE 1: PARTIDA COMPLETA (con seguimiento turno a turno)")
    print("  Objetivo: ver cómo funciona el juego y cómo actúa la IA greedy.\n")

    jugadores, estadisticas = jugar_partida()
    mostrar_resultado_final(jugadores, estadisticas)

    # ── PARTE 2: Simulación Montecarlo con N=1000 partidas ───────────────────
    print("\n  ► PARTE 2: SIMULACIÓN MONTECARLO (1000 partidas en modo silencioso)")
    print("  Objetivo: estimar probabilidades de victoria y distribución de puntajes.")
    print("  Mientras más partidas simulemos, más precisa es la estimación.\n")

    resultados_montecarlo = simular_n_partidas(n=1000)
    mostrar_resultados_simulacion(resultados_montecarlo)

    print("\n  ✓ Simulación completada exitosamente.")
    print("═" * 60 + "\n")
