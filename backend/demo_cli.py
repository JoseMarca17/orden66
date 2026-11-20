"""Demostración de consola del agente Orden 66.

Ejecutar desde backend/: ``python demo_cli.py --escenario E4``.
"""

from pathlib import Path
import argparse
import csv
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent))

from orden66.backend.core import config
from orden66.backend.core.agent import AgenteOrden66
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.genetic_algo import utilidad
from orden66.backend.core.models import Calendario, Pelicula, Sala


def calendario():
    return Calendario.crear([Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS], [Pelicula(*p) for p in config.PELICULAS_BASE])


def cargar_red(cal):
    ruta = ROOT / "storage" / "modelo_rb.npy"
    if ruta.exists():
        return RedBayesiana.cargar(ruta)
    red = RedBayesiana()
    historial = ROOT / "data" / "historial_ventas.csv"
    with historial.open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    mitad = int(len(filas) * 0.8)
    registros = []
    peliculas = {p.id: p for p in cal.peliculas}
    salas = {s.id: s for s in cal.salas}
    for fila in filas[:mitad]:
        pelicula = peliculas[fila["pelicula_id"]]; sala = salas[fila["sala"]]
        registros.append({"dia": int(fila["dia"]), "inicio": int(fila["inicio"]), "tipo": pelicula.tipo, "semana": pelicula.semana_cartelera, "capacidad": sala.capacidad, "feriado": int(fila["feriado"]), "promocion": int(fila["promocion"]), "ocupacion": float(fila["ocupacion"])})
    red.entrenar(registros); red.guardar(ruta)
    return red


def texto_hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def ejecutar(escenario):
    cal = calendario(); red = cargar_red(cal); agente = AgenteOrden66(cal, red)
    cartelera, curva = agente.generar(semilla=66, generaciones=5)
    esperados = sum(red.esperados(f, cal) for f in cartelera.funciones)
    bajas = sum(red.ocupacion_esperada(f, cal) < 0.20 for f in cartelera.funciones)
    print("\n" + "=" * 72); print(f"ORDEN 66 · DEMOSTRACIÓN CLI · ESCENARIO {escenario}"); print("=" * 72)
    print(f"Utilidad total U(C):                  {utilidad(cartelera, cal, red):,.2f}")
    print(f"Espectadores esperados:               {esperados:,.1f}")
    print(f"Funciones con ocupación menor al 20%: {bajas}")
    print(f"Generaciones evaluadas:               {len(curva)}\n")
    nombres_dia = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    for dia in range(7):
        print(f"[{nombres_dia[dia]}]")
        for sala in sorted(cal.salas, key=lambda s: s.id):
            funciones = sorted((f for f in cartelera.funciones if f.dia == dia and f.sala == sala.id), key=lambda f: f.inicio)
            if not funciones: continue
            print(f"  Sala {sala.id} ({sala.capacidad} butacas)")
            for funcion in funciones:
                fin = funcion.inicio + funcion.pelicula.duracion
                ocup = red.ocupacion_esperada(funcion, cal); espectadores = round(sala.capacidad * ocup)
                print(f"    {texto_hora(funcion.inicio)} - {texto_hora(fin)} | {funcion.pelicula.titulo} ({funcion.pelicula.clasificacion}) | Ocup. esp: {ocup * 100:.1f}% ({espectadores} esp.)")
    lunes = [f for f in cartelera.funciones if f.dia == 0][:3]
    print("\n" + "-" * 72); print("APRENDIZAJE EN LÍNEA · 3 funciones del lunes al 95%")
    for funcion in lunes:
        antes = red.probabilidades(funcion, cal); capacidad = next(s.capacidad for s in cal.salas if s.id == funcion.sala)
        red.actualizar_con_ventas([(funcion, round(capacidad * 0.95))], cal); despues = red.probabilidades(funcion, cal)
        print(f"{funcion.pelicula.titulo} / {funcion.sala} {texto_hora(funcion.inicio)}: alta {antes[2] * 100:.1f}% → {despues[2] * 100:.1f}%")
    red.guardar(ROOT / "storage" / "modelo_rb.npy")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Demo de Orden 66")
    parser.add_argument("--escenario", choices=("E1", "E2", "E3", "E4"), default="E4")
    ejecutar(parser.parse_args().escenario)
