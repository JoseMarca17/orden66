"""API HTTP de Orden 66. El motor de IA permanece en backend.core."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal
from uuid import uuid4
import json
import os

try:
    from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError:  # Permite importar el núcleo sin instalar la capa web.
    FastAPI = None

from .core import config
from .core.agent import AgenteOrden66
from .core.genetic_algo import utilidad
from .core.historial import cargar_o_entrenar
from .core.models import Calendario, Pelicula, Sala, simultaneas_de

ROOT = Path(__file__).resolve().parent
STORAGE = ROOT / "storage"
POSTERS = STORAGE / "posters"
MODELO_RB = STORAGE / "modelo_rb.npy"
HISTORIAL = ROOT / "data" / "historial_ventas.csv"
CARTELERA_ULTIMA = STORAGE / "cartelera_ultima.json"
POSTERS.mkdir(parents=True, exist_ok=True)
jobs, jobs_lock, guardado_lock = {}, Lock(), Lock()
executor = ThreadPoolExecutor(max_workers=2)
catalogo = [dict(zip(("id", "titulo", "duracion", "clasificacion", "formato", "tipo", "semana_cartelera"), pelicula)) for pelicula in config.PELICULAS_BASE]

# Escenarios de la tesis. E4 (estreno fuerte de P04) solo existe en el simulador: el agente
# no lo observa, así que para generar la cartelera equivale a E1.
ESCENARIOS = {"E1": ((), ()), "E2": ((4,), ()), "E3": ((), (0, 1, 2)), "E4": ((), ())}


def crear_calendario(feriados=(), promociones=()):
    salas = tuple(Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS)
    peliculas = tuple(Pelicula(*p) for p in config.PELICULAS_BASE)
    return Calendario.crear(salas, peliculas, feriados=frozenset(feriados), promociones=frozenset(promociones))


# Una sola red compartida, cargada al iniciar. Los trabajos solo la leen (no aprenden en línea),
# así que se puede usar desde los hilos del executor sin bloqueo.
red, origen_red = cargar_o_entrenar(MODELO_RB, HISTORIAL, crear_calendario())


def serializar_funcion(funcion, simultanea, calendario) -> dict:
    """Función + predicción de la red: ocupación (0-1), espectadores y P(baja, media, alta)."""
    prediccion = red.prediccion(funcion, calendario, simultanea)
    baja, media, alta = (round(float(p), 4) for p in prediccion["probabilidades"])
    return {
        "pelicula": asdict(funcion.pelicula), "sala": funcion.sala, "dia": funcion.dia, "inicio": funcion.inicio,
        "simultanea": simultanea,
        "ocupacion_esperada": round(prediccion["ocupacion"], 4),
        "espectadores_esperados": round(prediccion["esperados"]),
        "probabilidades": {"baja": baja, "media": media, "alta": alta},
        "en_riesgo": prediccion["en_riesgo"],
    }


def resolver_parametros(cuerpo: dict, semilla_query: int, generaciones_query: int | None) -> dict:
    """Combina el cuerpo JSON (prioridad) con los parámetros de consulta de siempre."""
    escenario = cuerpo.get("escenario")
    feriados, promociones = ESCENARIOS.get(escenario or "E1", ((), ()))
    return {
        "escenario": escenario,
        "feriados": sorted(set(feriados) | set(cuerpo.get("feriados") or ())),
        "promociones": sorted(set(promociones) | set(cuerpo.get("promociones") or ())),
        "semilla": semilla_query if cuerpo.get("semilla") is None else cuerpo["semilla"],
        "generaciones": generaciones_query if cuerpo.get("generaciones") is None else cuerpo["generaciones"],
    }


def generar(parametros: dict, progreso=lambda n: None) -> dict:
    calendario = crear_calendario(parametros["feriados"], parametros["promociones"])
    progreso(5)
    cartelera, curva = AgenteOrden66(calendario, red).generar(parametros["semilla"], generaciones=parametros["generaciones"])
    simultaneas = simultaneas_de(cartelera.funciones)
    resultado = {
        "fecha": datetime.now().astimezone().isoformat(timespec="seconds"),
        "parametros": parametros,
        "utilidad": round(utilidad(cartelera, calendario, red), 2),
        "funciones": [serializar_funcion(f, s, calendario) for f, s in zip(cartelera.funciones, simultaneas)],
        "convergencia": curva,
    }
    guardar_ultima(resultado)
    return resultado


def guardar_ultima(resultado: dict) -> None:
    """Escritura atómica: primero a un temporal y luego se reemplaza."""
    with guardado_lock:
        temporal = CARTELERA_ULTIMA.with_suffix(".tmp")
        temporal.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
        os.replace(temporal, CARTELERA_ULTIMA)


def leer_ultima() -> dict | None:
    if not CARTELERA_ULTIMA.exists():
        return None
    return json.loads(CARTELERA_ULTIMA.read_text(encoding="utf-8"))


def diagnostico_rb() -> dict:
    total = int(red.conteos.sum())
    return {"entrenada": total > 0, "forma": list(red.conteos.shape), "total_conteos": total, "origen": origen_red}


if FastAPI is not None:
    Dia = Annotated[int, Field(ge=0, le=6)]

    class ParametrosGeneracion(BaseModel):
        """Cuerpo opcional de /api/generar-cartelera. Todo es opcional."""
        feriados: list[Dia] = []
        promociones: list[Dia] = []
        escenario: Literal["E1", "E2", "E3", "E4"] | None = None
        semilla: int | None = None
        generaciones: Annotated[int, Field(ge=0, le=500)] | None = None

    app = FastAPI(title="Orden 66", version="1.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.mount("/posters", StaticFiles(directory=POSTERS), name="posters")

    def iniciar_job(fn):
        job_id = str(uuid4())
        with jobs_lock: jobs[job_id] = {"estado": "pendiente", "progreso": 0}
        def run():
            with jobs_lock: jobs[job_id]["estado"] = "ejecutando"
            try:
                resultado = fn(lambda n: jobs[job_id].update(progreso=n))
                with jobs_lock: jobs[job_id].update(estado="completado", progreso=100, resultado=resultado)
            except Exception as exc:
                with jobs_lock: jobs[job_id].update(estado="error", error=str(exc))
        executor.submit(run)
        return {"job_id": job_id}

    @app.get("/api/estado")
    def estado():
        return {"nombre": "Orden 66", "peliculas": len(config.PELICULAS_BASE), "salas": len(config.SALAS), "jobs": len(jobs)}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/health/rb")
    def health_rb():
        return diagnostico_rb()

    @app.get("/api/jobs/{job_id}")
    def consultar_job(job_id: str):
        if job_id not in jobs: raise HTTPException(404, "Trabajo no encontrado")
        return jobs[job_id]

    @app.get("/api/peliculas")
    def listar_peliculas():
        return catalogo

    @app.post("/api/peliculas")
    async def alta_pelicula(id: str = Form(...), titulo: str = Form(...), duracion: int = Form(...), clasificacion: str = Form(...), formato: str = Form(...), tipo: str = Form(...), semana_cartelera: int = Form(1), poster: UploadFile | None = File(None)):
        destino = None
        if poster:
            destino = POSTERS / f"{id}_{poster.filename}"
            destino.write_bytes(await poster.read())
        pelicula = {"id": id, "titulo": titulo, "duracion": duracion, "clasificacion": clasificacion, "formato": formato, "tipo": tipo, "semana_cartelera": semana_cartelera, "poster": f"/posters/{destino.name}" if destino else None}
        catalogo.append(pelicula)
        return pelicula

    @app.post("/api/generar-cartelera")
    def generar_cartelera(cuerpo: ParametrosGeneracion | None = Body(None), semilla: int = 0, generaciones: int | None = None):
        """Cuerpo JSON opcional (feriados, promociones, escenario, semilla, generaciones).
        Sin cuerpo se comporta como antes, con ``semilla`` y ``generaciones`` por consulta."""
        parametros = resolver_parametros(cuerpo.model_dump() if cuerpo else {}, semilla, generaciones)
        return iniciar_job(lambda progreso: generar(parametros, progreso))

    @app.get("/api/cartelera/ultima")
    def cartelera_ultima():
        ultima = leer_ultima()
        if ultima is None: raise HTTPException(404, "Todavía no se generó ninguna cartelera")
        return ultima

    # Endpoints de adorno: existían como maqueta y no registraban ni simulaban nada.
    # Responden 501 hasta que se implementen de verdad (aprendizaje con ventas reales).
    @app.post("/api/registrar-venta")
    def registrar_venta(pelicula_id: str, sala: str, dia: int, inicio: int, espectadores: int):
        raise HTTPException(501, "No implementado: registrar ventas reales todavía no actualiza la red bayesiana.")

    @app.post("/api/simular-ventas")
    def simular_ventas():
        raise HTTPException(501, "No implementado: la simulación de ventas sobre funciones pasadas todavía no existe en la API.")

    @app.post("/api/benchmark")
    def benchmark(semillas: int = 2):
        def trabajo(progreso):
            from .core.evaluator import ejecutar_experimentos
            filas = ejecutar_experimentos(crear_calendario(), red, range(semillas), destino=ROOT / "results" / "resultados_benchmark.csv", generaciones=1)
            progreso(100); return {"filas": len(filas)}
        return iniciar_job(trabajo)
else:
    app = None
