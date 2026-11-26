"""Genera tablas y figuras listas para incorporar al informe de tesis.

Uso desde ``backend/``::

    python generar_reporte_tesis.py                       # 10 semillas, 40 generaciones
    python generar_reporte_tesis.py --semillas 30         # más semillas por escenario (~11 h)
    python generar_reporte_tesis.py --medir 3             # solo mide el tiempo y proyecta el total
"""

from pathlib import Path
import argparse
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
from orden66.backend.core.evaluator import evaluar_cartelera
from orden66.backend.core.historial import entrenar_desde_historial
from orden66.backend.core.models import Calendario, Pelicula, Sala, simultaneas_de


FIGURAS = ROOT / "results" / "figuras"
RESULTS = ROOT / "results"
ANTERIOR = RESULTS / "anterior"
RUTA_M1 = ROOT / "data" / "cartelera_manual_m1.json"
# 30 semillas tardan ~11 h con población 50 y 40 generaciones (~320 s por corrida de M3);
# se usan 10 por escenario (~3.6 h). Configurable con --semillas.
SEMILLAS_REPORTE = 10
METODOS = ("M1", "M2", "M3")
ESCENARIOS = ("E1", "E2", "E3", "E4")
# Generaciones del AG en el informe (producción usa config.GENERACIONES_AG = 100).
# Configurable con --generaciones.
GENERACIONES_REPORTE = 40
SEMILLAS = tuple(range(SEMILLAS_REPORTE))


def crear_calendario(escenario="E1"):
    feriados = frozenset({4}) if escenario == "E2" else frozenset()
    promociones = frozenset({0, 1, 2}) if escenario == "E3" else frozenset()
    return Calendario.crear(
        [Sala(s.id, s.capacidad, s.formatos) for s in config.SALAS],
        [Pelicula(*p) for p in config.PELICULAS_BASE],
        feriados=feriados,
        promociones=promociones,
    )


def entrenar_red():
    """80 % del historial para entrenar y 20 % para probar (mismo corte que la API)."""
    return entrenar_desde_historial(ROOT / "data" / "historial_ventas.csv", crear_calendario())


def escenario_y_metodo(escenario, metodo, semilla, red):
    calendario = crear_calendario(escenario)
    if metodo == "M1":
        cartelera = m1_manual(calendario, RUTA_M1); curva = []
    elif metodo == "M2":
        cartelera = m2_aleatoria(calendario, semilla); curva = []
    else:
        cartelera, curva = AgenteOrden66(calendario, red).generar(semilla=semilla, generaciones=GENERACIONES_REPORTE)
    return calendario, cartelera, curva


def ejecutar_experimentos(red, escenarios=ESCENARIOS, semillas=None):
    semillas = SEMILLAS if semillas is None else semillas
    filas = []
    curvas = {escenario: [] for escenario in escenarios}
    total = len(escenarios) * len(semillas) * len(METODOS); actual = 0
    for escenario in escenarios:
        for semilla in semillas:
            for metodo in METODOS:
                inicio = time.perf_counter()
                calendario, cartelera, curva = escenario_y_metodo(escenario, metodo, semilla, red)
                metricas = evaluar_cartelera(cartelera, calendario, red, semilla, escenario)
                filas.append({"escenario": escenario, "semilla": semilla, "metodo": metodo, "tiempo": time.perf_counter() - inicio, **metricas})
                if metodo == "M3": curvas[escenario].append(curva)
                actual += 1
                if metodo == "M3" or actual == total:
                    print(f"  Experimentos: {actual}/{total} ({escenario}, semilla {semilla}, M3 en {filas[-1]['tiempo']:.1f} s)", flush=True)
    return pd.DataFrame(filas), curvas


def media_desv(serie):
    return f"{serie.mean():.2f} ± {serie.std(ddof=1):.2f}"


