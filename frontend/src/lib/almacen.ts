import type { Funcion } from './dominio';

/** Cartelera guardada en el navegador: la comparten la vista del administrador y la pública. */
export type CarteleraGuardada = { generada: string; funciones: Funcion[]; convergencia: number[] };

export const CLAVE_CARTELERA = 'orden66.cartelera';

export function leerCartelera(): CarteleraGuardada | null {
  try {
    const crudo = window.localStorage.getItem(CLAVE_CARTELERA);
    if (!crudo) return null;
    const datos = JSON.parse(crudo) as Partial<CarteleraGuardada>;
    if (!Array.isArray(datos.funciones) || typeof datos.generada !== 'string') return null;
    return { generada: datos.generada, funciones: datos.funciones, convergencia: Array.isArray(datos.convergencia) ? datos.convergencia : [] };
  } catch {
    return null;
  }
}

export function guardarCartelera(funciones: Funcion[], convergencia: number[]): void {
  const datos: CarteleraGuardada = { generada: new Date().toISOString(), funciones, convergencia };
  try {
    window.localStorage.setItem(CLAVE_CARTELERA, JSON.stringify(datos));
  } catch {
    // Almacenamiento bloqueado o lleno: la cartelera sigue en memoria en esta pestaña.
  }
}
