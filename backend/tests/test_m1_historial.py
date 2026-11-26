"""M1 manual por reglas y calendario semanal del historial (feriados y promociones)."""

from dataclasses import replace
from pathlib import Path

from orden66.backend.core import config
from orden66.backend.core.baselines import cargar_m1, construir_m1
from orden66.backend.core.simulator import generar_historial
from orden66.backend.core.validator import validar

RUTA_M1 = Path(__file__).resolve().parents[1] / "data" / "cartelera_manual_m1.json"


def test_m1_es_valida_en_los_cuatro_escenarios_y_determinista(calendario):
    m1 = cargar_m1(calendario, RUTA_M1)
    assert [f.clave for f in m1.funciones] == [f.clave for f in construir_m1(calendario).funciones]
    assert 130 <= len(m1.funciones) <= 150
    escenarios = (calendario, replace(calendario, feriados=frozenset({4})), replace(calendario, promociones=frozenset({0, 1, 2})))
    for cal in escenarios:
        assert validar(m1, cal).es_valida


def test_m1_misma_secuencia_por_sala_todos_los_dias(calendario):
    m1 = construir_m1(calendario)
    secuencia = lambda dia, sala: [(f.inicio, f.pelicula.id) for f in m1.por_dia_sala(dia, sala)]
    for sala in config.SALAS:
        assert all(secuencia(dia, sala.id) == secuencia(0, sala.id) for dia in range(7))


def test_m1_familiares_en_matine_y_populares_grandes_en_tarde_noche(calendario):
    for f in construir_m1(calendario).funciones:
        if f.pelicula.tipo == "familiar_animada":
            assert f.inicio < 14 * 60
        if f.sala in ("S5", "S6") and f.inicio >= 14 * 60:
            assert f.pelicula.semana_cartelera == 1 or f.pelicula.tipo == "superheroes_accion"


def test_historial_tiene_feriados_y_promociones_por_semana(calendario):
    registros = generar_historial(calendario, n=config.FUNCIONES_POR_SEMANA_HISTORIAL * 40, semilla=0)
    assert any(r["feriado"] for r in registros) and any(r["promocion"] for r in registros)
    assert all(r["dia"] in config.DIAS_PROMOCION_HISTORIAL for r in registros if r["promocion"])
