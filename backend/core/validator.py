"""Verificación independiente de restricciones R1 a R7."""

from collections import Counter
from dataclasses import dataclass
from . import config
from .models import Calendario, Cartelera


@dataclass
class ResultadoValidacion:
    restricciones: dict[str, bool]
    errores: dict[str, list[str]]

    @property
    def porcentaje(self) -> float:
        return 100 * sum(self.restricciones.values()) / len(self.restricciones)

    @property
    def es_valida(self) -> bool:
        return all(self.restricciones.values())


def validar(cartelera: Cartelera, calendario: Calendario) -> ResultadoValidacion:
    errores = {f"R{i}": [] for i in range(1, 8)}
    salas = {s.id: s for s in calendario.salas}
    por_pelicula = Counter(f.pelicula.id for f in cartelera.funciones)
    por_dia_pelicula = Counter((f.dia, f.pelicula.id) for f in cartelera.funciones)
    posiciones = Counter((f.pelicula.id, f.sala, f.dia, f.inicio) for f in cartelera.funciones)

    for f in cartelera.funciones:
        sala = salas.get(f.sala)
        if sala is None or f.pelicula.formato not in sala.formatos:
            errores["R1"].append(f.clave)
        if f.pelicula.clasificacion == "+18" and f.inicio < 1080:
            errores["R2"].append(f.clave)
        if f.inicio < config.INICIOS[0] or f.fin > config.CIERRE:
            errores["R3"].append(f.clave)
        if posiciones[f.clave] != 1:
            errores["R7"].append(f.clave)

    for i, a in enumerate(cartelera.funciones):
        for b in cartelera.funciones[i + 1:]:
            if a.sala == b.sala and a.dia == b.dia and not (a.fin + config.LIMPIEZA <= b.inicio or b.fin + config.LIMPIEZA <= a.inicio):
                errores["R4"].append((a.clave, b.clave))

    for pelicula in calendario.peliculas:
        if por_pelicula[pelicula.id] < config.MIN_FUNCIONES_PELICULA:
            errores["R5"].append(pelicula.id)
        if any(n > config.MAX_FUNCIONES_DIA for (d, p), n in por_dia_pelicula.items() if p == pelicula.id):
            errores["R6"].append(f"dia:{pelicula.id}")
        if por_pelicula[pelicula.id] > config.MAX_FUNCIONES_SEMANA:
            errores["R6"].append(f"semana:{pelicula.id}")
    conteo_sala_dia = Counter((f.sala, f.dia) for f in cartelera.funciones)
    errores["R6"].extend((s, d) for (s, d), n in conteo_sala_dia.items() if n > config.MAX_FUNCIONES_DIA)
    restricciones = {clave: not valores for clave, valores in errores.items()}
    return ResultadoValidacion(restricciones, errores)


def porcentaje_restricciones(cartelera: Cartelera, calendario: Calendario) -> float:
    return validar(cartelera, calendario).porcentaje
