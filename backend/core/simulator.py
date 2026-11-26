"""Simulador oculto de demanda y generador de historial de ventas."""

from dataclasses import replace
from pathlib import Path
import csv
import random
import numpy as np
from . import config
from .models import Calendario, Cartelera, Funcion, calcular_simultaneas


def _tipo_dia(dia: int) -> str:
    return "laborable" if dia <= 3 else "viernes" if dia == 4 else "fin_de_semana"


def _franja(inicio: int) -> str:
    return "matine" if inicio <= 839 else "tarde" if inicio <= 1139 else "noche"


def ocupacion_real(funcion: Funcion, calendario: Calendario, semilla: int = 0, estreno_fuerte: bool = False, simultaneas: int = 0) -> float:
    """Ocupación "verdadera" de una función. ``simultaneas`` = 1 si en la misma cartelera hay otra
    función de la misma película, el mismo día, en otra sala y a 60 min o menos (ver ``calcular_simultaneas``)."""
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
    demanda *= config.FACTOR_SIMULTANEA ** int(bool(simultaneas))
    if estreno_fuerte and funcion.pelicula.id == "P04":
        demanda *= 1.5
    sala = next(s for s in calendario.salas if s.id == funcion.sala)
    return float(np.clip(demanda / sala.capacidad + rng.normal(0, 0.08), 0, 1))


def generar_historial(calendario: Calendario, n: int = 20000, semilla: int = 0, destino: str | Path | None = None) -> list[dict]:
    """Genera registros reproducibles y cubre combinaciones mediante muestreo estratificado.

    Las funciones se sortean igual que antes (mismo orden de llamadas al generador) y luego se agrupan
    en semanas de ``FUNCIONES_POR_SEMANA_HISTORIAL``: dentro de cada semana se calcula qué funciones son
    simultáneas, con la misma regla que usan la red y el simulador.

    Cada semana sortea además sus feriados (``PROB_FERIADO_HISTORIAL`` por día) y si tiene promoción
    (``PROB_SEMANA_PROMOCION_HISTORIAL``, en ``DIAS_PROMOCION_HISTORIAL``), con un generador aparte
    derivado de la misma semilla, para no alterar el sorteo de las funciones."""
    rng = random.Random(semilla)
    funciones = []
    for _ in range(n):
        pelicula = rng.choice(calendario.peliculas)
        sala = rng.choice(calendario.salas)
        if pelicula.formato not in sala.formatos:
            compatibles = [s for s in calendario.salas if pelicula.formato in s.formatos]
            sala = rng.choice(compatibles)
        f = Funcion(pelicula, sala.id, rng.randrange(7), rng.choice(config.INICIOS))
        if pelicula.clasificacion == "+18":
            f.inicio = rng.randrange(1080, 1321, 30)
        funciones.append(f)
    rng_calendario = random.Random(f"{semilla}-calendario")
    simultaneas, calendarios = [], []
    tamano = config.FUNCIONES_POR_SEMANA_HISTORIAL
    for desde in range(0, n, tamano):
        semana = funciones[desde:desde + tamano]
        simultaneas += calcular_simultaneas([(f.pelicula.id, f.sala, f.dia, f.inicio) for f in semana])
        feriados = {d for d in config.DIAS if rng_calendario.random() < config.PROB_FERIADO_HISTORIAL}
        promociones = set(config.DIAS_PROMOCION_HISTORIAL) if rng_calendario.random() < config.PROB_SEMANA_PROMOCION_HISTORIAL else set()
        calendario_semana = replace(calendario, feriados=calendario.feriados | feriados, promociones=calendario.promociones | promociones)
        calendarios += [calendario_semana] * len(semana)
    capacidades = {s.id: s.capacidad for s in calendario.salas}
    registros = []
    for i, (f, simultanea, cal) in enumerate(zip(funciones, simultaneas, calendarios)):
        ocup = ocupacion_real(f, cal, semilla=semilla + i, simultaneas=simultanea)
        registros.append({"pelicula_id": f.pelicula.id, "sala": f.sala, "dia": f.dia, "inicio": f.inicio, "feriado": int(f.dia in cal.feriados), "promocion": int(f.dia in cal.promociones), "simultaneas": simultanea, "ocupacion": ocup, "espectadores": round(capacidades[f.sala] * ocup)})
    if destino is not None:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        with destino.open("w", newline="", encoding="utf-8") as archivo:
            writer = csv.DictWriter(archivo, fieldnames=registros[0].keys())
            writer.writeheader(); writer.writerows(registros)
    return registros
