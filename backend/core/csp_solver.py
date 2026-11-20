"""Programación de restricciones para construir y reparar carteleras."""

from collections import Counter, defaultdict
import random
import time

from . import config
from .models import Calendario, Cartelera, Funcion


Posicion = tuple[str, int, int]


def _sala_por_id(calendario: Calendario):
    return {s.id: s for s in calendario.salas}


def _compatible(pelicula, posicion: Posicion, salas) -> bool:
    sala, _dia, inicio = posicion
    sala_obj = salas.get(sala)
    return bool(sala_obj and pelicula.formato in sala_obj.formatos and inicio >= config.INICIOS[0] and inicio + pelicula.duracion <= config.CIERRE and (pelicula.clasificacion != "+18" or inicio >= 1080))


def _cruza(pelicula_a, inicio_a: int, pelicula_b, inicio_b: int) -> bool:
    return not (inicio_a + pelicula_a.duracion + config.LIMPIEZA <= inicio_b or inicio_b + pelicula_b.duracion + config.LIMPIEZA <= inicio_a)


def _puede_agregar(pelicula, posicion, asignadas, conteo_dia, conteo_pelicula, salas) -> bool:
    sala, dia, inicio = posicion
    if conteo_dia[(sala, dia)] >= config.MAX_FUNCIONES_DIA:
        return False
    if conteo_dia[("pelicula", dia, pelicula.id)] >= config.MAX_FUNCIONES_DIA:
        return False
    if conteo_pelicula[pelicula.id] >= config.MAX_FUNCIONES_SEMANA:
        return False
    for otra, otra_pos in asignadas:
        otra_sala, otra_dia, otro_inicio = otra_pos
        if sala == otra_sala and dia == otra_dia and _cruza(pelicula, inicio, otra, otro_inicio):
            return False
    return True


def _dominio_inicial(pelicula, calendario: Calendario) -> list[Posicion]:
    salas = _sala_por_id(calendario)
    return [(sala.id, dia, inicio) for sala in calendario.salas for dia in config.DIAS for inicio in config.INICIOS if _compatible(pelicula, (sala.id, dia, inicio), salas)]


def _grado(pelicula, dominio, asignadas) -> int:
    return sum(1 for posicion in dominio if not any(posicion[0] == otra_pos[0] and posicion[1] == otra_pos[1] for otra, otra_pos in asignadas))


def _resolver_obligatorias(calendario, peliculas, semilla, fijas=(), limite_nodos=100_000, limite_segundos=10.0):
    rng = random.Random(semilla)
    salas = _sala_por_id(calendario)
    asignadas = []
    conteo_dia = Counter()
    conteo_pelicula = Counter()
    for fija in fijas:
        posicion = (fija.sala, fija.dia, fija.inicio)
        if _compatible(fija.pelicula, posicion, salas) and _puede_agregar(fija.pelicula, posicion, asignadas, conteo_dia, conteo_pelicula, salas):
            asignadas.append((fija.pelicula, posicion))
            conteo_dia[(fija.sala, fija.dia)] += 1
            conteo_dia[("pelicula", fija.dia, fija.pelicula.id)] += 1
            conteo_pelicula[fija.pelicula.id] += 1

    variables = []
    for pelicula in peliculas:
        faltantes = max(0, config.MIN_FUNCIONES_PELICULA - conteo_pelicula[pelicula.id])
        variables.extend([pelicula] * faltantes)
    dominios = {i: _dominio_inicial(p, calendario) for i, p in enumerate(variables)}
    nodos = 0
    inicio_reloj = time.monotonic()

    def buscar(restantes):
        nonlocal nodos
        nodos += 1
        if nodos > limite_nodos or time.monotonic() - inicio_reloj > limite_segundos:
            return False
        if not restantes:
            return True
        opciones = []
        for indice in restantes:
            pelicula = variables[indice]
            posibles = dominios[indice]
            if len(posibles) > 180:
                # La consistencia R4 ya se mantiene en los dominios; limitar la
                # exploración evita revisar 1050 posiciones en cada nivel.
                posibles = [pos for pos in posibles if _puede_agregar(pelicula, pos, asignadas, conteo_dia, conteo_pelicula, salas)]
            else:
                posibles = [pos for pos in posibles if _puede_agregar(pelicula, pos, asignadas, conteo_dia, conteo_pelicula, salas)]
            if not posibles:
                return False
            opciones.append((len(posibles), -_grado(pelicula, posibles, asignadas), indice, posibles))
        _, _, indice, posibles = min(opciones)
        rng.shuffle(posibles)
        pelicula = variables[indice]
        siguientes = [i for i in restantes if i != indice]
        for posicion in posibles:
            if not _puede_agregar(pelicula, posicion, asignadas, conteo_dia, conteo_pelicula, salas):
                continue
            asignadas.append((pelicula, posicion))
            sala, dia, _ = posicion
            conteo_dia[(sala, dia)] += 1
            conteo_dia[("pelicula", dia, pelicula.id)] += 1
            conteo_pelicula[pelicula.id] += 1
            # Comprobación hacia adelante y poda temporal de vecinos (R4).
            cambios = {}
            for i in siguientes:
                anterior = dominios[i]
                nuevo = [v for v in anterior if not (v[0] == sala and v[1] == dia and _cruza(variables[i], v[2], pelicula, posicion[2]))]
                cambios[i] = anterior
                dominios[i] = nuevo
            viable = all(any(_puede_agregar(variables[i], v, asignadas, conteo_dia, conteo_pelicula, salas) for v in dominios[i]) for i in siguientes)
            if viable and buscar(siguientes):
                return True
            for i, anterior in cambios.items():
                dominios[i] = anterior
            asignadas.pop()
            conteo_dia[(sala, dia)] -= 1
            conteo_dia[("pelicula", dia, pelicula.id)] -= 1
            conteo_pelicula[pelicula.id] -= 1
        return False

    if not buscar(list(dominios)):
        raise RuntimeError("No se pudo resolver el conjunto obligatorio dentro del límite")
    funciones = [Funcion(pelicula, sala, dia, inicio) for pelicula, (sala, dia, inicio) in asignadas]
    return funciones, asignadas, conteo_dia, conteo_pelicula


