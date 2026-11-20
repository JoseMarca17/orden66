# 🎬 Orden 66

> **Agente inteligente basado en utilidad para generar la cartelera semanal de un cine boliviano.**

Orden 66 combina **Programación de Restricciones**, **Redes Bayesianas** y un **Algoritmo Genético** para construir una cartelera válida, estimar la demanda y seleccionar la programación con mayor utilidad esperada.

---

## ✨ ¿Qué resuelve?

El agente responde de forma automática:

- ¿Qué películas deben proyectarse?
- ¿En qué sala, día y horario?
- ¿Qué cartelera respeta todas las restricciones operativas?
- ¿Qué funciones tienen mayor ocupación esperada?
- ¿Cómo debe aprender el sistema a partir de ventas reales?

La utilidad de una cartelera se calcula como:

```text
U(C) = espectadores esperados − λ × funciones con ocupación menor al 20 %
```

---

## 🧠 Módulos de inteligencia artificial

### 1. PSR — Programación de Restricciones

`backend/core/csp_solver.py`

Genera y repara carteleras usando:

- Backtracking.
- Heurística MRV.
- Desempate por grado.
- Consistencia de nodo.
- Comprobación hacia adelante.
- Reparación de carteleras corruptas.

### 2. Red Bayesiana

`backend/core/bayesian_net.py`

Estima la probabilidad de ocupación:

```text
P(baja), P(media), P(alta)
```

Utiliza conteos NumPy y suavizado de Laplace. Aprende de las ventas reales mediante `actualizar_con_ventas()`.

### 3. Algoritmo Genético

`backend/core/genetic_algo.py`

Optimiza la cartelera mediante:

- Selección por torneo.
- Elitismo.
- Cruce por bloques de días.
- Mutación de película, horario, sala y funciones.
- Reparación automática de individuos inválidos.
- Caché de evaluaciones.

---

## 🏗️ Arquitectura

```text
orden66/
├── backend/
│   ├── core/
│   │   ├── config.py             # Parámetros centralizados
│   │   ├── models.py             # Modelos de dominio
│   │   ├── validator.py          # Restricciones R1–R7
│   │   ├── simulator.py           # Demanda oculta
│   │   ├── csp_solver.py          # PSR
│   │   ├── bayesian_net.py        # Red Bayesiana
│   │   ├── genetic_algo.py        # Algoritmo Genético
│   │   ├── agent.py               # Orquestador
│   │   ├── evaluator.py           # Evaluación experimental
│   │   └── baselines.py           # M1 y M2
│   ├── data/                      # Salas, películas e historial
│   ├── storage/                   # Estado persistente y pósters
│   ├── results/                   # Tablas, CSV y figuras
│   ├── tests/                     # Suite pytest
│   ├── api.py                     # API FastAPI
│   ├── demo_cli.py                # Demo de consola
│   └── generar_reporte_tesis.py   # Tablas y figuras académicas
├── frontend/                      # React + Vite + TypeScript
├── notebooks/                     # Notebook reproducible
└── README.md
```

El núcleo `backend/core/` no depende de FastAPI, React ni lectura de archivos durante los algoritmos.

---

## ⚙️ Instalación

Requisitos:

- Python 3.11 o superior.
- Node.js y npm.

Desde la carpeta `orden66/`:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
```

En Windows:

```powershell
.venv\Scripts\activate
```

Instalar dependencias Python:

```bash
pip install -r backend/requirements.txt
```

Instalar dependencias del frontend:

```bash
cd frontend
npm install
cd ..
```

---

## ✅ Ejecutar las pruebas

```bash
cd backend
pytest -v
```

La suite cubre:

- Restricciones R1–R7.
- Generación y reparación del PSR.
- Entrenamiento y aprendizaje de la Red Bayesiana.
- Utilidad y validez del Algoritmo Genético.
- Integración del agente.

---

## 🖥️ Demo de consola

Desde `backend/`:

```bash
python demo_cli.py
```

Seleccionar escenario:

```bash
python demo_cli.py --escenario E1
python demo_cli.py --escenario E2
python demo_cli.py --escenario E3
python demo_cli.py --escenario E4
```

La demo imprime utilidad, espectadores esperados, cartelera ordenada y aprendizaje en línea con tres funciones reales simuladas.

---

## 📊 Reporte experimental de tesis

Genera las tablas y figuras académicas:

```bash
cd backend
python generar_reporte_tesis.py
```

Archivos generados:

```text
results/tabla_15_lista.md
results/tabla_16_lista.md
results/resultados_experimentos.csv
results/figuras/fig_convergencia_ag.png
results/figuras/fig_barras_metodos.png
results/figuras/fig_cartelera_gantt.png
```

---

## 🌐 Ejecutar la aplicación web

### Backend

Desde `orden66/`:

```bash
source .venv/bin/activate
uvicorn backend.api:app --reload --port 8000
```

API y documentación:

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- Salud: <http://localhost:8000/health>

### Frontend

En otra terminal:

```bash
cd frontend
npm run dev
```

Aplicación:

<http://localhost:5173>

La interfaz incluye:

- Cartelera semanal con timeline por sala.
- Generación asíncrona de carteleras.
- Catálogo y alta de películas con póster.
- Evaluación de convergencia y comparación de métodos.

---

## 📚 Notebook

El anexo reproducible está en:

```text
notebooks/orden66.ipynb
```

Incluye la creación del calendario, generación de una cartelera, red bayesiana y ejecución del agente.

---

## 🎯 Restricciones operativas

El validador independiente comprueba:

| Restricción | Descripción |
|---|---|
| R1 | Formato compatible con la sala |
| R2 | Películas +18 desde las 18:00 |
| R3 | Horario entre 10:00 y 24:00 |
| R4 | Sin solapamientos y con 20 min de limpieza |
| R5 | Mínimo 4 funciones por película |
| R6 | Máximo 8 funciones diarias y 30 semanales |
| R7 | Una posición por función |

---

## 🔁 Flujo del agente

```text
Percibir
   ↓
Generar cartelera válida con PSR
   ↓
Estimar demanda con Red Bayesiana
   ↓
Optimizar utilidad con Algoritmo Genético
   ↓
Entregar cartelera
   ↓
Aprender de ventas reales
   ↓
Recalcular
```

---

## 📌 Reproducibilidad

Todas las operaciones importantes reciben una semilla explícita. Esto permite repetir experimentos, comparar métodos y reconstruir los resultados de la tesis.

Los parámetros centrales están definidos únicamente en:

```text
backend/core/config.py
```
