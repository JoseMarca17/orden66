"""Funciones simultáneas: misma película, mismo día, otra sala, inicio a 60 min o menos."""

import csv

from orden66.backend.core import config
from orden66.backend.core.models import Calendario, Cartelera, Funcion, calcular_simultaneas, simultaneas_de
from orden66.backend.core.simulator import generar_historial, ocupacion_real


def test_regla_de_simultaneas():
    posiciones = [
        ("P01", "S1", 0, 600),   # 0: con 1 (otra sala, 60 min)
        ("P01", "S2", 0, 660),   # 1: con 0
        ("P01", "S3", 0, 721),   # 2: a 61 min de 1 → no
        ("P02", "S4", 0, 600),   # 3: otra película → no
        ("P01", "S5", 1, 600),   # 4: otro día → no
        ("P03", "S1", 2, 600),   # 5 y 6: misma sala → no
        ("P03", "S1", 2, 630),
    ]
    assert calcular_simultaneas(posiciones) == [1, 1, 0, 0, 0, 0, 0]


def test_simulador_reduce_la_demanda_si_es_simultanea(calendario):
    funcion = Funcion(calendario.peliculas[3], "S6", 5, 1200)
    sola = ocupacion_real(funcion, calendario, semilla=1, simultaneas=0)
    compartida = ocupacion_real(funcion, calendario, semilla=1, simultaneas=1)
    assert compartida < sola


def test_simultaneas_de_una_cartelera(calendario):
    p = calendario.peliculas[0]
    cartelera = Cartelera([Funcion(p, "S1", 0, 600), Funcion(p, "S2", 0, 630), Funcion(p, "S1", 1, 600)])
    assert simultaneas_de(cartelera.funciones) == [1, 1, 0]


def test_historial_incluye_simultaneas(tmp_path, calendario):
    registros = generar_historial(calendario, n=config.FUNCIONES_POR_SEMANA_HISTORIAL * 3, semilla=0, destino=tmp_path / "h.csv")
    assert {r["simultaneas"] for r in registros} == {0, 1}
    with (tmp_path / "h.csv").open(encoding="utf-8") as archivo:
        assert "simultaneas" in next(csv.reader(archivo))
