import type { Vista } from './dominio';

/** Ruta leída del hash: `#/cartelera`, `#/salas?dia=4`, `#/salas/S1?dia=4`, `#/catalogo`, `#/evaluacion`. */
export type Ruta = { vista: Vista; salaId: string | null; dia: number | null };

const VISTAS: Vista[] = ['cartelera', 'salas', 'catalogo', 'evaluacion'];

export function leerRuta(hash = window.location.hash): Ruta {
  const [camino, consulta = ''] = hash.replace(/^#\/?/, '').split('?');
  const partes = camino.split('/').filter(Boolean);
  const vista = VISTAS.includes(partes[0] as Vista) ? (partes[0] as Vista) : 'cartelera';
  const salaId = vista === 'salas' && partes[1] ? decodeURIComponent(partes[1]) : null;
  const valorDia = new URLSearchParams(consulta).get('dia');
  const numero = valorDia === null ? NaN : Number(valorDia);
  const dia = Number.isInteger(numero) && numero >= 0 && numero <= 6 ? numero : null;
  return { vista, salaId, dia };
}

export function hashSalas(dia: number, salaId?: string | null): string {
  return `#/salas${salaId ? `/${encodeURIComponent(salaId)}` : ''}?dia=${dia}`;
}
