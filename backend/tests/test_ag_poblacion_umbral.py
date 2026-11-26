"""Fase 2: población inicial diversa del AG y umbral de riesgo P(baja) > UMBRAL_RIESGO."""

import pytest

from orden66.backend.core import config
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.genetic_algo import AlgoritmoGenetico, utilidad
from orden66.backend.core.models import Cartelera, Funcion
from orden66.backend.core.validator import validar


def test_poblacion_inicial_tiene_50_carteleras_distintas_que_respetan_las_fijas(calendario):
    titan = next(p for p in calendario.peliculas if p.id == "P04")
    fija = Funcion(titan, "S6", 5, 1200)
    poblacion = AlgoritmoGenetico(calendario, RedBayesiana(), semilla=5).poblacion_inicial(fijas=[fija])
    assert len(poblacion) == config.POBLACION_AG
    assert len({tuple(sorted(f.clave for f in c.funciones)) for c in poblacion}) == config.POBLACION_AG
    for cartelera in poblacion:
        assert fija.clave in {f.clave for f in cartelera.funciones}
        assert validar(cartelera, calendario).es_valida


def _red_con_p_baja(calendario, funcion, ventas_bajas):
    red = RedBayesiana()
    red.actualizar_con_ventas([(funcion, 5)] * ventas_bajas, calendario)
    return red


def test_utilidad_penaliza_solo_si_p_baja_supera_el_umbral(calendario):
    funcion = Funcion(calendario.peliculas[0], "S1", 0, 600)
    cartelera = Cartelera([funcion])
    riesgosa = _red_con_p_baja(calendario, funcion, 3)   # P(baja) = 4/6 ≈ 0.67
    segura = _red_con_p_baja(calendario, funcion, 0)     # P(baja) = 1/3
    assert riesgosa.probabilidades(funcion, calendario)[0] > config.UMBRAL_RIESGO
    assert utilidad(cartelera, calendario, riesgosa) == pytest.approx(riesgosa.esperados(funcion, calendario) - config.LAMBDA)
    assert utilidad(cartelera, calendario, segura) == pytest.approx(segura.esperados(funcion, calendario))


def test_umbral_de_riesgo_es_configurable(calendario, monkeypatch):
    funcion = Funcion(calendario.peliculas[0], "S1", 0, 600)
    red = _red_con_p_baja(calendario, funcion, 3)
    monkeypatch.setattr(config, "UMBRAL_RIESGO", 0.9)
    assert utilidad(Cartelera([funcion]), calendario, red) == pytest.approx(red.esperados(funcion, calendario))
