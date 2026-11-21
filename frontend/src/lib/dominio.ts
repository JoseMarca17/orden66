import { useEffect, useState } from 'react';

export type Vista = 'cartelera' | 'salas' | 'catalogo' | 'evaluacion';
export type Pelicula = { id: string; titulo: string; duracion: number; clasificacion: string; formato: string; tipo: string; semana_cartelera: number; poster?: string | null };
/** Forma en que la API entrega cada función (`f.__dict__` en backend/api.py). */
export type Funcion = { pelicula: Pelicula; sala: string; dia: number; inicio: number; espectadores?: number | null; ocupacion_esperada?: number | null; probabilidades?: number[] | null };
export type Catalogo = Pelicula[];
export type SalaInfo = { id: string; capacidad: number; formatos: string[]; filas: number; asientos: number };

export const API = 'http://localhost:8000';
export const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'];
export const DIAS_CORTOS = ['LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB', 'DOM'];

/** Salas de backend/core/config.py con su distribución de butacas (filas × asientos). */
export const SALAS: SalaInfo[] = [
  { id: 'S1', capacidad: 80, formatos: ['2D'], filas: 8, asientos: 10 },
  { id: 'S2', capacidad: 80, formatos: ['2D'], filas: 8, asientos: 10 },
  { id: 'S3', capacidad: 140, formatos: ['2D', '3D'], filas: 10, asientos: 14 },
  { id: 'S4', capacidad: 140, formatos: ['2D', '3D'], filas: 10, asientos: 14 },
  { id: 'S5', capacidad: 240, formatos: ['2D', '3D'], filas: 12, asientos: 20 },
  { id: 'S6', capacidad: 200, formatos: ['3D', 'XD'], filas: 10, asientos: 20 },
];
export const salaPorId = (id: string) => SALAS.find((s) => s.id === id);

export const APERTURA = 600;
export const JORNADA = 840; // 10:00 → 24:00
export const LIMPIEZA = 20;
export const UMBRAL_RIESGO = 0.2;
const VALOR_CLASE = [0.15, 0.45, 0.8]; // igual que RedBayesiana.ocupacion_esperada
/** Lo que devuelve la red bayesiana de la API sin entrenar (Laplace con conteos en cero). */
export const PRIOR_UNIFORME = [1 / 3, 1 / 3, 1 / 3];

export type Prediccion = { probs: number[]; ocupacion: number; espectadores: number; capacidad: number; estimada: boolean };

/** Predicción de la RB para una función. Usa los campos de la API si llegan; si no, el prior uniforme. */
export function prediccion(f: Funcion): Prediccion {
  const capacidad = salaPorId(f.sala)?.capacidad ?? 0;
  const probs = f.probabilidades && f.probabilidades.length === 3 ? f.probabilidades : PRIOR_UNIFORME;
  const ocupacion = f.ocupacion_esperada ?? probs.reduce((acc, p, i) => acc + p * VALOR_CLASE[i], 0);
  return { probs, ocupacion, espectadores: Math.round(capacidad * ocupacion), capacidad, estimada: f.ocupacion_esperada == null && !f.probabilidades };
}

export const hora = (minutos: number) => `${String(Math.floor(minutos / 60) % 24).padStart(2, '0')}:${String(minutos % 60).padStart(2, '0')}`;
export const duracionTexto = (minutos: number) => `${Math.floor(minutos / 60)}h ${String(minutos % 60).padStart(2, '0')}m`;
export const fin = (f: Funcion) => f.inicio + f.pelicula.duracion;

export const ETIQUETA_TIPO: Record<string, string> = { familiar_animada: 'Familiar · Animada', superheroes_accion: 'Superhéroes · Acción', otra_extranjera: 'Extranjera', nacional: 'Nacional', terror: 'Terror' };
export const etiquetaTipo = (tipo: string) => ETIQUETA_TIPO[tipo] ?? tipo.replaceAll('_', ' ');

