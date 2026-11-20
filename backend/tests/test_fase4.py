from orden66.backend.core import config
from orden66.backend.core.agent import AgenteOrden66
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.genetic_algo import utilidad
from orden66.backend.core.models import Calendario, Pelicula, Sala
from orden66.backend.core.validator import validar


def calendario():
    return Calendario.crear([Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS], [Pelicula(*p) for p in config.PELICULAS_BASE])


def test_agente_devuelve_cartelera_valida_y_curva():
    c = calendario(); mejor, curva = AgenteOrden66(c, RedBayesiana()).generar(3, generaciones=3)
    assert validar(mejor, c).es_valida
    assert len(mejor.funciones) >= 48
    assert curva


def test_agente_es_reproducible():
    c = calendario(); a = AgenteOrden66(c, RedBayesiana())
    uno, curva_uno = a.generar(9, generaciones=1)
    dos, curva_dos = AgenteOrden66(c, RedBayesiana()).generar(9, generaciones=1)
    assert sorted(f.clave for f in uno.funciones) == sorted(f.clave for f in dos.funciones)
    assert curva_uno == curva_dos
