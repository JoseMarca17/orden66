"""Evaluación reproducible de métodos y escenarios."""

from pathlib import Path
import csv
import time
import numpy as np

from .agent import AgenteOrden66
from .baselines import m1_manual, m2_aleatoria
from .genetic_algo import utilidad
from .simulator import ocupacion_real
from .validator import porcentaje_restricciones


def evaluar_cartelera(cartelera, calendario, red, semilla=0, escenario=None):
    esperados = sum(red.esperados(f, calendario) for f in cartelera.funciones)
    reales = []
    for i, funcion in enumerate(cartelera.funciones):
        reales.append(ocupacion_real(funcion, calendario, semilla + i, estreno_fuerte=escenario == "E4") * next(s.capacidad for s in calendario.salas if s.id == funcion.sala))
    ocupacion = np.mean([x / next(s.capacidad for s in calendario.salas if s.id == f.sala) for x, f in zip(reales, cartelera.funciones)])
    return {"esperados": float(esperados), "reales": float(sum(reales)), "ocupacion_promedio": float(ocupacion), "funciones_baja_20": float(np.mean([red.ocupacion_esperada(f, calendario) < .2 for f in cartelera.funciones])), "restricciones": porcentaje_restricciones(cartelera, calendario), "utilidad": utilidad(cartelera, calendario, red)}


def ejecutar_experimentos(calendario, red=None, semillas=range(30), destino="results/resultados_experimentos.csv", generaciones=None):
    red = red or __import__("backend.core.bayesian_net", fromlist=["RedBayesiana"]).RedBayesiana()
    filas = []
    for escenario in ("E1", "E2", "E3", "E4"):
        for semilla in semillas:
            for metodo in ("M1", "M2", "M3"):
                inicio = time.perf_counter()
                if metodo == "M1": cartelera = m1_manual(calendario)
                elif metodo == "M2": cartelera = m2_aleatoria(calendario, semilla)
                else: cartelera, curva = AgenteOrden66(calendario, red).generar(semilla, generaciones=generaciones)
                metricas = evaluar_cartelera(cartelera, calendario, red, semilla, escenario)
                filas.append({"escenario": escenario, "semilla": semilla, "metodo": metodo, "tiempo": time.perf_counter() - inicio, **metricas})
    ruta = Path(destino); ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=filas[0].keys()); writer.writeheader(); writer.writerows(filas)
    return filas
