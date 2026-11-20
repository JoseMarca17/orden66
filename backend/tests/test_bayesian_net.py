"""Pruebas de entrenamiento, predicción y aprendizaje en línea."""

from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.models import Funcion


def registro(clase, i=0):
    return {"dia": i % 7, "inicio": 1200, "feriado": 0, "promocion": 0, "tipo": "superheroes_accion", "semana": 1, "capacidad": 240, "simultaneas": 0, "clase": clase}


def test_entrenamiento_80_20_y_metricas():
    datos = [registro("alta", i) for i in range(80)] + [registro("media", i) for i in range(20)]
    red = RedBayesiana(); red.entrenar(datos[:80])
    metricas = red.metricas(datos[80:])
    assert red.conteos.sum() == 80
    assert 0 <= metricas["exactitud"] <= 1
    assert metricas["log_loss"] >= 0
    assert "exactitud_base" in metricas


def test_ocupacion_esperada_usa_laplace_y_capacidad():
    red = RedBayesiana(); dato = registro("alta")
    assert 0.15 <= red.ocupacion_esperada(dato) <= 0.80
    assert 0 < red.esperados(dato) <= 240


def test_actualizar_con_ventas_aumenta_probabilidad_de_alta(calendario):
    red = RedBayesiana(); funcion = Funcion(calendario.peliculas[3], "S6", 0, 1200)
    antes = red.probabilidades(funcion, calendario)[2]
    red.actualizar_con_ventas([(funcion, 190), (funcion, 190), (funcion, 190)], calendario)
    despues = red.probabilidades(funcion, calendario)[2]
    assert despues > antes
