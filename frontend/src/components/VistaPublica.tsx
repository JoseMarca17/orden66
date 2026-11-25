import { useEffect, useMemo, useState } from 'react';
import { CalendarDays, Film } from 'lucide-react';
import { MarcoLuces } from './MarcoLuces';
import { SelectorDias } from './SelectorDias';
import { Letrero } from './Letrero';
import { ChipsHorario } from './ChipsHorario';
import { DetallePelicula, Poster } from './VistaCartelera';
import { DIAS, duracionTexto, etiquetaTipo, fechaDia, indiceHoy } from '../lib/dominio';
import type { Catalogo, Funcion, Pelicula } from '../lib/dominio';
import { hashPublico } from '../lib/ruta';

/*
 * Cartelera para el espectador: los mismos datos que la del administrador, sin nada interno del agente
 * (ni utilidad, ni espectadores esperados, ni ocupación, ni probabilidades, ni butacas).
 */

type Props = {
  catalogo: Catalogo; funciones: Funcion[]; dia: number; setDia: (dia: number) => void; ahora: Date;
  /** Película pedida por un enlace viejo `#/publico/pelicula/<id>`: se abre su modal una vez. */
  peliculaPedida: string | null; atenderPedida: () => void;
};

type Filtro = 'todos' | '2D' | '3D' | 'XD' | 'TP' | 'estrenos';
const FILTROS: [Filtro, string][] = [['todos', 'Todos'], ['2D', '2D'], ['3D', '3D'], ['XD', 'XD'], ['TP', 'Apta para todos (TP)'], ['estrenos', 'Estrenos']];

function pasaFiltro(p: Pelicula, filtro: Filtro) {
  if (filtro === 'todos') return true;
  if (filtro === 'TP') return p.clasificacion === 'TP';
  if (filtro === 'estrenos') return p.semana_cartelera === 1;
  return p.formato === filtro;
}

const porInicio = (a: Funcion, b: Funcion) => a.inicio - b.inicio;

/** Película del catálogo (trae el póster subido) o, si no está, la que viene dentro de la función. */
function usePeliculas(catalogo: Catalogo, funciones: Funcion[]) {
  return useMemo(() => {
    const porId = new Map(catalogo.map((p) => [p.id, p]));
    return (id: string) => porId.get(id) ?? funciones.find((f) => f.pelicula.id === id)?.pelicula;
  }, [catalogo, funciones]);
}

export function EncabezadoPublico({ ahora }: { ahora: Date }) {
  const hoy = ahora.toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
  return (
    <header className="encabezado-publico">
      <a className="marca" href={hashPublico(indiceHoy(ahora))} aria-label="ORDEN 66 · CINE, ir a la cartelera">
        <div className="marca-logo">66</div>
        <p className="marca-nombre">ORDEN 66 · CINE</p>
      </a>
      <p className="encabezado-publico-fecha"><CalendarDays size={15} /> Hoy, {hoy}</p>
    </header>
  );
}

function SinCartelera() {
  return (
    <div className="estado-vacio">
      <Film size={30} />
      <h3>La cartelera de esta semana estará disponible pronto</h3>
      <p>Estamos preparando las funciones. Vuelve en un rato para ver películas y horarios.</p>
    </div>
  );
}

export function CarteleraPublica({ catalogo, funciones, dia, setDia, ahora, peliculaPedida, atenderPedida }: Props) {
  const [filtro, setFiltro] = useState<Filtro>('todos');
  const [abierta, setAbierta] = useState<Pelicula | null>(null);
  const pelicula = usePeliculas(catalogo, funciones);
  const delDia = useMemo(() => funciones.filter((f) => f.dia === dia).sort(porInicio), [funciones, dia]);
  const peliculas = useMemo(
    () => [...new Set(delDia.map((f) => f.pelicula.id))].map(pelicula).filter((p): p is Pelicula => !!p && pasaFiltro(p, filtro)),
    [delDia, pelicula, filtro],
  );
  useEffect(() => {
    if (!peliculaPedida) return;
    const enCartelera = funciones.some((f) => f.pelicula.id === peliculaPedida);
    setAbierta((enCartelera && pelicula(peliculaPedida)) || null);
    atenderPedida();
  }, [peliculaPedida, funciones, pelicula, atenderPedida]);
  const fecha = fechaDia(ahora, dia).toLocaleDateString('es-BO', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

  if (!funciones.length) return <SinCartelera />;

  return (
    <>
      <Letrero presenta="ORDEN 66 · CINE" titulo="EN CARTELERA" fecha={fecha} />
      <SelectorDias dia={dia} setDia={setDia} ahora={ahora} />

      <div className="filtros-pildoras" role="group" aria-label="Filtrar películas">
        {FILTROS.map(([clave, etiqueta]) => (
          <button key={clave} className={filtro === clave ? 'activo' : ''} aria-pressed={filtro === clave} onClick={() => setFiltro(clave)}>{etiqueta}</button>
        ))}
      </div>

      {!delDia.length ? (
        <p className="aviso-vacio">No hay funciones el {DIAS[dia].toLowerCase()}. Elige otro día de la semana.</p>
      ) : !peliculas.length ? (
        <p className="aviso-vacio">Ninguna película del {DIAS[dia].toLowerCase()} coincide con este filtro.</p>
      ) : (
        <section className="grilla-peliculas">
          {peliculas.map((p) => (
            <MarcoLuces key={p.id} arriba={10} lado={5} className="marco-pelicula">
              <article className="pelicula">
                <Poster pelicula={p} />
                <div className="pelicula-cuerpo">
                  <p className="pelicula-meta">{etiquetaTipo(p.tipo)} · {duracionTexto(p.duracion)}</p>
                  <div className="chips"><ChipsHorario funciones={delDia.filter((f) => f.pelicula.id === p.id)} ahora={ahora} /></div>
                  <button className="btn-dorado ancho publico-ver" onClick={() => setAbierta(p)}>VER HORARIOS</button>
                </div>
              </article>
            </MarcoLuces>
          ))}
        </section>
      )}

      {abierta && <DetallePelicula publico pelicula={abierta} funciones={funciones.filter((f) => f.pelicula.id === abierta.id)} ahora={ahora} cerrar={() => setAbierta(null)} />}
    </>
  );
}