export function gradienteTipo(tipo: string): string {
  if (tipo.includes('familiar')) return 'linear-gradient(160deg, #e8789c 0%, #b8355f 45%, #6b0f24 100%)';
  if (tipo.includes('superheroe')) return 'linear-gradient(160deg, #2f58b8 0%, #3a2a6e 45%, #6b0f24 100%)';
  if (tipo.includes('terror')) return 'linear-gradient(170deg, #6b0f24 0%, #2a040d 55%, #050103 100%)';
  if (tipo.includes('nacional')) return 'linear-gradient(160deg, #1f7a3e 0%, #f5c542 50%, #c8102e 100%)';
  return 'linear-gradient(160deg, #77707c 0%, #4a2a36 50%, #6b0f24 100%)';
}

/** Lunes 00:00 de la semana actual: el día 0 de la cartelera. */
export function inicioSemana(ahora: Date): Date {
  const d = new Date(ahora.getFullYear(), ahora.getMonth(), ahora.getDate());
  d.setDate(d.getDate() - ((d.getDay() + 6) % 7));
  return d;
}
export function fechaDia(ahora: Date, dia: number): Date {
  const d = inicioSemana(ahora);
  d.setDate(d.getDate() + dia);
  return d;
}
export const indiceHoy = (ahora: Date) => (ahora.getDay() + 6) % 7;

/** Minuto del día seleccionado que corresponde a "ahora": antes de abrir si es futuro, después de cerrar si ya pasó. */
export function minutoReferencia(ahora: Date, dia: number): number {
  const hoy = indiceHoy(ahora);
  if (dia < hoy) return 24 * 60 + 60;
  if (dia > hoy) return -1;
  return ahora.getHours() * 60 + ahora.getMinutes();
}
export const haPasado = (f: Funcion, ahora: Date) => f.inicio <= minutoReferencia(ahora, f.dia);

export type EstadoSala = { tipo: 'funcion' | 'limpieza' | 'libre'; funcion?: Funcion };
export function estadoSala(funciones: Funcion[], minuto: number): EstadoSala {
  const actual = funciones.find((f) => f.inicio <= minuto && minuto < fin(f));
  if (actual) return { tipo: 'funcion', funcion: actual };
  const limpieza = funciones.find((f) => fin(f) <= minuto && minuto < fin(f) + LIMPIEZA);
  if (limpieza) return { tipo: 'limpieza', funcion: limpieza };
  return { tipo: 'libre' };
}

/** Hora actual que se refresca sola (para apagar funciones pasadas y el estado de las salas). */
export function useAhora(intervaloMs = 30_000): Date {
  const [ahora, setAhora] = useState(() => new Date());
  useEffect(() => {
    const id = window.setInterval(() => setAhora(new Date()), intervaloMs);
    return () => window.clearInterval(id);
  }, [intervaloMs]);
  return ahora;
}

export const catalogoInicial: Catalogo = ([
  ['P01', 'La Estrella Perdida', 95, 'TP', '2D', 'familiar_animada', 1], ['P02', 'Guardianes del Bosque', 105, 'TP', '3D', 'familiar_animada', 2], ['P03', 'Planeta de Papel', 100, 'TP', '2D', 'familiar_animada', 3], ['P04', 'Titán Cósmico', 150, '+13', 'XD', 'superheroes_accion', 1],
  ['P05', 'Héroes del Amanecer', 140, '+13', '3D', 'superheroes_accion', 2], ['P06', 'Código Invencible', 125, '+13', '2D', 'superheroes_accion', 3], ['P07', 'La Última Señal', 110, '+18', '2D', 'otra_extranjera', 1], ['P08', 'Ciudad de Niebla', 130, '+13', '2D', 'otra_extranjera', 2],
  ['P09', 'Horizonte Azul', 120, '+13', '3D', 'otra_extranjera', 1], ['P10', 'Ecos de Medianoche', 135, '+18', '2D', 'otra_extranjera', 3], ['P11', 'Voces de Bolivia', 115, '+13', '2D', 'nacional', 2], ['P12', 'El Camino de Sal', 98, 'TP', '2D', 'nacional', 1],
] as const).map(([id, titulo, duracion, clasificacion, formato, tipo, semana_cartelera]) => ({ id, titulo, duracion, clasificacion, formato, tipo, semana_cartelera }));