def tabla_15(df):
    nombres = {"M1": "M1 (Manual)", "M2": "M2 (Aleatorio PSR)", "M3": "M3 (Orden 66)"}
    lineas = [
        "| Escenario | Método | Espect. (RB) | Espect. (simulador) | Ocup. prom. | Func. < 20 % | Func. en riesgo | Restr. | Tiempo (s) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for escenario in ESCENARIOS:
        for metodo in METODOS:
            bloque = df[(df.escenario == escenario) & (df.metodo == metodo)]
            lineas.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                escenario, nombres[metodo], media_desv(bloque.esperados), media_desv(bloque.reales),
                media_desv(bloque.ocupacion_promedio * 100), media_desv(bloque.funciones_baja_20 * 100),
                media_desv(bloque.funciones_riesgo * 100), media_desv(bloque.restricciones), media_desv(bloque.tiempo),
            ))
    lineas.append("")
    lineas.append(f"*{len(df.semilla.unique())} semillas por escenario · AG con {GENERACIONES_REPORTE} generaciones y población {config.POBLACION_AG} · "
                  f"«Func. en riesgo» = P(baja) > {config.UMBRAL_RIESGO} (la que penaliza U(C)); «Func. < 20 %» = ocupación esperada < 0.20 (criterio anterior).*")
    lineas.append(""); lineas.append("**Wilcoxon pareada M3 vs M2 (espectadores del simulador)**"); lineas.append("")
    lineas.append("| Escenario | Estadístico | p-valor |"); lineas.append("|---|---:|---:|")
    for escenario in ESCENARIOS:
        estadistico, pvalor = prueba_wilcoxon(df, escenario)
        lineas.append(f"| {escenario} | {estadistico} | {pvalor} |")
    texto = "\n".join(lineas)
    (RESULTS / "tabla_15_lista.md").write_text(texto + "\n", encoding="utf-8")
    print("\n" + texto)


def prueba_wilcoxon(df, escenario):
    m2 = df[(df.escenario == escenario) & (df.metodo == "M2")].sort_values("semilla").reales.to_numpy()
    m3 = df[(df.escenario == escenario) & (df.metodo == "M3")].sort_values("semilla").reales.to_numpy()
    if wilcoxon is None:
        return "N/D", "N/D (instalar scipy)"
    prueba = wilcoxon(m3, m2, alternative="two-sided", method="auto")
    return f"{prueba.statistic:.3f}", f"{prueba.pvalue:.6f}"


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
    simultaneas = dict(zip((f.clave for f in cartelera.funciones), simultaneas_de(cartelera.funciones)))
    dia = 4; fig, ax = plt.subplots(figsize=(15, 7), facecolor="white"); colores = {p.id: plt.cm.tab20(i % 20) for i, p in enumerate(calendario.peliculas)}
    for y, sala in enumerate(calendario.salas):
        funciones = sorted((f for f in cartelera.funciones if f.dia == dia and f.sala == sala.id), key=lambda f: f.inicio)
        for funcion in funciones:
            inicio = funcion.inicio; dur = funcion.pelicula.duracion; ocup = red.ocupacion_esperada(funcion, calendario, simultaneas[funcion.clave]) * 100
            ax.barh(y, dur, left=inicio, height=.62, color=colores[funcion.pelicula.id], edgecolor="#27364a", linewidth=.8)
            ax.text(inicio + dur / 2, y, f"{texto_hora(inicio)}\n{funcion.pelicula.titulo[:16]}\n{ocup:.0f}%", ha="center", va="center", fontsize=7, color="black")
            ax.barh(y, 20, left=inicio + dur, height=.62, color="#b8bec7", edgecolor="white", linewidth=.5)
        ax.text(590, y, sala.id, ha="right", va="center", fontsize=9, weight="bold")
    ax.set_xlim(600, 1440); ax.set_xticks(np.arange(600, 1441, 120), [texto_hora(x) for x in np.arange(600, 1441, 120)]); ax.set_yticks(range(len(calendario.salas)), [f"{s.id} · {s.capacidad} butacas" for s in calendario.salas]); ax.invert_yaxis(); ax.set_xlabel("Horario · Viernes del escenario E4"); ax.set_title("Cartelera Gantt con limpieza y ocupación esperada", weight="bold"); ax.grid(axis="x", alpha=.25); fig.tight_layout(); fig.savefig(FIGURAS / "fig_cartelera_gantt.png", dpi=300, facecolor="white"); plt.close(fig)


