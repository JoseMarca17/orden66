from orden66.backend.core import config
from orden66.backend.core.models import Calendario, Cartelera, Funcion, Pelicula, Sala
from orden66.backend.core.validator import validar
from orden66.backend.core.simulator import generar_historial


def calendario():
    salas = [Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS]
    peliculas = [Pelicula(*p) for p in config.PELICULAS_BASE]
    return Calendario.crear(salas, peliculas)


def cartelera_minima(c):
    funciones = []
    ocupadas = {(s.id, d): [] for s in c.salas for d in range(4)}
    for p in c.peliculas:
        for dia in range(4):
            for sala in c.salas:
                if p.formato not in sala.formatos:
                    continue
                posibles = range(1080, 1321, 30) if p.clasificacion == "+18" else range(600, 1321, 30)
                inicio = next((t for t in posibles if all(t >= fin + 20 or t + p.duracion + 20 <= desde for desde, fin in ocupadas[(sala.id, dia)])), None)
                if inicio is not None:
                    ocupadas[(sala.id, dia)].append((inicio, inicio + p.duracion))
                    funciones.append(Funcion(p, sala.id, dia, inicio))
                    break
    return Cartelera(funciones)


def test_cartelera_minima_valida():
    c = calendario()
    resultado = validar(cartelera_minima(c), c)
    assert resultado.es_valida


def test_validador_detecta_formato():
    c = calendario(); p = c.peliculas[1]
    resultado = validar(Cartelera([Funcion(p, "S1", 0, 600)]), c)
    assert not resultado.restricciones["R1"]


def test_validador_detecta_clasificacion_horario_y_colision():
    c = calendario(); p = next(p for p in c.peliculas if p.clasificacion == "+18")
    cartelera = Cartelera([Funcion(p, "S1", 0, 600), Funcion(p, "S1", 0, 650)])
    resultado = validar(cartelera, c)
    assert not resultado.restricciones["R2"]
    assert not resultado.restricciones["R4"]


def test_validador_detecta_minimos_y_maximos():
    c = calendario(); p = c.peliculas[0]
    funciones = [Funcion(p, "S1", 0, 600 + i * 30) for i in range(9)]
    resultado = validar(Cartelera(funciones), c)
    assert not resultado.restricciones["R5"]
    assert not resultado.restricciones["R6"]


def test_historial_tiene_20000_filas(tmp_path):
    registros = generar_historial(calendario(), n=20_000, semilla=7, destino=tmp_path / "historial_ventas.csv")
    assert len(registros) == 20_000
    assert (tmp_path / "historial_ventas.csv").exists()
