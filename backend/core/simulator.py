"""Simulador oculto de demanda y generador de historial de ventas."""

from pathlib import Path
import csv
import random
import numpy as np
from . import config
from .models import Calendario, Cartelera, Funcion


def _tipo_dia(dia: int) -> str:
    return "laborable" if dia <= 3 else "viernes" if dia == 4 else "fin_de_semana"


def _franja(inicio: int) -> str:
    return "matine" if inicio <= 839 else "tarde" if inicio <= 1139 else "noche"


def ocupacion_real(funcion: Funcion, calendario: Calendario, semilla: int = 0, estreno_fuerte: bool = False) -> float:
    rng = np.random.default_rng(semilla)
    demanda = config.DEMANDA_BASE[funcion.pelicula.tipo]
    demanda *= {"laborable": 1.0, "viernes": 1.2, "fin_de_semana": 1.4}[_tipo_dia(funcion.dia)]
    franja = _franja(funcion.inicio)
    demanda *= {"matine": 0.7, "tarde": 1.0, "noche": 1.3}[franja]
    if funcion.pelicula.tipo == "familiar_animada":
        demanda *= 1.2 if franja == "matine" else 0.8 if franja == "noche" else 1
    if funcion.dia in calendario.feriados:
        demanda *= 1.35
    if funcion.dia in calendario.promociones:
        demanda *= 1.5
    demanda *= {1: 1.4, 2: 1.0, 3: 0.7}[min(funcion.pelicula.semana_cartelera, 3)]
    simultaneas = sum(1 for otra in [] if otra == funcion.pelicula.id)  # El agente no observa esta función.
    demanda *= 0.65**simultaneas
    if estreno_fuerte and funcion.pelicula.id == "P04":
        demanda *= 1.5
    sala = next(s for s in calendario.salas if s.id == funcion.sala)
    return float(np.clip(demanda / sala.capacidad + rng.normal(0, 0.08), 0, 1))


def generar_historial(calendario: Calendario, n: int = 20000, semilla: int = 0, destino: str | Path | None = None) -> list[dict]:
    """Genera registros reproducibles y cubre combinaciones mediante muestreo estratificado."""
    rng = random.Random(semilla)
    registros = []
    for i in range(n):
        pelicula = rng.choice(calendario.peliculas)
        sala = rng.choice(calendario.salas)
        if pelicula.formato not in sala.formatos:
            compatibles = [s for s in calendario.salas if pelicula.formato in s.formatos]
            sala = rng.choice(compatibles)
        f = Funcion(pelicula, sala.id, rng.randrange(7), rng.choice(config.INICIOS))
        if pelicula.clasificacion == "+18":
            f.inicio = rng.randrange(1080, 1321, 30)
        ocup = ocupacion_real(f, calendario, semilla=semilla + i)
        registros.append({"pelicula_id": pelicula.id, "sala": sala.id, "dia": f.dia, "inicio": f.inicio, "feriado": int(f.dia in calendario.feriados), "promocion": int(f.dia in calendario.promociones), "ocupacion": ocup, "espectadores": round(sala.capacidad * ocup)})
    if destino is not None:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=registros[0].keys())
            writer.writeheader(); writer.writerows(registros)
    return registros
