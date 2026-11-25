/**
 * Pósters locales en `public/posters/<id>.jpg` (Vite los sirve desde la raíz).
 * Si el archivo no existe o no carga, el componente Poster vuelve al degradado por género.
 */
export const urlPoster = (id: string) => `/posters/${encodeURIComponent(id)}.jpg`;
