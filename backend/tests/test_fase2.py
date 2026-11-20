from orden66.backend.core import config
from orden66.backend.core.csp_solver import generar_cartelera_valida, reparar
from orden66.backend.core.models import Calendario, Funcion, Pelicula, Sala, Cartelera
from orden66.backend.core.validator import validar


def calendario():
    return Calendario.crear(
        [Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS],
        [Pelicula(*p) for p in config.PELICULAS_BASE],
    )


def test_psr_genera_100_carteleras_validas():
    c = calendario()
    for semilla in range(100):
        cartelera = generar_cartelera_valida(c, semilla)
        resultado = validar(cartelera, c)
        assert resultado.es_valida, (semilla, resultado.errores)
        assert len(cartelera.funciones) >= 48


def test_reparacion_corrige_funciones_corruptas():
    c = calendario()
    p = c.peliculas[0]
    corrupta = Cartelera([Funcion(p, "S6", 0, 600), Funcion(p, "S1", 0, 600)])
    reparada = reparar(corrupta, c, semilla=42)
    assert validar(reparada, c).es_valida
    assert len(reparada.funciones) >= 48
