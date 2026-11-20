import numpy as np
from orden66.backend.core import config
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.models import Calendario, Funcion, Pelicula, Sala


def calendario():
    return Calendario.crear([Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS], [Pelicula(*p) for p in config.PELICULAS_BASE])


def registro(clase):
    return {"dia": 0, "inicio": 600, "feriado": 0, "promocion": 0, "tipo": "nacional", "semana": 1, "capacidad": 80, "simultaneas": 0, "clase": clase}


def test_tabla_y_suavizado_laplace():
    red = RedBayesiana()
    assert red.conteos.shape == (3, 3, 2, 2, 4, 3, 3, 2, 3)
    assert np.allclose(red.probabilidades(registro(0)), [1 / 3] * 3)
    red.entrenar([registro("alta")] * 2)
    assert red.probabilidades(registro(0))[2] > red.probabilidades(registro(0))[0]


def test_actualizacion_por_funcion_y_metricas():
    c = calendario(); red = RedBayesiana()
    f = Funcion(c.peliculas[0], "S1", 0, 600)
    red.actualizar_con_ventas([(f, 70)], c)
    assert red.conteos.sum() == 1
    metricas = red.metricas([registro("alta"), registro("baja")])
    assert {"exactitud", "log_loss", "exactitud_base"} <= metricas.keys()


def test_guardar_y_cargar(tmp_path):
    red = RedBayesiana(); red.entrenar([registro("media")])
    ruta = tmp_path / "modelo_rb.npy"; red.guardar(ruta)
    cargada = RedBayesiana.cargar(ruta)
    assert np.array_equal(red.conteos, cargada.conteos)
