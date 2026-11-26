"""Métodos de comparación del evaluador."""

from pathlib import Path
import json

from .csp_solver import generar_cartelera_valida
from .models import Calendario, Cartelera, Funcion

# M1: cartelera armada "a mano", como la haría una persona, con reglas simples y sin red ni AG:
#  - Las más populares (estrenos y superhéroes) van en las salas grandes y en tarde/noche.
#  - Las familiares van en matiné (antes de las 14:00).
#  - Las +18 desde las 18:00; cada película solo en salas de su formato.
#  - Cada sala repite la misma secuencia todos los días.
#  - Horarios redondos, 20 min de limpieza, ninguna película en dos salas a menos de 60 min.
# 20 funciones por día × 7 días = 140 funciones (parecido a M2 y M3). Todas las películas
# quedan con 7 a 21 funciones por semana (R5: mínimo 4, R6: máximo 30).
PLAN_M1 = {
    # sala: [(hora, película), ...]
    "S6": [("11:00", "P02"), ("14:00", "P04"), ("17:30", "P04"), ("20:30", "P04")],   # 200 butacas, XD/3D
    "S5": [("10:30", "P01"), ("13:30", "P05"), ("16:30", "P09"), ("19:30", "P05")],   # 240 butacas
    "S3": [("10:30", "P03"), ("15:00", "P06"), ("18:00", "P09"), ("21:00", "P07")],   # 140 butacas
    "S4": [("14:00", "P12"), ("16:30", "P08"), ("20:00", "P06")],                     # 140 butacas
    "S1": [("11:00", "P11"), ("18:30", "P07"), ("21:30", "P10")],                     # 80 butacas
    "S2": [("16:00", "P11"), ("19:00", "P08")],                                       # 80 butacas
}


def _minutos(hora: str) -> int:
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def construir_m1(calendario: Calendario) -> Cartelera:
    """Expande ``PLAN_M1`` a los 7 días. Determinista."""
    peliculas = {p.id: p for p in calendario.peliculas}
    funciones = [Funcion(peliculas[pelicula], sala, dia, _minutos(hora))
                 for dia in range(7) for sala, plan in PLAN_M1.items() for hora, pelicula in plan]
    return Cartelera(funciones)


def guardar_m1(cartelera: Cartelera, ruta: str | Path) -> None:
    datos = {"descripcion": "Cartelera manual M1: misma secuencia por sala todos los días (ver PLAN_M1 en core/baselines.py).",
             "funciones": [{"pelicula_id": f.pelicula.id, "sala": f.sala, "dia": f.dia, "inicio": f.inicio} for f in cartelera.funciones]}
    Path(ruta).write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cargar_m1(calendario: Calendario, ruta: str | Path) -> Cartelera:
    peliculas = {p.id: p for p in calendario.peliculas}
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    return Cartelera([Funcion(peliculas[f["pelicula_id"]], f["sala"], int(f["dia"]), int(f["inicio"])) for f in datos["funciones"]])


def m1_manual(calendario, ruta=None):
    """Baseline manual: lee ``data/cartelera_manual_m1.json`` si se da la ruta; si no, la arma con ``PLAN_M1``."""
    return cargar_m1(calendario, ruta) if ruta is not None else construir_m1(calendario)


def m2_aleatoria(calendario, semilla=0):
    return generar_cartelera_valida(calendario, semilla)
