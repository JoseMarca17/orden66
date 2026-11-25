import type { SalaInfo } from './dominio';

/**
 * Plano visual de una sala. Cada fila (de la pantalla hacia atrás) es una lista de bloques
 * de butacas; entre dos bloques hay un pasillo. Todas las filas se centran sobre el mismo eje.
 * Es solo una representación visual: no cambia la capacidad que usa el backend.
 */
export type Fila = number[];
export type PlanoSala = { descripcion: string; filas: Fila[] };

const repetir = (n: number, fila: Fila): Fila[] => Array.from({ length: n }, () => [...fila]);

const PLANOS: Record<string, PlanoSala> = {
  S1: { descripcion: 'Dos bloques con pasillo central', filas: repetir(8, [5, 5]) },
  S2: { descripcion: 'Bloque central con pasillos laterales', filas: repetir(8, [2, 6, 2]) },
  S3: { descripcion: 'Dos bloques con pasillo central', filas: repetir(10, [7, 7]) },
  S4: {
    descripcion: 'Bloques laterales y última fila corrida',
    filas: [...repetir(9, [3, 8, 3]), [14]],
  },
  S5: {
    descripcion: 'Sala grande que se ensancha hacia atrás',
    filas: [...repetir(8, [2, 14, 2]), ...repetir(3, [4, 14, 4]), [30]],
  },
  S6: {
    descripcion: 'Bloque central adelante y bloques laterales atrás',
    filas: [...repetir(6, [18]), ...repetir(3, [2, 18, 2]), [26]],
  },
};

export const contarButacas = (plano: PlanoSala) =>
  plano.filas.reduce((total, fila) => total + fila.reduce((a, b) => a + b, 0), 0);

/** Cuadrícula simple de antes: filas × asientos con un pasillo al medio. */
const cuadriculaSimple = (sala: SalaInfo): PlanoSala => ({
  descripcion: 'Cuadrícula con pasillo central',
  filas: repetir(sala.filas, [Math.ceil(sala.asientos / 2), Math.floor(sala.asientos / 2)]),
});

const cache = new Map<string, PlanoSala>();

/** Plano de la sala; si no existe o su total no coincide con la capacidad, usa la cuadrícula simple. */
export function planoDeSala(sala: SalaInfo): PlanoSala {
  const guardado = cache.get(sala.id);
  if (guardado) return guardado;
  let plano = PLANOS[sala.id];
  if (!plano) {
    plano = cuadriculaSimple(sala);
  } else if (contarButacas(plano) !== sala.capacidad) {
    console.warn(`Plano de ${sala.id}: ${contarButacas(plano)} butacas, pero la capacidad es ${sala.capacidad}. Se usa la cuadrícula simple.`);
    plano = cuadriculaSimple(sala);
  }
  cache.set(sala.id, plano);
  return plano;
}

/** Ancho de una fila en unidades de butaca (cada pasillo cuenta como una butaca). */
export const anchoFila = (fila: Fila) => fila.reduce((a, b) => a + b, 0) + fila.length - 1;