def texto_hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def medir(red, semillas_medidas):
    """Corre E1 con unas pocas semillas y proyecta el tiempo de 4 escenarios × N semillas."""
    inicio = time.perf_counter()
    df, _ = ejecutar_experimentos(red, ("E1",), tuple(range(semillas_medidas)))
    total = time.perf_counter() - inicio
    por_semilla = total / semillas_medidas
    print(f"\nE1 con {semillas_medidas} semillas: {total / 60:.1f} min ({por_semilla:.0f} s por semilla con M1+M2+M3)")
    print(df.groupby("metodo").tiempo.mean().round(1).to_string())
    for n in (10, 30):
        print(f"Proyección 4 escenarios × {n} semillas: {por_semilla * 4 * n / 3600:.2f} h")


def _metricas_rb_anteriores():
    """Lee exactitud, log-loss y base de results/anterior/tabla_16_lista.md."""
    valores = {}
    for linea in (ANTERIOR / "tabla_16_lista.md").read_text(encoding="utf-8").splitlines():
        celdas = [c.strip() for c in linea.strip("|").split("|")]
        if celdas[0].startswith("Red Bayesiana"):
            valores["exactitud"], valores["log_loss"] = float(celdas[1]), float(celdas[2])
        elif celdas[0].startswith("Predictor base"):
            valores["exactitud_base"] = float(celdas[1])
    return valores


def comparacion(df, metricas_rb):
    """Arma results/comparacion.md con la tabla anterior y la nueva lado a lado."""
    anterior = pd.read_csv(ANTERIOR / "resultados_experimentos.csv")
    rb_ant = _metricas_rb_anteriores()
    nombres = {"M1": "M1 (Manual)", "M2": "M2 (Aleatorio PSR)", "M3": "M3 (Orden 66)"}
    par = lambda a, b: f"{a} → **{b}**"
    l = ["# Comparación de resultados: anterior vs. nuevo", "",
         "Resultados anteriores copiados en `results/anterior/`. Qué cambió entre una corrida y otra:", "",
         "- **Red bayesiana:** tabla con la forma correcta `(3,3,3,2,2,4,3,3,2)` (antes mezclaba noche con tarde, nacional con extranjera y sala grande con mediana), funciones simultáneas reales e historial regenerado (misma semilla 0, 20 000 filas) con feriados (8 % por día) y semanas con promoción lunes a miércoles (15 %).",
         f"- **U(C):** penaliza P(baja) > {config.UMBRAL_RIESGO} en lugar de ocupación esperada < 0.20 (λ = {config.LAMBDA:g} sin cambios).",
         f"- **AG (M3):** población inicial de {config.POBLACION_AG} carteleras distintas del PSR (antes 1 copiada 50 veces) y {GENERACIONES_REPORTE} generaciones (antes 1).",
         "- **M1:** cartelera manual por reglas (`data/cartelera_manual_m1.json`, 140 funciones); antes era una cartelera del PSR con semilla 0.",
         f"- **Semillas:** {len(anterior.semilla.unique())} antes, {len(df.semilla.unique())} ahora, por escenario.",
         "- El simulador también cambió: ahora resta público a las funciones simultáneas (×0.65), así que los espectadores «reales» no son comparables 1 a 1 entre corridas; lo comparable es la posición relativa de M1, M2 y M3 dentro de cada corrida.",
         "", "## Tabla 16 · Red bayesiana (20 % de prueba)", "",
         "| Métrica | Anterior | Nuevo |", "|---|---:|---:|",
         f"| Exactitud | {rb_ant.get('exactitud', float('nan')):.4f} | **{metricas_rb['exactitud']:.4f}** |",
         f"| Log-loss | {rb_ant.get('log_loss', float('nan')):.4f} | **{metricas_rb['log_loss']:.4f}** |",
         f"| Exactitud del predictor base | {rb_ant.get('exactitud_base', float('nan')):.4f} | **{metricas_rb['exactitud_base']:.4f}** |",
         "", "## Tabla 15 · Métodos por escenario (media ± desv.)", "",
         "Cada celda: anterior → **nuevo**. «Func. en riesgo» no existía antes.", "",
         "| Escenario | Método | Espect. (RB) | Espect. (simulador) | Ocup. prom. (%) | Func. < 20 % | Func. en riesgo (%) | Tiempo (s) |",
         "|---|---|---:|---:|---:|---:|---:|---:|"]
    for escenario in ESCENARIOS:
        for metodo in METODOS:
            a = anterior[(anterior.escenario == escenario) & (anterior.metodo == metodo)]
            n = df[(df.escenario == escenario) & (df.metodo == metodo)]
            l.append(f"| {escenario} | {nombres[metodo]} | {par(media_desv(a.esperados), media_desv(n.esperados))} | {par(media_desv(a.reales), media_desv(n.reales))} | "
                     f"{par(media_desv(a.ocupacion_promedio * 100), media_desv(n.ocupacion_promedio * 100))} | {par(media_desv(a.funciones_baja_20 * 100), media_desv(n.funciones_baja_20 * 100))} | "
                     f"**{media_desv(n.funciones_riesgo * 100)}** | {par(media_desv(a.tiempo), media_desv(n.tiempo))} |")
    l += ["", "## Ventaja de M3 sobre M2 y prueba de Wilcoxon pareada (espectadores del simulador)", "",
          "| Escenario | M3 − M2 anterior | M3 − M2 nuevo | Wilcoxon anterior (estad. / p) | Wilcoxon nuevo (estad. / p) |",
          "|---|---:|---:|---:|---:|"]
    diferencia = lambda d, e: (d[(d.escenario == e) & (d.metodo == "M3")].sort_values("semilla").reales.to_numpy()
                               - d[(d.escenario == e) & (d.metodo == "M2")].sort_values("semilla").reales.to_numpy()).mean()
    for escenario in ESCENARIOS:
        ea, pa = prueba_wilcoxon(anterior, escenario); en, pn = prueba_wilcoxon(df, escenario)
        l.append(f"| {escenario} | {diferencia(anterior, escenario):+.1f} | **{diferencia(df, escenario):+.1f}** | {ea} / {pa} | **{en} / {pn}** |")
    l += ["", "## Ventaja de M3 sobre M1 (espectadores del simulador)", "",
          "| Escenario | M3 − M1 anterior | M3 − M1 nuevo |", "|---|---:|---:|"]
    media = lambda d, e, m: d[(d.escenario == e) & (d.metodo == m)].reales.mean()
    for escenario in ESCENARIOS:
        l.append(f"| {escenario} | {media(anterior, escenario, 'M3') - media(anterior, escenario, 'M1'):+.1f} | **{media(df, escenario, 'M3') - media(df, escenario, 'M1'):+.1f}** |")
    (RESULTS / "comparacion.md").write_text("\n".join(l) + "\n", encoding="utf-8")


