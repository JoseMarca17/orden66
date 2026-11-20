"""Pruebas del PSR y de su reparación."""

from orden66.backend.core.csp_solver import generar_cartelera_valida, reparar
from orden66.backend.core.models import Cartelera, Funcion
from orden66.backend.core.validator import validar


def test_generador_psr_produce_carteleras_validas_en_varias_semillas(calendario):
    for semilla in range(10):
        cartelera = generar_cartelera_valida(calendario, semilla)
        assert len(cartelera.funciones) >= 48
        assert validar(cartelera, calendario).es_valida


def test_reparar_corrige_cartelera_corrompida(calendario):
    pelicula = calendario.peliculas[0]
    corrompida = Cartelera([Funcion(pelicula, "S6", 0, 600), Funcion(pelicula, "S1", 0, 600)])
    reparada = reparar(corrompida, calendario, semilla=17)
    assert validar(reparada, calendario).es_valida
    assert len(reparada.funciones) >= 48
