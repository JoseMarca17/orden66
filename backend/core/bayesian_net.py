"""Red bayesiana de conteos para estimar ocupación de funciones."""

from pathlib import Path
import math
import numpy as np

from . import config
from .models import Calendario, Cartelera, Funcion


TIPOS = {"familiar_animada": 0, "superheroes_accion": 1, "otra_extranjera": 2, "nacional": 3}


# Ejes de la tabla de conteos, en el mismo orden que devuelve ``_indice`` (tras la clase).
EJES = ("clase", "tipo_dia", "franja", "feriado", "promocion", "tipo_pelicula", "semana", "capacidad", "simultaneas")


class RedBayesiana:
    """Modelo 8 padres → ocupación, implementado con conteos discretos.

    Forma: clase (3) × tipo_dia (3) × franja (3) × feriado (2) × promoción (2)
    × tipo_pelicula (4) × semana (3) × capacidad (3) × simultáneas (2).
    """

    forma = (3, 3, 3, 2, 2, 4, 3, 3, 2)

    def __init__(self, conteos: np.ndarray | None = None):
        self.conteos = np.zeros(self.forma, dtype=np.int64) if conteos is None else np.asarray(conteos, dtype=np.int64).copy()
        if self.conteos.shape != self.forma:
            raise ValueError(f"La tabla debe tener forma {self.forma}")

    @staticmethod
    def _tipo_dia(dia: int) -> int:
        return 0 if dia <= 3 else 1 if dia == 4 else 2

    @staticmethod
    def _franja(inicio: int) -> int:
        return 0 if inicio <= 839 else 1 if inicio <= 1139 else 2

    @staticmethod
    def _semana(valor: int) -> int:
        return max(1, min(int(valor), 3)) - 1

    @staticmethod
    def _capacidad(valor: int) -> int:
        return 0 if valor <= 90 else 1 if valor <= 180 else 2

    @staticmethod
    def _clase(ocupacion: float) -> int:
        return 0 if ocupacion < 0.30 else 1 if ocupacion <= 0.65 else 2

    def _indice(self, registro, calendario: Calendario | None = None, simultaneas: int | None = None) -> tuple:
        if isinstance(registro, Funcion):
            funcion = registro
            sala = next(s for s in calendario.salas if s.id == funcion.sala)
            feriado = int(calendario is not None and funcion.dia in calendario.feriados)
            promocion = int(calendario is not None and funcion.dia in calendario.promociones)
            simultaneas = 0 if simultaneas is None else int(bool(simultaneas))
            return self._validar(self._tipo_dia(funcion.dia), self._franja(funcion.inicio), feriado, promocion, TIPOS[funcion.pelicula.tipo], self._semana(funcion.pelicula.semana_cartelera), self._capacidad(sala.capacidad), simultaneas)
        p = registro
        tipo_dia = p.get("tipo_dia", self._tipo_dia(int(p.get("dia", 0))))
        if isinstance(tipo_dia, str):
            tipo_dia = {"laborable": 0, "viernes": 1, "fin_de_semana": 2}[tipo_dia]
        franja = p.get("franja", self._franja(int(p.get("inicio", 600))))
        if isinstance(franja, str):
            franja = {"matine": 0, "matiné": 0, "tarde": 1, "noche": 2}[franja]
        tipo = p.get("tipo_pelicula", p.get("tipo", 0))
        if isinstance(tipo, str):
            tipo = TIPOS[tipo]
        capacidad = p.get("capacidad", p.get("capacidad_sala", 80))
        if capacidad in (0, 1, 2):
            capacidad_idx = capacidad
        else:
            capacidad_idx = self._capacidad(int(capacidad))
        if simultaneas is None:
            simultaneas = p.get("simultaneas", 0)
        return self._validar(int(tipo_dia), int(franja), int(p.get("feriado", 0)), int(p.get("promocion", 0)), int(tipo), self._semana(int(p.get("semana", p.get("semana_cartelera", 1)))), capacidad_idx, int(bool(int(simultaneas))))

    def _validar(self, *indice) -> tuple:
        """Comprueba cada valor contra su eje; un valor fuera de rango es un error, no se recorta."""
        for eje, (valor, tamano) in enumerate(zip(indice, self.forma[1:]), start=1):
            if not 0 <= valor < tamano:
                raise ValueError(f"{EJES[eje]}={valor} fuera de rango (0..{tamano - 1})")
        return indice

    def probabilidades(self, registro, calendario=None, simultaneas=None) -> np.ndarray:
        """Devuelve P(baja, media, alta) con Laplace +1."""
        conteos = self.conteos[(slice(None),) + self._indice(registro, calendario, simultaneas)]
        return (conteos + 1) / (conteos.sum() + 3)

    def ocupacion_esperada(self, registro, calendario=None, simultaneas=None) -> float:
        p = self.probabilidades(registro, calendario, simultaneas)
        return float(np.dot(p, config.VALORES_CLASE))

    def prediccion(self, funcion: Funcion, calendario: Calendario, simultaneas: int = 0) -> dict:
        """Todo lo que la red predice de una función, con una sola consulta a la tabla."""
        p = self.probabilidades(funcion, calendario, simultaneas)
        ocupacion = float(np.dot(p, config.VALORES_CLASE))
        capacidad = next(s.capacidad for s in calendario.salas if s.id == funcion.sala)
        return {"probabilidades": p, "ocupacion": ocupacion, "esperados": capacidad * ocupacion, "en_riesgo": bool(p[0] > config.UMBRAL_RIESGO)}

    def esperados(self, registro, calendario=None, simultaneas=None) -> float:
        if isinstance(registro, Funcion):
            capacidad = next(s.capacidad for s in calendario.salas if s.id == registro.sala)
        else:
            capacidad = int(registro.get("capacidad", registro.get("capacidad_sala", 80)))
        return capacidad * self.ocupacion_esperada(registro, calendario, simultaneas)

    def entrenar(self, registros) -> None:
        """Suma un conteo por registro; acepta ocupación o clase explícita."""
        for registro in registros:
            clase = registro.get("clase") if isinstance(registro, dict) else None
            if clase is None:
                clase = self._clase(float(registro.get("ocupacion", 0)))
            elif isinstance(clase, str):
                clase = config.CLASES_OCUPACION.index(clase)
            self.conteos[(int(clase),) + self._indice(registro)] += 1

    def actualizar_con_ventas(self, funciones_con_venta_real, calendario: Calendario) -> None:
        """Aprende una clase por función, no por espectador individual.

        Cada dato es ``(funcion, espectadores)``, ``(funcion, espectadores, simultanea)`` o un dict
        con ``funcion``, ``espectadores`` y opcionalmente ``simultaneas``."""
        for dato in funciones_con_venta_real:
            simultanea = 0
            if isinstance(dato, dict):
                funcion = dato["funcion"]
                espectadores = dato.get("espectadores", dato.get("venta", 0))
                simultanea = dato.get("simultaneas", 0)
            elif len(dato) == 3:
                funcion, espectadores, simultanea = dato
            else:
                funcion, espectadores = dato
            capacidad = next(s.capacidad for s in calendario.salas if s.id == funcion.sala)
            clase = self._clase(float(espectadores) / capacidad)
            self.conteos[(clase,) + self._indice(funcion, calendario, simultanea)] += 1

    def metricas(self, test, calendario=None) -> dict:
        """Calcula exactitud, log-loss y línea base de clase más frecuente."""
        reales, predichas, perdidas = [], [], []
        for registro in test:
            real = registro.get("clase")
            if real is None:
                real = self._clase(float(registro.get("ocupacion", 0)))
            elif isinstance(real, str):
                real = config.CLASES_OCUPACION.index(real)
            real = int(real)
            p = self.probabilidades(registro, calendario)
            reales.append(real); predichas.append(int(np.argmax(p))); perdidas.append(-math.log(max(float(p[real]), 1e-15)))
        frecuencia = np.bincount(reales, minlength=3)
        base = int(np.argmax(frecuencia))
        return {"exactitud": float(np.mean(np.asarray(predichas) == np.asarray(reales))), "log_loss": float(np.mean(perdidas)), "exactitud_base": float(np.mean(np.asarray(reales) == base)), "clase_base": base}

    def guardar(self, ruta: str | Path) -> None:
        ruta = Path(ruta); ruta.parent.mkdir(parents=True, exist_ok=True); np.save(ruta, self.conteos)

    @classmethod
    def cargar(cls, ruta: str | Path) -> "RedBayesiana":
        return cls(np.load(ruta))