def main():
    global SEMILLAS, GENERACIONES_REPORTE
    parser = argparse.ArgumentParser(description="Reporte experimental de Orden 66")
    parser.add_argument("--semillas", type=int, default=SEMILLAS_REPORTE, help="semillas por escenario")
    parser.add_argument("--generaciones", type=int, default=GENERACIONES_REPORTE, help="generaciones del AG para M3")
    parser.add_argument("--medir", type=int, metavar="N", help="solo medir el tiempo con N semillas en E1 y proyectar")
    args = parser.parse_args()
    SEMILLAS = tuple(range(args.semillas)); GENERACIONES_REPORTE = args.generaciones
    RESULTS.mkdir(parents=True, exist_ok=True); FIGURAS.mkdir(parents=True, exist_ok=True)
    red, test = entrenar_red()
    if args.medir:
        medir(red, args.medir); return
    print("ORDEN 66 · REPORTE EXPERIMENTAL DE TESIS"); print(f"Ejecutando {len(ESCENARIOS)} escenarios × {len(METODOS)} métodos × {len(SEMILLAS)} semillas, AG con {GENERACIONES_REPORTE} generaciones...")
    df, curvas = ejecutar_experimentos(red)
    df.to_csv(RESULTS / "resultados_experimentos.csv", index=False)
    tabla_15(df); tabla_16(red, test)
    cal_e4, cartelera_e4, _ = escenario_y_metodo("E4", "M3", 0, red)
    figura_convergencia(curvas); figura_barras(df); figura_gantt(cal_e4, cartelera_e4, red)
    comparacion(df, red.metricas(test))
    print("\nArchivos generados:")
    for ruta in (RESULTS / "tabla_15_lista.md", RESULTS / "tabla_16_lista.md", RESULTS / "resultados_experimentos.csv", RESULTS / "comparacion.md", FIGURAS / "fig_convergencia_ag.png", FIGURAS / "fig_barras_metodos.png", FIGURAS / "fig_cartelera_gantt.png"):
        print(f"  ✓ {ruta.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
