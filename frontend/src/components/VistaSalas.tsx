import { useEffect, useMemo, useRef, useState } from 'react';
import { Armchair, ArrowLeft, Play } from 'lucide-react';
import { SelectorDias } from './SelectorDias';
import { DIAS, JORNADA, SALAS, estadoSala, fechaDia, fin, hora, minutoReferencia, prediccion, salaPorId } from '../lib/dominio';
import type { Funcion } from '../lib/dominio';
import { hashSalas } from '../lib/ruta';
import { anchoFila, contarButacas, planoDeSala } from '../lib/planosSalas';
import type { PlanoSala } from '../lib/planosSalas';

type Props = { funciones: Funcion[]; dia: number; setDia: (dia: number) => void; ahora: Date; generar: () => void; generando: boolean };

const ETIQUETA_ESTADO = { funcion: 'En función', limpieza: 'Limpieza', libre: 'Libre' } as const;

const funcionesDeSala = (funciones: Funcion[], dia: number, salaId: string) =>
  funciones.filter((f) => f.dia === dia && f.sala === salaId).sort((a, b) => a.inicio - b.inicio);

function BotonGenerar({ generar, generando }: { generar: () => void; generando: boolean }) {
  return <button className="btn-dorado" onClick={generar} disabled={generando}><Play size={16} /> {generando ? 'Generando…' : 'Generar cartelera'}</button>;
}

/* ───────── Pantalla 1: cuadrícula "Nuestras salas" (#/salas) ───────── */
export function VistaSalas({ funciones, dia, setDia, ahora, generar, generando }: Props) {
  const minuto = minutoReferencia(ahora, dia);

  return (
    <div className="vista-salas">
      <header className="encabezado-sobrio">
        <h1>NUESTRAS SALAS</h1>
        <p>{DIAS[dia]} · ocupación esperada según la red bayesiana</p>
      </header>
      <SelectorDias dia={dia} setDia={setDia} ahora={ahora} sobrio />

      {!funciones.length ? (
        <div className="estado-vacio">
          <Armchair size={30} />
          <h3>Todavía no hay una cartelera generada</h3>
          <p>Genera la cartelera para ver el estado de cada sala, su uso y la ocupación estimada de sus funciones.</p>
          <BotonGenerar generar={generar} generando={generando} />
        </div>
      ) : (
        <section className="grilla-salas">
          {SALAS.map((sala) => {
            const funcs = funcionesDeSala(funciones, dia, sala.id);
            const estado = estadoSala(funcs, minuto);
            const uso = Math.min(1, funcs.reduce((acc, f) => acc + f.pelicula.duracion, 0) / JORNADA);
            const proxima = funcs.find((f) => f.inicio > minuto);
            const ocupProm = funcs.length ? funcs.reduce((acc, f) => acc + prediccion(f).ocupacion, 0) / funcs.length : null;
            return (
              <a key={sala.id} href={hashSalas(dia, sala.id)} className={`tarjeta-sala${sala.formatos.includes('XD') ? ' xd' : ''}`} aria-label={`Sala ${sala.id}: ver detalle y butacas`}>
                <div className="sala-cabecera">
                  <div>
                    <h3>SALA {sala.id}</h3>
                    <p>{sala.capacidad} butacas · {sala.formatos.join(' / ')}</p>
                  </div>
                  <span className={`estado-sala ${estado.tipo}`}>{ETIQUETA_ESTADO[estado.tipo]}</span>
                </div>
                <div className="uso">
                  <div className="uso-etiqueta"><span>Uso de la sala</span><b>{Math.round(uso * 100)} %</b></div>
                  <div className="uso-barra"><i style={{ width: `${uso * 100}%` }} /></div>
                </div>
                <dl className="sala-datos">
                  <div><dt>Próxima función</dt><dd>{proxima ? <><b>{hora(proxima.inicio)}</b> {proxima.pelicula.titulo}</> : 'Sin más funciones'}</dd></div>
                  <div><dt>Ocupación esperada</dt><dd className="cifra">{ocupProm === null ? '—' : `${Math.round(ocupProm * 100)} %`}</dd></div>
                </dl>
                <span className="tarjeta-sala-ver">Ver butacas →</span>
              </a>
            );
          })}
        </section>
      )}
    </div>
  );
}

