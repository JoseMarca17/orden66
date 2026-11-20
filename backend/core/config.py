"""Parámetros únicos de configuración del dominio."""

from dataclasses import dataclass

DIAS = tuple(range(7))
INICIOS = tuple(range(600, 1321, 30))
CIERRE = 1440
LIMPIEZA = 20
MIN_FUNCIONES_PELICULA = 4
MAX_FUNCIONES_DIA = 8
MAX_FUNCIONES_SEMANA = 30

POBLACION_AG = 50
GENERACIONES_AG = 100
PARADA_SIN_MEJORA = 25
P_CRUCE = 0.8
P_MUTACION = 0.2
ELITISMO = 2
TORNEO_K = 3
LAMBDA = 25.0

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
