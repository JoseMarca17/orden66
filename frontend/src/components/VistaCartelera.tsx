import { useEffect, useMemo, useState } from 'react';
import { Play, TriangleAlert, X } from 'lucide-react';
import { MarcoLuces } from './MarcoLuces';
import { SelectorDias } from './SelectorDias';
import { Letrero } from './Letrero';
import { ChipsHorario } from './ChipsHorario';
import { API, DIAS, UMBRAL_RIESGO, duracionTexto, etiquetaTipo, fechaDia, gradienteTipo, prediccion } from '../lib/dominio';
import type { Catalogo, Funcion, Pelicula } from '../lib/dominio';
import { urlPoster } from '../lib/posters';

type Props = { catalogo: Catalogo; funciones: Funcion[]; convergencia: number[]; dia: number; setDia: (dia: number) => void; estado: string; generando: boolean; generar: () => void; ahora: Date };

const formatoNumero = (n: number) => Math.round(n).toLocaleString('es-BO');

export function VistaCartelera({ catalogo, funciones, convergencia, dia, setDia, estado, generando, generar, ahora }: Props) {
  const [detalle, setDetalle] = useState<Pelicula | null>(null);
  const delDia = useMemo(() => funciones.filter((f) => f.dia === dia).sort((a, b) => a.inicio - b.inicio), [funciones, dia]);
  const predicciones = useMemo(() => delDia.map(prediccion), [delDia]);
  const esperadosDia = predicciones.reduce((acc, p) => acc + p.espectadores, 0);
  const enRiesgo = predicciones.filter((p) => p.ocupacion < UMBRAL_RIESGO).length;
  const utilidad = convergencia.length ? convergencia[convergencia.length - 1] : null;
  const hayCartelera = funciones.length > 0;

  const porId = useMemo(() => new Map(catalogo.map((p) => [p.id, p])), [catalogo]);
  const peliculas = useMemo(() => {
    if (!hayCartelera) return catalogo;
    const ids = [...new Set(delDia.map((f) => f.pelicula.id))];
    return ids.map((id) => porId.get(id) ?? delDia.find((f) => f.pelicula.id === id)!.pelicula);
  }, [hayCartelera, catalogo, delDia, porId]);

  const fecha = fechaDia(ahora, dia).toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  return (
    <>
      <Letrero presenta="ORDEN 66 · PRESENTA" titulo="CARTELERA DE LA SEMANA" fecha={fecha} />

      <div className="barra-acciones">
        <p className="estado-motor"><span className="punto-dorado" /> {estado}</p>
        <button className="btn-dorado" onClick={generar} disabled={generando}><Play size={16} /> {generando ? 'Generando…' : 'Generar cartelera'}</button>
      </div>

      <SelectorDias dia={dia} setDia={setDia} ahora={ahora} />

      <div className="resumen">
        <div className="tarjeta-dato"><span>Utilidad U(C)</span><b>{utilidad === null ? '—' : formatoNumero(utilidad)}</b><small>Semana completa · AG</small></div>
        <div className="tarjeta-dato"><span>Espectadores esperados</span><b>{hayCartelera ? formatoNumero(esperadosDia) : '—'}</b><small>{DIAS[dia]} · red bayesiana</small></div>
        <div className="tarjeta-dato"><span>Funciones del día</span><b>{hayCartelera ? delDia.length : '—'}</b><small>{hayCartelera ? `${new Set(delDia.map((f) => f.sala)).size} de 6 salas activas` : 'Sin cartelera generada'}</small></div>
        <div className="tarjeta-dato"><span>Funciones en riesgo</span><b>{hayCartelera ? enRiesgo : '—'}</b><small>Ocupación esperada &lt; 20 %</small></div>
      </div>

      <h2 className="titulo-seccion">EN EXHIBICIÓN</h2>
      {hayCartelera && !delDia.length && <p className="aviso-vacio">No hay funciones programadas para el {DIAS[dia].toLowerCase()}.</p>}
      <section className="grilla-peliculas">
        {peliculas.map((p) => {
          const funcs = delDia.filter((f) => f.pelicula.id === p.id);
          const esperado = funcs.reduce((acc, f) => acc + prediccion(f).espectadores, 0);
          return (
            <MarcoLuces key={p.id} arriba={10} lado={5} className="marco-pelicula">
              <article className="pelicula">
                <Poster pelicula={p} />
                <div className="pelicula-cuerpo">
                  <p className="pelicula-meta">{etiquetaTipo(p.tipo)} · {duracionTexto(p.duracion)}</p>
                  <div className="chips">
                    <ChipsHorario funciones={funcs} ahora={ahora} />
                    {!funcs.length && <span className="chips-vacio">Genera la cartelera para ver horarios</span>}
                  </div>
                  <p className="esperado">Esperado hoy: <b>{hayCartelera ? `${formatoNumero(esperado)} esp.` : '—'}</b></p>
                  <button className="btn-dorado ancho" onClick={() => setDetalle(p)}>VER DETALLES</button>
                </div>
              </article>
            </MarcoLuces>
          );
        })}
      </section>

      {detalle && <DetallePelicula pelicula={detalle} funciones={funciones.filter((f) => f.pelicula.id === detalle.id)} ahora={ahora} cerrar={() => setDetalle(null)} />}
    </>
  );
}

