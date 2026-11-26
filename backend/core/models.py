"""Modelos de dominio serializables y sin dependencias de infraestructura."""

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class Pelicula:
    id: str
    titulo: str
    duracion: int
    clasificacion: str
    formato: str
    tipo: str
    semana_cartelera: int


@dataclass(frozen=True)
class Sala:
    id: str
    capacidad: int
    formatos: frozenset[str]


@dataclass
class Funcion:
    pelicula: Pelicula
    sala: str
    dia: int
    inicio: int
    espectadores: int | None = None
    ocupacion_esperada: float | None = None

    @property
    def fin(self) -> int:
        return self.inicio + self.pelicula.duracion

    @property
    def clave(self) -> tuple:
        return (self.pelicula.id, self.sala, self.dia, self.inicio)


@dataclass
class Cartelera:
    funciones: list[Funcion] = field(default_factory=list)

    def por_dia_sala(self, dia: int, sala: str) -> list[Funcion]:
        return sorted((f for f in self.funciones if f.dia == dia and f.sala == sala), key=lambda f: f.inicio)

    def agregar(self, funcion: Funcion) -> None:
        self.funciones.append(funcion)


def calcular_simultaneas(posiciones: list[tuple[str, str, int, int]], ventana: int | None = None) -> list[int]:
    """Marca con 1 cada función que tiene otra de la misma película, el mismo día, en otra sala,
    con inicio a ``ventana`` minutos o menos. ``posiciones`` = (pelicula_id, sala, dia, inicio)."""
    from . import config  # import local: models no depende de config en el resto del módulo
    ventana = config.VENTANA_SIMULTANEA if ventana is None else ventana
    marcas = [0] * len(posiciones)
    grupos: dict[tuple[str, int], list[int]] = {}
    for i, (pelicula, _sala, dia, _inicio) in enumerate(posiciones):
        grupos.setdefault((pelicula, dia), []).append(i)
    for indices in grupos.values():
        for a_pos, a in enumerate(indices):
            for b in indices[a_pos + 1:]:
                if posiciones[a][1] != posiciones[b][1] and abs(posiciones[a][3] - posiciones[b][3]) <= ventana:
                    marcas[a] = marcas[b] = 1
    return marcas


def simultaneas_de(funciones: Iterable[Funcion]) -> list[int]:
    """``calcular_simultaneas`` para funciones de una cartelera (en el mismo orden)."""
    return calcular_simultaneas([(f.pelicula.id, f.sala, f.dia, f.inicio) for f in funciones])


@dataclass(frozen=True)
class Calendario:
    salas: tuple[Sala, ...]
    peliculas: tuple[Pelicula, ...]
    feriados: frozenset[int] = frozenset()
    promociones: frozenset[int] = frozenset()

    @classmethod
    def crear(cls, salas: Iterable[Sala], peliculas: Iterable[Pelicula], **kwargs) -> "Calendario":
        return cls(tuple(salas), tuple(peliculas), **kwargs)