/* ───────── Pantalla 2: página de detalle (#/salas/<id>) ───────── */
export function PaginaSala({ salaId, funciones, dia, setDia, ahora, generar, generando }: Props & { salaId: string }) {
  const sala = salaPorId(salaId);
  const funcs = useMemo(() => funcionesDeSala(funciones, dia, salaId), [funciones, dia, salaId]);
  const minuto = minutoReferencia(ahora, dia);
  const [elegida, setElegida] = useState<Funcion | undefined>();
  const scrollMapa = useRef<HTMLDivElement>(null);
  // Si el plano es más ancho que el recuadro, arranca centrado (se ve el eje de la sala y ambos costados).
  useEffect(() => {
    const el = scrollMapa.current;
    if (el) el.scrollLeft = (el.scrollWidth - el.clientWidth) / 2;
  }, [salaId, elegida]);
  // Al cambiar de día o regenerar la cartelera, vuelve a la próxima función de la sala.
  useEffect(() => setElegida(funcs.find((f) => fin(f) > minutoReferencia(new Date(), dia)) ?? funcs[0]), [funcs, dia]);
  const pred = elegida ? prediccion(elegida) : null;
  const fecha = fechaDia(ahora, dia).toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long' });

  const navegacion = (
    <nav className="nav-detalle" aria-label="Ubicación">
      <a className="btn-contorno" href={hashSalas(dia)}><ArrowLeft size={16} /> Volver a salas</a>
      <ol className="migas">
        <li>ORDEN 66</li>
        <li><a href={hashSalas(dia)}>SALAS</a></li>
        <li aria-current="page">SALA {salaId.toUpperCase()}</li>
      </ol>
    </nav>
  );

  if (!sala) {
    return (
      <div className="pagina-sala">
        {navegacion}
        <div className="estado-vacio">
          <Armchair size={30} />
          <h3>La sala “{salaId}” no existe</h3>
          <p>Las salas disponibles son {SALAS.map((s) => s.id).join(', ')}.</p>
          <a className="btn-dorado" href={hashSalas(dia)}><ArrowLeft size={16} /> Volver a salas</a>
        </div>
      </div>
    );
  }

  const plano = planoDeSala(sala);
  return (
    <div className="pagina-sala">
      {navegacion}

      <header className="encabezado-sala">
        <h1>SALA {sala.id}</h1>
        <p className="plano-descripcion">{plano.descripcion}</p>
        <p>{sala.formatos.join(' / ')} · {plano.filas.length} filas · {contarButacas(plano)} butacas</p>
        <p className="encabezado-dia">{fecha}</p>
      </header>
      <SelectorDias dia={dia} setDia={setDia} ahora={ahora} sobrio />

      {!funciones.length ? (
        <div className="estado-vacio">
          <Armchair size={30} />
          <h3>No hay una cartelera generada</h3>
          <p>La cartelera se guarda en memoria y se pierde al recargar la página. Genérala para ver las funciones y las butacas de esta sala.</p>
          <div className="acciones-vacio">
            <BotonGenerar generar={generar} generando={generando} />
            <a className="btn-contorno" href={hashSalas(dia)}><ArrowLeft size={16} /> Volver a salas</a>
          </div>
        </div>
      ) : !funcs.length ? (
        <div className="estado-vacio">
          <Armchair size={30} />
          <h3>Sin funciones el {DIAS[dia].toLowerCase()}</h3>
          <p>Esta sala no tiene funciones programadas ese día. Elige otro día o vuelve a la lista de salas.</p>
          <a className="btn-contorno" href={hashSalas(dia)}><ArrowLeft size={16} /> Volver a salas</a>
        </div>
      ) : (
        <>
          <div className="selector-funciones" role="tablist" aria-label="Funciones de la sala">
            {funcs.map((f) => (
              <button key={f.inicio} role="tab" aria-selected={elegida === f} className={`${elegida === f ? 'activo' : ''}${fin(f) <= minuto ? ' pasada' : ''}`} onClick={() => setElegida(f)}>
                <b>{hora(f.inicio)}</b><span>{f.pelicula.titulo}</span>
              </button>
            ))}
          </div>

          {elegida && pred && (
            <>
              <div className="datos-funcion">
                <div><span>Película</span><b>{elegida.pelicula.titulo}</b><small>{elegida.pelicula.clasificacion} · {elegida.pelicula.formato}</small></div>
                <div><span>Horario</span><b>{hora(elegida.inicio)} – {hora(fin(elegida))}</b><small>{elegida.pelicula.duracion} min + 20 min de limpieza</small></div>
                <div><span>Espectadores esperados</span><b>{pred.espectadores} / {pred.capacidad}</b><small>{Math.round(pred.ocupacion * 100)} % de ocupación</small></div>
                <div>
                  <span>P(baja · media · alta)</span>
                  <div className="barra-prob" role="img" aria-label={`Baja ${Math.round(pred.probs[0] * 100)} %, media ${Math.round(pred.probs[1] * 100)} %, alta ${Math.round(pred.probs[2] * 100)} %`}>
                    {pred.probs.map((p, i) => <i key={i} className={`prob-${i}`} style={{ width: `${p * 100}%` }} />)}
                  </div>
                  <small className="prob-leyenda">{pred.probs.map((p) => `${Math.round(p * 100)} %`).join(' · ')}</small>
                </div>
              </div>
              {pred.estimada && <p className="nota">La API no envía la predicción por función; se muestra la de su red bayesiana sin entrenar (probabilidades uniformes).</p>}

              <section className="sala-mapa" aria-label="Mapa de butacas">
                <div className="mapa-scroll" ref={scrollMapa}>
                  <div className="mapa-lienzo">
                    <div className="pantalla"><span>PANTALLA</span></div>
                    <MapaButacas plano={plano} ocupadas={pred.espectadores} semilla={`${elegida.dia}-${elegida.sala}-${elegida.inicio}`} />
                  </div>
                </div>
                <div className="leyenda-butacas">
                  <span><Butaca className="butaca ocupada" /> Ocupada (estimación)</span>
                  <span><Butaca className="butaca" /> Libre</span>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </div>
  );
}

/** Ícono de butaca: respaldo, asiento y apoyabrazos. */
function Butaca({ className, titulo }: { className?: string; titulo?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      {titulo && <title>{titulo}</title>}
      <path d="M6.5 3h11A2.5 2.5 0 0 1 20 5.5V13H4V5.5A2.5 2.5 0 0 1 6.5 3Z" />
      <rect x="1.5" y="10" width="3.5" height="9" rx="1.5" />
      <rect x="19" y="10" width="3.5" height="9" rx="1.5" />
      <rect x="5" y="13.5" width="14" height="5" rx="1.5" />
      <rect x="6.5" y="18.5" width="2" height="3" rx=".6" />
      <rect x="15.5" y="18.5" width="2" height="3" rx=".6" />
    </svg>
  );
}

/** Semiancho (en butacas) de la zona central del plano: el bloque del medio, o la fila entera si tiene pasillo al centro. */
function semianchoCentral(plano: PlanoSala) {
  let maximo = 0;
  for (const fila of plano.filas) {
    if (fila.length === 1) continue;
    const ancho = fila.length % 2 === 1 ? fila[(fila.length - 1) / 2] : anchoFila(fila);
    maximo = Math.max(maximo, ancho / 2);
  }
  return maximo || Math.max(...plano.filas.map(anchoFila)) / 2;
}

/**
 * Mapa visual del plano de la sala. Las butacas ocupadas son una estimación (espectadores esperados):
 * primero el bloque central en filas medias y traseras, luego los costados y adelante. No representa ventas reales.
 */
/** Generador pseudoaleatorio determinista (mulberry32) sembrado con un texto. */
function aleatorioCon(semilla: string) {
  let h = 2166136261;
  for (let i = 0; i < semilla.length; i++) h = Math.imul(h ^ semilla.charCodeAt(i), 16777619);
  return () => {
    h = (h + 0x6d2b79f5) | 0;
    let t = Math.imul(h ^ (h >>> 15), 1 | h);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Variación leve del orden de llenado: misma función (día + sala + hora) → mismo mapa. */
const VARIACION_MAPA = 0.18;

function MapaButacas({ plano, ocupadas, semilla }: { plano: PlanoSala; ocupadas: number; semilla: string }) {
  const ocupadasSet = useMemo(() => {
    const azar = aleatorioCon(semilla);
    const filas = plano.filas.length;
    const filaIdeal = (filas - 1) * 0.65;
    const semiCentral = semianchoCentral(plano);
    const semiMaximo = Math.max(...plano.filas.map(anchoFila)) / 2;
    const todas: { clave: string; puntaje: number }[] = [];
    plano.filas.forEach((fila, r) => {
      const inicio = -anchoFila(fila) / 2;
      let pos = 0;
      fila.forEach((bloque, b) => {
        for (let c = 0; c < bloque; c++) {
          const x = Math.abs(inicio + pos + 0.5);
          const lateral = x / (2 * semiMaximo);
          const fueraDelCentro = x > semiCentral ? 0.35 : 0;
          const profundidad = Math.abs(r - filaIdeal) / filas + (r < filaIdeal ? 0.25 * (filaIdeal - r) / filas : 0);
          todas.push({ clave: `${r}-${b}-${c}`, puntaje: lateral + fueraDelCentro + 1.2 * profundidad + VARIACION_MAPA * azar() });
          pos++;
        }
        pos++; // pasillo
      });
    });
    todas.sort((a, b) => a.puntaje - b.puntaje);
    return new Set(todas.slice(0, Math.max(0, Math.min(ocupadas, todas.length))).map((x) => x.clave));
  }, [plano, ocupadas, semilla]);

  const anchoMaximo = Math.max(...plano.filas.map((f) => f.reduce((a, b) => a + b, 0)));
  const letra = (r: number) => String.fromCharCode(65 + r);
  return (
    <div className={`mapa-butacas ${anchoMaximo >= 20 ? 'compacta' : 'amplia'}`}>
      {plano.filas.map((fila, r) => {
        let numero = 0;
        return (
          <div key={r} className="fila-butacas">
            <span className="fila-letra">{letra(r)}</span>
            {fila.map((bloque, b) => [
              b > 0 && <span key={`p${b}`} className="pasillo" />,
              ...Array.from({ length: bloque }, (_, c) => {
                numero++;
                const ocupada = ocupadasSet.has(`${r}-${b}-${c}`);
                return <Butaca key={`${b}-${c}`} className={`butaca${ocupada ? ' ocupada' : ''}`} titulo={`${letra(r)}-${numero}${ocupada ? ' · ocupada (estimación)' : ''}`} />;
              }),
            ])}
            <span className="fila-letra">{letra(r)}</span>
          </div>
        );
      })}
    </div>
  );
}
