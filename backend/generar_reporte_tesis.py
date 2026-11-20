"""Genera tablas y figuras listas para incorporar al informe de tesis.

Uso desde ``backend/``::

    python generar_reporte_tesis.py
"""

from dataclasses import replace
from pathlib import Path
import csv
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from scipy.stats import wilcoxon
except ImportError:  # pragma: no cover - mensaje claro al ejecutar el informe
    wilcoxon = None

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent))

from orden66.backend.core import config
from orden66.backend.core.agent import AgenteOrden66
from orden66.backend.core.baselines import m1_manual, m2_aleatoria
from orden66.backend.core.bayesian_net import RedBayesiana
from orden66.backend.core.evaluator import evaluar_cartelera
from orden66.backend.core.genetic_algo import utilidad
from orden66.backend.core.models import Calendario, Pelicula, Sala
from orden66.backend.core.simulator import ocupacion_real


FIGURAS = ROOT / "results" / "figuras"
RESULTS = ROOT / "results"
SEMILLAS = tuple(range(30))
METODOS = ("M1", "M2", "M3")
ESCENARIOS = ("E1", "E2", "E3", "E4")


def crear_calendario(escenario="E1"):
    feriados = frozenset({4}) if escenario == "E2" else frozenset()
    promociones = frozenset({0, 1, 2}) if escenario == "E3" else frozenset()
    return Calendario.crear(
        [Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS],
        [Pelicula(*p) for p in config.PELICULAS_BASE],
        feriados=feriados,
        promociones=promociones,
    )


def cargar_registros():
    ruta = ROOT / "data" / "historial_ventas.csv"
    with ruta.open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    peliculas = {p[0]: p for p in config.PELICULAS_BASE}
    salas = {s.id: s for s in config.SALAS}
    registros = []
    for fila in filas:
        pelicula = peliculas[fila["pelicula_id"]]; sala = salas[fila["sala"]]
        registros.append({
            "dia": int(fila["dia"]), "inicio": int(fila["inicio"]),
            "feriado": int(fila["feriado"]), "promocion": int(fila["promocion"]),
            "tipo": pelicula[5], "semana": int(pelicula[6]),
            "capacidad": sala.capacidad, "simultaneas": 0,
            "ocupacion": float(fila["ocupacion"]),
        })
    return registros


def entrenar_red():
    registros = cargar_registros()
    corte = int(len(registros) * 0.8)
    red = RedBayesiana(); red.entrenar(registros[:corte])
    return red, registros[corte:]


def escenario_y_metodo(escenario, metodo, semilla, red):
    calendario = crear_calendario(escenario)
    if metodo == "M1":
        cartelera = m1_manual(calendario); curva = []
    elif metodo == "M2":
        cartelera = m2_aleatoria(calendario, semilla); curva = []
    else:
        cartelera, curva = AgenteOrden66(calendario, red).generar(semilla=semilla)
    return calendario, cartelera, curva


def ejecutar_experimentos(red):
    filas = []
    curvas = {escenario: [] for escenario in ESCENARIOS}
    total = len(ESCENARIOS) * len(SEMILLAS) * len(METODOS); actual = 0
    for escenario in ESCENARIOS:
        for semilla in SEMILLAS:
            for metodo in METODOS:
                inicio = time.perf_counter()
                calendario, cartelera, curva = escenario_y_metodo(escenario, metodo, semilla, red)
                metricas = evaluar_cartelera(cartelera, calendario, red, semilla, escenario)
                filas.append({"escenario": escenario, "semilla": semilla, "metodo": metodo, "tiempo": time.perf_counter() - inicio, **metricas})
                if metodo == "M3": curvas[escenario].append(curva)
                actual += 1
                if actual % 10 == 0 or actual == total:
                    print(f"  Experimentos: {actual}/{total}")
    return pd.DataFrame(filas), curvas


def media_desv(serie):
    return f"{serie.mean():.2f} ± {serie.std(ddof=1):.2f}"


