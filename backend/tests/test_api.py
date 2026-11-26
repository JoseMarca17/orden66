"""Fase 3: API. Sin httpx no hay TestClient, así que se llaman las funciones de los endpoints."""

import json

import pytest

pytest.importorskip("fastapi")
from fastapi import HTTPException

from orden66.backend import api
from orden66.backend.core import config


def test_red_compartida_cargada_con_la_forma_nueva():
    diagnostico = api.health_rb()
    assert diagnostico["entrenada"] is True
    assert diagnostico["forma"] == [3, 3, 3, 2, 2, 4, 3, 3, 2]
    assert diagnostico["total_conteos"] > 0


def test_parametros_del_cuerpo_tienen_prioridad_y_el_escenario_suma_dias():
    p = api.resolver_parametros({"escenario": "E2", "promociones": [0], "semilla": 4}, semilla_query=9, generaciones_query=5)
    assert p == {"escenario": "E2", "feriados": [4], "promociones": [0], "semilla": 4, "generaciones": 5}
    assert api.resolver_parametros({}, 9, None)["semilla"] == 9


def test_cuerpo_valida_dias_y_escenario():
    with pytest.raises(Exception):
        api.ParametrosGeneracion(feriados=[7])
    with pytest.raises(Exception):
        api.ParametrosGeneracion(escenario="E9")


def test_generar_devuelve_prediccion_por_funcion_y_guarda_la_ultima(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "CARTELERA_ULTIMA", tmp_path / "cartelera_ultima.json")
    monkeypatch.setattr(config, "POBLACION_AG", 3)  # la prueba no necesita 50 carteleras
    with pytest.raises(HTTPException) as no_hay:
        api.cartelera_ultima()
    assert no_hay.value.status_code == 404

    parametros = api.resolver_parametros({"escenario": "E3", "semilla": 1, "generaciones": 0}, 0, None)
    resultado = api.generar(parametros)
    funcion = resultado["funciones"][0]
    assert 0 <= funcion["ocupacion_esperada"] <= 1
    assert isinstance(funcion["espectadores_esperados"], int)
    assert set(funcion["probabilidades"]) == {"baja", "media", "alta"}
    assert sum(funcion["probabilidades"].values()) == pytest.approx(1, abs=1e-3)
    guardada = json.loads((tmp_path / "cartelera_ultima.json").read_text(encoding="utf-8"))
    assert guardada["parametros"]["promociones"] == [0, 1, 2]
    assert guardada["utilidad"] == resultado["utilidad"]
    assert api.cartelera_ultima()["fecha"] == resultado["fecha"]


def test_endpoints_de_adorno_responden_501():
    for llamada in (lambda: api.registrar_venta("P01", "S1", 0, 600, 10), api.simular_ventas):
        with pytest.raises(HTTPException) as error:
            llamada()
        assert error.value.status_code == 501
