import { useEffect, useMemo, useState } from 'react';
import { Play, X } from 'lucide-react';
import { MarcoLuces } from './MarcoLuces';
import { SelectorDias } from './SelectorDias';
import { API, DIAS, UMBRAL_RIESGO, duracionTexto, etiquetaTipo, fechaDia, gradienteTipo, haPasado, hora, prediccion } from '../lib/dominio';
import type { Catalogo, Funcion, Pelicula } from '../lib/dominio';

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
      <div className="letrero-fila">
        <MarcoLuces arriba={20} lado={5} className="marco-letrero">
          <div className="letrero">
            <p className="letrero-presenta">ORDEN 66 · PRESENTA</p>
            <h1 className="letrero-titulo">CARTELERA DE LA SEMANA</h1>
            <div className="letrero-linea" />
            <p className="letrero-fecha">{fecha}</p>
          </div>
        </MarcoLuces>
        <MarcoLuces arriba={3} lado={12} className="marco-cine">
          <div className="letrero-cine" aria-label="Cine">{['C', 'I', 'N', 'E'].map((l) => <span key={l}>{l}</span>)}</div>
        </MarcoLuces>
      </div>

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
                    {funcs.map((f) => (
                      <span key={`${f.sala}-${f.inicio}`} className={`chip${haPasado(f, ahora) ? ' pasada' : ''}`} title={haPasado(f, ahora) ? 'Función ya iniciada' : undefined}>
                        <b>{hora(f.inicio)}</b><small>{f.sala}</small>
                      </span>
                    ))}
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

export function Poster({ pelicula, alto }: { pelicula: Pelicula; alto?: number }) {
  return (
    <div className="poster" style={{ background: gradienteTipo(pelicula.tipo), height: alto }}>
      {pelicula.poster && <img src={`${API}${pelicula.poster}`} alt="" />}
      <span className="badge-clasif">{pelicula.clasificacion}</span>
      <span className="badge-formato">{pelicula.formato}</span>
      <div className="poster-pie">
        {pelicula.semana_cartelera === 1 && <span className="estreno">ESTRENO</span>}
        <h3>{pelicula.titulo}</h3>
      </div>
    </div>
  );
}

function DetallePelicula({ pelicula, funciones, ahora, cerrar }: { pelicula: Pelicula; funciones: Funcion[]; ahora: Date; cerrar: () => void }) {
  useEffect(() => {
    const tecla = (e: KeyboardEvent) => e.key === 'Escape' && cerrar();
    window.addEventListener('keydown', tecla);
    return () => window.removeEventListener('keydown', tecla);
  }, [cerrar]);
  const semana = funciones.reduce((acc, f) => acc + prediccion(f).espectadores, 0);
  return (
    <div className="modal-fondo" onClick={cerrar}>
      <div className="modal detalle-pelicula" role="dialog" aria-modal="true" aria-label={pelicula.titulo} onClick={(e) => e.stopPropagation()}>
        <button className="btn-icono cerrar" onClick={cerrar} aria-label="Cerrar"><X size={18} /></button>
        <Poster pelicula={pelicula} alto={240} />
        <div className="detalle-cuerpo">
          <p className="pelicula-meta">{pelicula.id} · {etiquetaTipo(pelicula.tipo)} · {duracionTexto(pelicula.duracion)} · Semana {pelicula.semana_cartelera} en cartelera</p>
          <p className="esperado">Esperado en la semana: <b>{funciones.length ? `${formatoNumero(semana)} esp.` : '—'}</b></p>
          {funciones.length ? DIAS.map((nombre, d) => {
            const delDia = funciones.filter((f) => f.dia === d).sort((a, b) => a.inicio - b.inicio);
            if (!delDia.length) return null;
            return (
              <div className="detalle-dia" key={nombre}>
                <span>{nombre}</span>
                <div className="chips">{delDia.map((f) => <span key={`${f.sala}-${f.inicio}`} className={`chip${haPasado(f, ahora) ? ' pasada' : ''}`}><b>{hora(f.inicio)}</b><small>{f.sala}</small></span>)}</div>
              </div>
            );
          }) : <p className="aviso-vacio">Esta película aún no tiene funciones. Genera la cartelera.</p>}
        </div>
      </div>
    </div>
  );
}