def tabla_15(df):
    nombres = {"M1": "M1 (Manual)", "M2": "M2 (Aleatorio PSR)", "M3": "M3 (Orden 66)"}
    lineas = [
        "| Escenario | Método | Espect. (RB) | Espect. (simulador) | Ocup. prom. | Func. < 20 % | Restr. | Tiempo (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for escenario in ESCENARIOS:
        for metodo in METODOS:
            bloque = df[(df.escenario == escenario) & (df.metodo == metodo)]
            lineas.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
                escenario, nombres[metodo], media_desv(bloque.esperados), media_desv(bloque.reales),
                media_desv(bloque.ocupacion_promedio * 100), media_desv(bloque.funciones_baja_20 * 100),
                media_desv(bloque.restricciones), media_desv(bloque.tiempo),
            ))
    lineas.append(""); lineas.append("**Wilcoxon pareada M3 vs M2 (espectadores del simulador)**"); lineas.append("")
    lineas.append("| Escenario | Estadístico | p-valor |"); lineas.append("|---|---:|---:|")
    for escenario in ESCENARIOS:
        m2 = df[(df.escenario == escenario) & (df.metodo == "M2")].sort_values("semilla").reales.to_numpy()
        m3 = df[(df.escenario == escenario) & (df.metodo == "M3")].sort_values("semilla").reales.to_numpy()
        if wilcoxon is None:
            estadistico, pvalor = "N/D", "N/D (instalar scipy)"
        else:
            prueba = wilcoxon(m3, m2, alternative="two-sided", method="auto")
            estadistico, pvalor = f"{prueba.statistic:.3f}", f"{prueba.pvalue:.6f}"
        lineas.append(f"| {escenario} | {estadistico} | {pvalor} |")
    texto = "\n".join(lineas)
    (RESULTS / "tabla_15_lista.md").write_text(texto + "\n", encoding="utf-8")
    print("\n" + texto)


def tabla_16(red, test):
    metricas = red.metricas(test)
    texto = "\n".join([
        "| Modelo | Exactitud | Log-loss |", "|---|---:|---:|",
        f"| Red Bayesiana (Laplace) | {metricas['exactitud']:.4f} | {metricas['log_loss']:.4f} |",
        f"| Predictor base (clase más frecuente) | {metricas['exactitud_base']:.4f} | — |",
    ])
    (RESULTS / "tabla_16_lista.md").write_text(texto + "\n", encoding="utf-8")
    print("\n" + texto)


def figura_convergencia(curvas):
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white")
    colores = {"E1": "#1f77b4", "E2": "#d62728", "E3": "#2ca02c", "E4": "#ff7f0e"}
    for escenario, listas in curvas.items():
        if not listas: continue
        longitud = min(len(curva) for curva in listas); matriz = np.array([curva[:longitud] for curva in listas])
        media, desv = matriz.mean(axis=0), matriz.std(axis=0)
        x = np.arange(1, longitud + 1); ax.plot(x, media, label=escenario, color=colores[escenario], linewidth=2); ax.fill_between(x, media - desv, media + desv, color=colores[escenario], alpha=.16)
    ax.set_title("Convergencia del algoritmo genético por escenario", weight="bold"); ax.set_xlabel("Generación"); ax.set_ylabel("Utilidad U(C)"); ax.legend(title="Escenario"); fig.tight_layout(); fig.savefig(FIGURAS / "fig_convergencia_ag.png", dpi=300, facecolor="white"); plt.close(fig)


