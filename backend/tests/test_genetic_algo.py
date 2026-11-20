"""Pruebas del algoritmo genético y su función de utilidad."""

from orden66.backend.core.agent import AgenteOrden66
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.csp_solver import generar_cartelera_valida
from orden66.backend.core.genetic_algo import utilidad
from orden66.backend.core.validator import validar


def test_mejor_cartelera_no_empeora_y_es_valida(calendario):
    red = RedBayesiana(); inicial = generar_cartelera_valida(calendario, 22)
    utilidad_inicial = utilidad(inicial, calendario, red)
    mejor, curva = AgenteOrden66(calendario, red).generar(22, generaciones=3)
    assert validar(mejor, calendario).es_valida
    assert utilidad(mejor, calendario, red) >= utilidad_inicial
    assert curva[-1] >= curva[0]
