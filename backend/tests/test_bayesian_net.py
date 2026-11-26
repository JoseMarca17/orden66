"""Pruebas de entrenamiento, predicción y aprendizaje en línea."""

import pytest

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


def test_forma_de_la_tabla_sigue_el_orden_de_los_ejes():
    # clase, tipo_dia, franja, feriado, promoción, tipo_pelicula, semana, capacidad, simultáneas
    assert RedBayesiana().conteos.shape == (3, 3, 3, 2, 2, 4, 3, 3, 2)


def test_noche_nacional_sala_grande_no_comparte_celda_con_tarde_extranjera_mediana():
    red = RedBayesiana()
    noche = {"dia": 5, "inicio": 1200, "tipo": "nacional", "capacidad": 240, "semana": 1}
    tarde = {"dia": 5, "inicio": 960, "tipo": "otra_extranjera", "capacidad": 140, "semana": 1}
    i_noche, i_tarde = red._indice(noche), red._indice(tarde)
    assert i_noche[1] == 2 and i_tarde[1] == 1   # franja: noche ≠ tarde
    assert i_noche[4] == 3 and i_tarde[4] == 2   # tipo: nacional ≠ extranjera
    assert i_noche[6] == 2 and i_tarde[6] == 1   # capacidad: grande ≠ mediana
    red.entrenar([dict(noche, clase="alta")] * 5)
    assert red.probabilidades(noche)[2] > red.probabilidades(tarde)[2]


def test_valor_fuera_de_rango_es_error_y_no_se_recorta():
    with pytest.raises(ValueError):
        RedBayesiana()._indice({"dia": 0, "inicio": 600, "tipo": 7, "capacidad": 80})


def test_simultanea_usa_su_propio_eje(calendario):
    red = RedBayesiana(); funcion = Funcion(calendario.peliculas[3], "S6", 5, 1200)
    red.actualizar_con_ventas([(funcion, 190, 1)] * 3, calendario)
    assert red.probabilidades(funcion, calendario, simultaneas=1)[2] > red.probabilidades(funcion, calendario, simultaneas=0)[2]