def figura_barras(df):
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="white"); x = np.arange(len(ESCENARIOS)); width = .25; colores = {"M1": "#9aa4b2", "M2": "#4c78a8", "M3": "#f28e2b"}; etiquetas = {"M1": "M1 (Manual)", "M2": "M2 (Aleatorio PSR)", "M3": "M3 (Orden 66)"}
    for indice, metodo in enumerate(METODOS):
        datos = [df[(df.escenario == e) & (df.metodo == metodo)].reales for e in ESCENARIOS]; medias = [v.mean() for v in datos]; desv = [v.std(ddof=1) for v in datos]
        ax.bar(x + (indice - 1) * width, medias, width, yerr=desv, capsize=4, label=etiquetas[metodo], color=colores[metodo], edgecolor="#243447", linewidth=.5)
    ax.set_xticks(x, ESCENARIOS); ax.set_ylabel("Espectadores reales (simulador)"); ax.set_title("Comparación de métodos por escenario", weight="bold"); ax.legend(); ax.grid(axis="y", alpha=.3); fig.tight_layout(); fig.savefig(FIGURAS / "fig_barras_metodos.png", dpi=300, facecolor="white"); plt.close(fig)


def figura_gantt(calendario, cartelera, red):
    dia = 4; fig, ax = plt.subplots(figsize=(15, 7), facecolor="white"); colores = {p.id: plt.cm.tab20(i % 20) for i, p in enumerate(calendario.peliculas)}
    for y, sala in enumerate(calendario.salas):
        funciones = sorted((f for f in cartelera.funciones if f.dia == dia and f.sala == sala.id), key=lambda f: f.inicio)
        for funcion in funciones:
            inicio = funcion.inicio; dur = funcion.pelicula.duracion; ocup = red.ocupacion_esperada(funcion, calendario) * 100
            ax.barh(y, dur, left=inicio, height=.62, color=colores[funcion.pelicula.id], edgecolor="#27364a", linewidth=.8)
            ax.text(inicio + dur / 2, y, f"{texto_hora(inicio)}\n{funcion.pelicula.titulo[:16]}\n{ocup:.0f}%", ha="center", va="center", fontsize=7, color="black")
            ax.barh(y, 20, left=inicio + dur, height=.62, color="#b8bec7", edgecolor="white", linewidth=.5)
        ax.text(590, y, sala.id, ha="right", va="center", fontsize=9, weight="bold")
    ax.set_xlim(600, 1440); ax.set_xticks(np.arange(600, 1441, 120), [texto_hora(x) for x in np.arange(600, 1441, 120)]); ax.set_yticks(range(len(calendario.salas)), [f"{s.id} · {s.capacidad} butacas" for s in calendario.salas]); ax.invert_yaxis(); ax.set_xlabel("Horario · Viernes del escenario E4"); ax.set_title("Cartelera Gantt con limpieza y ocupación esperada", weight="bold"); ax.grid(axis="x", alpha=.25); fig.tight_layout(); fig.savefig(FIGURAS / "fig_cartelera_gantt.png", dpi=300, facecolor="white"); plt.close(fig)


def texto_hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def main():
    RESULTS.mkdir(parents=True, exist_ok=True); FIGURAS.mkdir(parents=True, exist_ok=True)
    print("ORDEN 66 · REPORTE EXPERIMENTAL DE TESIS"); print(f"Ejecutando {len(ESCENARIOS)} escenarios × {len(METODOS)} métodos × {len(SEMILLAS)} semillas...")
    red, test = entrenar_red(); df, curvas = ejecutar_experimentos(red)
    df.to_csv(RESULTS / "resultados_experimentos.csv", index=False)
    tabla_15(df); tabla_16(red, test)
    cal_e4, cartelera_e4, _ = escenario_y_metodo("E4", "M3", 0, red)
    figura_convergencia(curvas); figura_barras(df); figura_gantt(cal_e4, cartelera_e4, red)
    print("\nArchivos generados:")
    for ruta in (RESULTS / "tabla_15_lista.md", RESULTS / "tabla_16_lista.md", RESULTS / "resultados_experimentos.csv", FIGURAS / "fig_convergencia_ag.png", FIGURAS / "fig_barras_metodos.png", FIGURAS / "fig_cartelera_gantt.png"):
        print(f"  ✓ {ruta.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
