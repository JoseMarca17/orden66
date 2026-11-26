"""Orquestador del ciclo percibir → optimizar → entregar → aprender."""

from .bayesian_net import RedBayesiana
from .genetic_algo import AlgoritmoGenetico


class AgenteOrden66:
    def __init__(self, calendario, red=None):
        self.calendario = calendario
        self.red = red or RedBayesiana()

    def generar(self, semilla=0, fijas=(), generaciones=None):
        """PSR (población inicial diversa de carteleras válidas) → AG que maximiza U(C)."""
        return AlgoritmoGenetico(self.calendario, self.red, semilla, generaciones).optimizar(fijas=fijas)

    def aprender(self, funciones_con_venta_real):
        self.red.actualizar_con_ventas(funciones_con_venta_real, self.calendario)
