"""Parámetros únicos de configuración del dominio."""

from dataclasses import dataclass

DIAS = tuple(range(7))
INICIOS = tuple(range(600, 1321, 30))
CIERRE = 1440
LIMPIEZA = 20
MIN_FUNCIONES_PELICULA = 4
MAX_FUNCIONES_DIA = 8
MAX_FUNCIONES_SEMANA = 30

# Funciones simultáneas: otra función de la misma película, el mismo día, en otra sala,
# que empieza a VENTANA_SIMULTANEA minutos o menos. Se reparten el público (×FACTOR_SIMULTANEA).
VENTANA_SIMULTANEA = 60
FACTOR_SIMULTANEA = 0.65
# El historial simulado se agrupa en "semanas" de este tamaño (el objetivo de relleno del PSR)
# para poder calcular qué funciones son simultáneas entre sí.
FUNCIONES_POR_SEMANA_HISTORIAL = 140
# Calendario de cada semana del historial: cada día es feriado con esta probabilidad, y
# una fracción de las semanas tiene promoción de lunes a miércoles. Así la red ve ejemplos
# de feriados y promociones (antes nunca los veía y en E2/E3 predecía el prior uniforme).
PROB_FERIADO_HISTORIAL = 0.08
PROB_SEMANA_PROMOCION_HISTORIAL = 0.15
DIAS_PROMOCION_HISTORIAL = (0, 1, 2)

POBLACION_AG = 50
GENERACIONES_AG = 100
PARADA_SIN_MEJORA = 25
P_CRUCE = 0.8
P_MUTACION = 0.2
ELITISMO = 2
TORNEO_K = 3
LAMBDA = 25.0
# Una función está "en riesgo" (y U(C) resta LAMBDA) cuando la red le asigna P(baja) > UMBRAL_RIESGO.
# Antes se penalizaba la ocupación esperada < 0.20, pero esa esperanza nunca baja de 0.15
# (valor de la clase "baja") y casi no se activaba.
UMBRAL_RIESGO = 0.5
VALORES_CLASE = (0.15, 0.45, 0.80)  # ocupación representativa de baja, media y alta

TIPOS_DIA = ("laborable", "viernes", "fin_de_semana")
FRANJAS = ("matine", "tarde", "noche")
CLASES_OCUPACION = ("baja", "media", "alta")


@dataclass(frozen=True)
class ConfigSala:
    id: str
    capacidad: int
    formatos: frozenset[str]


SALAS = (
    ConfigSala("S1", 80, frozenset({"2D"})),
    ConfigSala("S2", 80, frozenset({"2D"})),
    ConfigSala("S3", 140, frozenset({"2D", "3D"})),
    ConfigSala("S4", 140, frozenset({"2D", "3D"})),
    ConfigSala("S5", 240, frozenset({"2D", "3D"})),
    ConfigSala("S6", 200, frozenset({"XD", "3D"})),
)

PELICULAS_BASE = (
    ("P01", "La Estrella Perdida", 95, "TP", "2D", "familiar_animada", 1),
    ("P02", "Guardianes del Bosque", 105, "TP", "3D", "familiar_animada", 2),
    ("P03", "Planeta de Papel", 100, "TP", "2D", "familiar_animada", 3),
    ("P04", "Titán Cósmico", 150, "+13", "XD", "superheroes_accion", 1),
    ("P05", "Héroes del Amanecer", 140, "+13", "3D", "superheroes_accion", 2),
    ("P06", "Código Invencible", 125, "+13", "2D", "superheroes_accion", 3),
    ("P07", "La Última Señal", 110, "+18", "2D", "otra_extranjera", 1),
    ("P08", "Ciudad de Niebla", 130, "+13", "2D", "otra_extranjera", 2),
    ("P09", "Horizonte Azul", 120, "+13", "3D", "otra_extranjera", 1),
    ("P10", "Ecos de Medianoche", 135, "+18", "2D", "otra_extranjera", 3),
    ("P11", "Voces de Bolivia", 115, "+13", "2D", "nacional", 2),
    ("P12", "El Camino de Sal", 98, "TP", "2D", "nacional", 1),
)

DEMANDA_BASE = {"familiar_animada": 70, "superheroes_accion": 90, "otra_extranjera": 50, "nacional": 40}
