"""Pruebas unitarias independientes de R1 a R7."""

from orden66.backend.core.models import Cartelera, Funcion
from orden66.backend.core.validator import validar


def una_funcion(calendario, pelicula=None, sala="S1", dia=0, inicio=600):
    return Funcion(pelicula or calendario.peliculas[0], sala, dia, inicio)


def test_R1_formato_de_pelicula_debe_ser_compatible(calendario):
    resultado = validar(Cartelera([una_funcion(calendario, calendario.peliculas[1], "S1")]), calendario)
    assert resultado.restricciones["R1"] is False


def test_R2_restringe_mas_18_antes_de_las_18(calendario):
    pelicula = next(p for p in calendario.peliculas if p.clasificacion == "+18")
    resultado = validar(Cartelera([una_funcion(calendario, pelicula, "S1", inicio=1079)]), calendario)
    assert resultado.restricciones["R2"] is False


def test_R3_restringe_funcion_fuera_de_10_a_24(calendario):
    pelicula_larga = calendario.peliculas[3]
    resultado = validar(Cartelera([una_funcion(calendario, pelicula_larga, "S6", inicio=1320)]), calendario)
    assert resultado.restricciones["R3"] is False


def test_R4_exige_20_minutos_de_limpieza(calendario):
    pelicula = calendario.peliculas[0]
    cartelera = Cartelera([Funcion(pelicula, "S1", 0, 600), Funcion(pelicula, "S1", 0, 710)])
    resultado = validar(cartelera, calendario)
    assert resultado.restricciones["R4"] is False


def test_R5_exige_cuatro_funciones_por_pelicula(calendario):
    resultado = validar(Cartelera([]), calendario)
    assert resultado.restricciones["R5"] is False


def test_R6_exige_maximo_ocho_por_dia_y_treinta_por_semana(calendario):
    pelicula = calendario.peliculas[0]
    funciones = [Funcion(pelicula, f"S{i % 2 + 1}", 0, 600 + (i // 2) * 180) for i in range(9)]
    resultado = validar(Cartelera(funciones), calendario)
    assert resultado.restricciones["R6"] is False


def test_R7_exige_una_sola_posicion_por_funcion(calendario):
    pelicula = calendario.peliculas[0]
    posicion = [Funcion(pelicula, "S1", 0, 600), Funcion(pelicula, "S1", 0, 600)]
    resultado = validar(Cartelera(posicion), calendario)
    assert resultado.restricciones["R7"] is False
