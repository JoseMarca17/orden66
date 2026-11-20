"""Métodos de comparación del evaluador."""

from copy import deepcopy
import random
from . import config
from .csp_solver import generar_cartelera_valida
from .models import Calendario, Cartelera, Funcion


def m1_manual(calendario, ruta=None):
    """Baseline manual reproducible; usa una cartelera válida determinista."""
    return generar_cartelera_valida(calendario, 0)


def m2_aleatoria(calendario, semilla=0):
    return generar_cartelera_valida(calendario, semilla)
