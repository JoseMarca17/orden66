"""Lectura del historial de ventas y entrenamiento de la red bayesiana.

Es la única parte del núcleo que lee archivos, y solo se usa al preparar el modelo
(API, demo y reporte), nunca dentro de los algoritmos.
"""

from pathlib import Path
import csv

from .bayesian_net import RedBayesiana
from .models import Calendario

PROPORCION_ENTRENAMIENTO = 0.8


def leer_historial(ruta: str | Path, calendario: Calendario) -> list[dict]:
    """Convierte cada fila del CSV en un registro que entiende ``RedBayesiana``."""
    peliculas = {p.id: p for p in calendario.peliculas}
    salas = {s.id: s for s in calendario.salas}
    registros = []
    with Path(ruta).open(encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            pelicula = peliculas[fila["pelicula_id"]]
            sala = salas[fila["sala"]]
            registros.append({
                "dia": int(fila["dia"]), "inicio": int(fila["inicio"]),
                "feriado": int(fila["feriado"]), "promocion": int(fila["promocion"]),
                "tipo": pelicula.tipo, "semana": pelicula.semana_cartelera,
                "capacidad": sala.capacidad,
                # Los historiales anteriores a esta columna no la traen: se asume 0.
                "simultaneas": int(fila.get("simultaneas") or 0),
                "ocupacion": float(fila["ocupacion"]),
            })
    return registros


def dividir(registros: list[dict], proporcion: float = PROPORCION_ENTRENAMIENTO) -> tuple[list[dict], list[dict]]:
    """Corte determinista: las primeras filas entrenan y el resto prueba."""
    corte = int(len(registros) * proporcion)
    return registros[:corte], registros[corte:]


def entrenar_desde_historial(ruta: str | Path, calendario: Calendario, proporcion: float = PROPORCION_ENTRENAMIENTO) -> tuple[RedBayesiana, list[dict]]:
    """Entrena con el ``proporcion`` inicial del historial y devuelve la red y el conjunto de prueba."""
    entrenamiento, prueba = dividir(leer_historial(ruta, calendario), proporcion)
    red = RedBayesiana()
    red.entrenar(entrenamiento)
    return red, prueba


def cargar_o_entrenar(ruta_modelo: str | Path, ruta_historial: str | Path, calendario: Calendario) -> tuple[RedBayesiana, str]:
    """Carga el modelo guardado; si falta o tiene otra forma, lo entrena con el historial y lo guarda.

    Devuelve la red y el origen ("archivo" o "entrenada").
    """
    ruta_modelo = Path(ruta_modelo)
    if ruta_modelo.exists():
        try:
            return RedBayesiana.cargar(ruta_modelo), "archivo"
        except ValueError:
            pass  # Forma vieja: se reentrena.
    red, _ = entrenar_desde_historial(ruta_historial, calendario)
    red.guardar(ruta_modelo)
    return red, "entrenada"
