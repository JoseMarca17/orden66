"""Orquestador del ciclo percibir → optimizar → entregar → aprender."""

from .bayesian_net import RedBayesiana
from .csp_solver import generar_cartelera_valida
from .genetic_algo import AlgoritmoGenetico


class AgenteOrden66:
    def __init__(self, calendario, red=None):
        self.calendario = calendario
        self.red = red or RedBayesiana()

    def generar(self, semilla=0, fijas=(), generaciones=None):
        inicial = generar_cartelera_valida(self.calendario, semilla, fijas=fijas)
        mejor, curva = AlgoritmoGenetico(self.calendario, self.red, semilla, generaciones).optimizar([inicial], fijas=fijas)
        return mejor, curva

    def aprender(self, funciones_con_venta_real):
        self.red.actualizar_con_ventas(funciones_con_venta_real, self.calendario)
