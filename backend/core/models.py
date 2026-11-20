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


@dataclass(frozen=True)
class Calendario:
    salas: tuple[Sala, ...]
    peliculas: tuple[Pelicula, ...]
    feriados: frozenset[int] = frozenset()
    promociones: frozenset[int] = frozenset()

    @classmethod
    def crear(cls, salas: Iterable[Sala], peliculas: Iterable[Pelicula], **kwargs) -> "Calendario":
        return cls(tuple(salas), tuple(peliculas), **kwargs)
