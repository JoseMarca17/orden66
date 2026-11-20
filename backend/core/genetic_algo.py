"""Algoritmo genético para maximizar la utilidad de una cartelera."""

from copy import deepcopy
import random

from . import config
from .bayesian_net import RedBayesiana
from .csp_solver import generar_cartelera_valida, reparar
from .models import Calendario, Cartelera, Funcion
from .validator import validar


def utilidad(cartelera: Cartelera, calendario: Calendario, red: RedBayesiana) -> float:
    valor = 0.0
    bajas = 0
    for funcion in cartelera.funciones:
        esperado = red.esperados(funcion, calendario)
        valor += esperado
        bajas += red.ocupacion_esperada(funcion, calendario) < 0.20
    return valor - config.LAMBDA * bajas


class AlgoritmoGenetico:
    def __init__(self, calendario: Calendario, red: RedBayesiana, semilla: int = 0, generaciones: int | None = None):
        self.calendario = calendario
        self.red = red
        self.rng = random.Random(semilla)
        self.generaciones = config.GENERACIONES_AG if generaciones is None else generaciones
        self.cache: dict[tuple, float] = {}

    def _evaluar(self, cartelera):
        clave = tuple(sorted(f.clave for f in cartelera.funciones))
        if clave not in self.cache:
            self.cache[clave] = utilidad(cartelera, self.calendario, self.red)
        return self.cache[clave]

    def _torneo(self, poblacion):
        candidatos = self.rng.sample(poblacion, min(config.TORNEO_K, len(poblacion)))
        return max(candidatos, key=self._evaluar)

    def _cruzar(self, a, b):
        corte = self.rng.randint(1, 6)
        hijos = []
        for izquierda, derecha in ((a, b), (b, a)):
            funciones = [deepcopy(f) for f in izquierda.funciones if f.dia < corte]
            funciones += [deepcopy(f) for f in derecha.funciones if f.dia >= corte]
            hijo = Cartelera(funciones)
            if not validar(hijo, self.calendario).es_valida:
                hijo = reparar(hijo, self.calendario, self.rng.randrange(1_000_000))
            hijos.append(hijo)
        return hijos

    def _mutar(self, cartelera):
        if self.rng.random() >= config.P_MUTACION or not cartelera.funciones:
            return cartelera
        original = deepcopy(cartelera)
        funcion = self.rng.choice(cartelera.funciones)
        eleccion = self.rng.random()
        if eleccion < 0.30:
            compatibles = [p for p in self.calendario.peliculas if p.formato in next(s for s in self.calendario.salas if s.id == funcion.sala).formatos]
            funcion.pelicula = self.rng.choice(compatibles)
        elif eleccion < 0.60:
            funcion.inicio = self.rng.choice(config.INICIOS)
            funcion.dia = self.rng.choice(config.DIAS)
        elif eleccion < 0.85:
            otras = [f for f in cartelera.funciones if f.dia == funcion.dia and f is not funcion]
            if otras:
                otra = self.rng.choice(otras); funcion.sala, otra.sala = otra.sala, funcion.sala
        else:
            cartelera.funciones.remove(funcion)
        if not validar(cartelera, self.calendario).es_valida:
            return original
        return cartelera

    def optimizar(self, poblacion_inicial=None, fijas=()):
        if poblacion_inicial:
            poblacion = [deepcopy(c) for c in poblacion_inicial]
        else:
            base = generar_cartelera_valida(self.calendario, self.rng.randrange(1_000_000), fijas=fijas)
            poblacion = [deepcopy(base)]
            for _ in range(config.POBLACION_AG - 1):
                poblacion.append(generar_cartelera_valida(self.calendario, self.rng.randrange(1_000_000), fijas=fijas))
        while len(poblacion) < config.POBLACION_AG:
            poblacion.append(deepcopy(poblacion[0]))
        mejor = max(poblacion, key=self._evaluar)
        curva = [self._evaluar(mejor)]
        sin_mejora = 0
        for _ in range(self.generaciones):
            ordenada = sorted(poblacion, key=self._evaluar, reverse=True)
            nueva = [deepcopy(x) for x in ordenada[:config.ELITISMO]]
            while len(nueva) < config.POBLACION_AG:
                padre = self._torneo(poblacion); madre = self._torneo(poblacion)
                hijos = self._cruzar(padre, madre) if self.rng.random() < config.P_CRUCE else [deepcopy(padre)]
                nueva.extend(self._mutar(h) for h in hijos)
            poblacion = nueva[:config.POBLACION_AG]
            candidato = max(poblacion, key=self._evaluar)
            valor = self._evaluar(candidato)
            curva.append(valor)
            if valor > self._evaluar(mejor):
                mejor = deepcopy(candidato); sin_mejora = 0
            else:
                sin_mejora += 1
            if sin_mejora >= config.PARADA_SIN_MEJORA:
                break
        return mejor, curva


def optimizar(cartelera, calendario, red, semilla=0, generaciones=None, fijas=()):
    return AlgoritmoGenetico(calendario, red, semilla, generaciones).optimizar([cartelera], fijas)
