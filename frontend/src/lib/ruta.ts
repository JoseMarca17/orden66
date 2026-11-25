import type { Vista } from './dominio';

/**
 * Ruta leída del hash: `#/cartelera`, `#/salas?dia=4`, `#/salas/S1?dia=4`, `#/catalogo`, `#/evaluacion`,
 * y la vista pública `#/publico?dia=4`. `#/publico/pelicula/P01` ya no es una página: se lee solo para redirigir
 * a `#/publico` con el modal de esa película abierto.
 */
export type Ruta = { vista: Vista | 'publico'; salaId: string | null; peliculaId: string | null; dia: number | null };

const VISTAS: Vista[] = ['cartelera', 'salas', 'catalogo', 'evaluacion'];

export function leerRuta(hash = window.location.hash): Ruta {
  const [camino, consulta = ''] = hash.replace(/^#\/?/, '').split('?');
  const partes = camino.split('/').filter(Boolean);
  const vista = partes[0] === 'publico' ? 'publico' : VISTAS.includes(partes[0] as Vista) ? (partes[0] as Vista) : 'cartelera';
  const salaId = vista === 'salas' && partes[1] ? decodeURIComponent(partes[1]) : null;
  const peliculaId = vista === 'publico' && partes[1] === 'pelicula' && partes[2] ? decodeURIComponent(partes[2]) : null;
  const valorDia = new URLSearchParams(consulta).get('dia');
  const numero = valorDia === null ? NaN : Number(valorDia);
  const dia = Number.isInteger(numero) && numero >= 0 && numero <= 6 ? numero : null;
  return { vista, salaId, peliculaId, dia };
}

export function hashSalas(dia: number, salaId?: string | null): string {
  return `#/salas${salaId ? `/${encodeURIComponent(salaId)}` : ''}?dia=${dia}`;
}

export function hashPublico(dia: number): string {
  return `#/publico?dia=${dia}`;
}