/**
 * Póster de una película. Prioridad: el subido desde la API, luego el local `/posters/<id>.jpg`;
 * si ninguno carga, queda el degradado por género. Sin `alto` mantiene la proporción 2:3.
 */
export function Poster({ pelicula, alto }: { pelicula: Pelicula; alto?: number }) {
  const [fallidas, setFallidas] = useState<string[]>([]);
  const fuentes = [pelicula.poster ? `${API}${pelicula.poster}` : null, urlPoster(pelicula.id)];
  const src = fuentes.find((f): f is string => !!f && !fallidas.includes(f));
  return (
    <div className="poster" style={{ background: gradienteTipo(pelicula.tipo), height: alto, aspectRatio: alto ? 'auto' : undefined }}>
      {src && <img key={src} src={src} alt="" loading="lazy" decoding="async" onError={() => setFallidas((a) => [...a, src])} />}
      <span className="badge-clasif">{pelicula.clasificacion}</span>
      <span className="badge-formato">{pelicula.formato}</span>
      <div className="poster-pie">
        {pelicula.semana_cartelera === 1 && <span className="estreno">ESTRENO</span>}
        <h3>{pelicula.titulo}</h3>
      </div>
    </div>
  );
}

/**
 * Modal de detalle de una película con sus horarios de la semana. Lo usan el admin y la cartelera pública;
 * con `publico` oculta todo lo interno (ID, semana en cartelera, espectadores esperados) y muestra el aviso +18.
 */
export function DetallePelicula({ pelicula, funciones, ahora, cerrar, publico = false }: { pelicula: Pelicula; funciones: Funcion[]; ahora: Date; cerrar: () => void; publico?: boolean }) {
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && cerrar();
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [cerrar]);
  const semana = publico ? 0 : funciones.reduce((acc, f) => acc + prediccion(f).espectadores, 0);
  return (
    <div className="modal-fondo" onClick={cerrar}>
      <div className="modal detalle-pelicula" role="dialog" aria-modal="true" aria-label={pelicula.titulo} onClick={(e) => e.stopPropagation()}>
        <button className="btn-icono cerrar" onClick={cerrar} aria-label="Cerrar"><X size={18} /></button>
        <Poster pelicula={pelicula} alto={240} />
        <div className="detalle-cuerpo">
          {publico ? (
            <>
              <p className="pelicula-meta">{etiquetaTipo(pelicula.tipo)} · {duracionTexto(pelicula.duracion)}</p>
              {pelicula.clasificacion === '+18' && <p className="aviso-edad"><TriangleAlert size={16} /> Solo mayores de 18 años</p>}
            </>
          ) : (
            <>
              <p className="pelicula-meta">{pelicula.id} · {etiquetaTipo(pelicula.tipo)} · {duracionTexto(pelicula.duracion)} · Semana {pelicula.semana_cartelera} en cartelera</p>
              <p className="esperado">Esperado en la semana: <b>{funciones.length ? `${formatoNumero(semana)} esp.` : '—'}</b></p>
            </>
          )}
          {funciones.length ? DIAS.map((nombre, d) => {
            const delDia = funciones.filter((f) => f.dia === d).sort((a, b) => a.inicio - b.inicio);
            if (!delDia.length) return null;
            return (
              <div className="detalle-dia" key={nombre}>
                <span>{nombre}</span>
                <div className="chips"><ChipsHorario funciones={delDia} ahora={ahora} /></div>
              </div>
            );
          }) : <p className="aviso-vacio">{publico ? 'Esta película no tiene funciones esta semana.' : 'Esta película aún no tiene funciones. Genera la cartelera.'}</p>}
        </div>
      </div>
    </div>
  );
}