def _rellenar(calendario, funciones, semilla, objetivo=140, limite_segundos=5.0):
    """Rellena sin retroceso; una función se omite si no tiene dominio viable."""
    rng = random.Random(semilla)
    salas = _sala_por_id(calendario)
    asignadas = [(f.pelicula, (f.sala, f.dia, f.inicio)) for f in funciones]
    conteo_dia = Counter()
    conteo_pelicula = Counter()
    for f in funciones:
        conteo_dia[(f.sala, f.dia)] += 1
        conteo_dia[("pelicula", f.dia, f.pelicula.id)] += 1
        conteo_pelicula[f.pelicula.id] += 1
    pesos = {"familiar_animada": 4, "superheroes_accion": 4, "otra_extranjera": 2, "nacional": 1}
    dominios = {p.id: _dominio_inicial(p, calendario) for p in calendario.peliculas}
    inicio_reloj = time.monotonic()
    while len(funciones) < objetivo and time.monotonic() - inicio_reloj < limite_segundos:
        peliculas = sorted(calendario.peliculas, key=lambda p: pesos[p.tipo] * (1 + rng.random()))
        agregada = False
        for pelicula in peliculas:
            dominio_completo = dominios[pelicula.id]
            dominio = rng.sample(dominio_completo, min(80, len(dominio_completo)))
            posibles = [pos for pos in dominio if _puede_agregar(pelicula, pos, asignadas, conteo_dia, conteo_pelicula, salas)]
            if not posibles:
                continue
            posicion = posibles[0]
            asignadas.append((pelicula, posicion))
            sala, dia, inicio = posicion
            conteo_dia[(sala, dia)] += 1; conteo_dia[("pelicula", dia, pelicula.id)] += 1; conteo_pelicula[pelicula.id] += 1
            funciones.append(Funcion(pelicula, sala, dia, inicio))
            agregada = True
            break
        if not agregada:
            break
    return funciones


def generar_cartelera_valida(calendario: Calendario, semilla: int, fijas=[]) -> Cartelera:
    """Construye las 48 funciones obligatorias y añade relleno válido."""
    funciones, *_ = _resolver_obligatorias(calendario, calendario.peliculas, semilla, fijas=fijas)
    return Cartelera(_rellenar(calendario, funciones, semilla + 1))


def reparar(cartelera: Cartelera, calendario: Calendario | None = None, semilla: int = 0) -> Cartelera:
    """Conserva funciones válidas no conflictivas y resuelve los faltantes."""
    if calendario is None:
        raise ValueError("reparar requiere el Calendario para verificar formatos y mínimos")
    salas = _sala_por_id(calendario)
    conservadas = []
    for funcion in cartelera.funciones:
        posicion = (funcion.sala, funcion.dia, funcion.inicio)
        asignadas = [(f.pelicula, (f.sala, f.dia, f.inicio)) for f in conservadas]
        conteo_dia = Counter((f.sala, f.dia) for f in conservadas)
        conteo_dia.update(("pelicula", f.dia, f.pelicula.id) for f in conservadas)
        conteo_pelicula = Counter(f.pelicula.id for f in conservadas)
        if _compatible(funcion.pelicula, posicion, salas) and _puede_agregar(funcion.pelicula, posicion, asignadas, conteo_dia, conteo_pelicula, salas):
            conservadas.append(funcion)
    funciones, *_ = _resolver_obligatorias(calendario, calendario.peliculas, semilla, fijas=conservadas)
    return Cartelera(_rellenar(calendario, funciones, semilla + 1))
