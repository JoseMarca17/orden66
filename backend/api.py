"""API HTTP de Orden 66. El motor de IA permanece en backend.core."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from uuid import uuid4
import json

try:
    from fastapi import FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
except ImportError:  # Permite importar el núcleo sin instalar la capa web.
    FastAPI = None

from .core import config
from .core.agent import AgenteOrden66
from .core.bayesian_net import RedBayesiana
from .core.models import Calendario, Pelicula, Sala
from .core.simulator import ocupacion_real

ROOT = Path(__file__).resolve().parent
POSTERS = ROOT / "storage" / "posters"
POSTERS.mkdir(parents=True, exist_ok=True)
jobs, jobs_lock = {}, Lock()
executor = ThreadPoolExecutor(max_workers=2)
catalogo = [dict(zip(("id", "titulo", "duracion", "clasificacion", "formato", "tipo", "semana_cartelera"), pelicula)) for pelicula in config.PELICULAS_BASE]


def crear_calendario():
    salas = tuple(Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS)
    peliculas = tuple(Pelicula(*p) for p in config.PELICULAS_BASE)
    return Calendario.crear(salas, peliculas)


if FastAPI is not None:
    app = FastAPI(title="Orden 66", version="1.0.0")
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
    def generar_cartelera(semilla: int = 0, generaciones: int | None = None):
        def trabajo(progreso):
            calendario = crear_calendario(); agente = AgenteOrden66(calendario, RedBayesiana())
            cartelera, curva = agente.generar(semilla, generaciones=generaciones)
            progreso(100)
            return {"funciones": [f.__dict__ | {"pelicula": f.pelicula.__dict__} for f in cartelera.funciones], "convergencia": curva}
        return iniciar_job(trabajo)

    @app.post("/api/registrar-venta")
    def registrar_venta(pelicula_id: str, sala: str, dia: int, inicio: int, espectadores: int):
        return {"registrada": True, "pelicula_id": pelicula_id, "espectadores": espectadores}

    @app.post("/api/simular-ventas")
    def simular_ventas():
        return {"modo": "demostracion", "mensaje": "Las ventas simuladas se generan sobre funciones ya pasadas."}

    @app.post("/api/benchmark")
    def benchmark(semillas: int = 2):
        def trabajo(progreso):
            from .core.evaluator import ejecutar_experimentos
            filas = ejecutar_experimentos(crear_calendario(), RedBayesiana(), range(semillas), destino=ROOT / "results" / "resultados_experimentos.csv", generaciones=1)
            progreso(100); return {"filas": len(filas)}
        return iniciar_job(trabajo)
else:
    app = None
