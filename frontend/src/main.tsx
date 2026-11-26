import React, { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { Armchair, BarChart3, CalendarDays, Film } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import './style.css';
import { VistaCartelera } from './components/VistaCartelera';
import { PaginaSala, VistaSalas } from './components/VistaSalas';
import { VistaCatalogo } from './components/VistaCatalogo';
import { VistaEvaluacion } from './components/VistaEvaluacion';
import { CarteleraPublica, EncabezadoPublico } from './components/VistaPublica';
import { CLAVE_CARTELERA, guardarCartelera, leerCartelera } from './lib/almacen';
import { API, catalogoInicial, indiceHoy, useAhora } from './lib/dominio';
import type { Catalogo, Funcion, Pelicula, Vista } from './lib/dominio';
import { hashPublico, hashSalas, leerRuta } from './lib/ruta';

const MENU: [Vista, LucideIcon, string][] = [['cartelera', CalendarDays, 'Cartelera'], ['salas', Armchair, 'Salas'], ['catalogo', Film, 'Catálogo'], ['evaluacion', BarChart3, 'Evaluación']];

function App() {
  const ahora = useAhora();
  const [ruta, setRuta] = useState(leerRuta);
  const vista = ruta.vista;
  const [dia, setDia] = useState(() => ruta.dia ?? indiceHoy(new Date()));
  const [guardada] = useState(leerCartelera);
  const [estado, setEstado] = useState(() => guardada ? `${guardada.funciones.length} funciones · guardada el ${new Date(guardada.generada).toLocaleString('es-BO', { dateStyle: 'short', timeStyle: 'short' })}` : 'Lista para generar');
  const [generando, setGenerando] = useState(false);
  const [funciones, setFunciones] = useState<Funcion[]>(() => guardada?.funciones ?? []);
  const [convergencia, setConvergencia] = useState<number[]>(() => guardada?.convergencia ?? []);
  const [catalogo, setCatalogo] = useState<Catalogo>(catalogoInicial);
  const [guardando, setGuardando] = useState(false);

  // Navegación por hash: el botón "atrás" y la recarga funcionan sin router.
  useEffect(() => {
    const alCambiar = () => setRuta(leerRuta());
    window.addEventListener('hashchange', alCambiar);
    return () => window.removeEventListener('hashchange', alCambiar);
  }, []);
  useEffect(() => { if (ruta.dia !== null) setDia(ruta.dia); }, [ruta.dia]);
  useEffect(() => { window.scrollTo(0, 0); }, [ruta.vista, ruta.salaId]);
  // La página `#/publico/pelicula/<id>` ya no existe: se redirige a `#/publico` con el modal de esa película abierto.
  const [peliculaPedida, setPeliculaPedida] = useState<string | null>(null);
  const atenderPedida = useCallback(() => setPeliculaPedida(null), []);
  useEffect(() => {
    if (ruta.vista !== 'publico' || !ruta.peliculaId) return;
    setPeliculaPedida(ruta.peliculaId);
    window.history.replaceState(null, '', hashPublico(ruta.dia ?? dia));
    setRuta(leerRuta());
  }, [ruta, dia]);
  // Si otra pestaña (el admin) genera una cartelera nueva, esta pestaña la toma sin recargar.
  useEffect(() => {
    const alGuardar = (e: StorageEvent) => {
      if (e.key !== CLAVE_CARTELERA) return;
      const nueva = leerCartelera();
      setFunciones(nueva?.funciones ?? []);
      setConvergencia(nueva?.convergencia ?? []);
    };
    window.addEventListener('storage', alGuardar);
    return () => window.removeEventListener('storage', alGuardar);
  }, []);

  const navegar = (hash: string, reemplazar = false) => {
    if (reemplazar) { window.history.replaceState(null, '', hash); setRuta(leerRuta(hash)); }
    else window.location.hash = hash;
  };
  /** En Salas el día vive en la URL; se reemplaza la entrada para no llenar el historial. */
  const cambiarDia = (nuevo: number) => {
    setDia(nuevo);
    if (vista === 'salas') navegar(hashSalas(nuevo, ruta.salaId), true);
    if (vista === 'publico') navegar(hashPublico(nuevo), true);
  };

  // Si este navegador no tiene cartelera guardada, trae la última que generó la API.
  useEffect(() => {
    if (guardada) return;
    fetch(`${API}/api/cartelera/ultima`)
      .then((r) => (r.ok ? r.json() : null))
      .then((ultima: { fecha: string; funciones: Funcion[]; convergencia: number[] } | null) => {
        if (!ultima?.funciones?.length || leerCartelera()) return;
        setFunciones(ultima.funciones); setConvergencia(ultima.convergencia ?? []);
        guardarCartelera(ultima.funciones, ultima.convergencia ?? [], ultima.fecha);
        setEstado(`${ultima.funciones.length} funciones · última generada en la API`);
      })
      .catch(() => undefined);
  }, [guardada]);
  useEffect(() => { fetch(`${API}/api/peliculas`).then((r) => r.ok ? r.json() : []).then((peliculas: Catalogo) => { if (peliculas.length) setCatalogo(peliculas); }).catch(() => undefined); }, []);

  async function generar() {
    setEstado('Generando cartelera…'); setGenerando(true);
    try {
      const respuesta = await fetch(`${API}/api/generar-cartelera?semilla=${Date.now() % 100000}&generaciones=5`, { method: 'POST' }); if (!respuesta.ok) throw new Error(`HTTP ${respuesta.status}`);
      const { job_id } = await respuesta.json(); let terminado = false;
      while (!terminado) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        const trabajo = await (await fetch(`${API}/api/jobs/${job_id}`)).json(); setEstado(`${trabajo.estado} · ${trabajo.progreso ?? 0}%`);
        if (trabajo.estado === 'completado') { setFunciones(trabajo.resultado.funciones); setConvergencia(trabajo.resultado.convergencia); guardarCartelera(trabajo.resultado.funciones, trabajo.resultado.convergencia); setEstado(`${trabajo.resultado.funciones.length} funciones generadas`); terminado = true; }
        if (trabajo.estado === 'error') throw new Error(trabajo.error);
      }
    } catch (error) { setEstado(`Error: ${error instanceof Error ? error.message : 'API no disponible'}`); }
    finally { setGenerando(false); }
  }

  async function guardarPelicula(event: FormEvent<HTMLFormElement>): Promise<boolean> {
    event.preventDefault(); setGuardando(true); const datos = new FormData(event.currentTarget);
    try {
      const respuesta = await fetch(`${API}/api/peliculas`, { method: 'POST', body: datos }); if (!respuesta.ok) throw new Error('No se pudo guardar');
      const pelicula = await respuesta.json();
      setCatalogo((actual) => [...actual, { ...Object.fromEntries(datos.entries()), ...pelicula, duracion: Number(datos.get('duracion')), semana_cartelera: Number(datos.get('semana_cartelera') ?? pelicula.semana_cartelera) } as Pelicula]);
      return true;
    } catch (error) { alert(error instanceof Error ? error.message : 'Error al guardar'); return false; }
    finally { setGuardando(false); }
  }

  if (vista === 'publico') {
    return (
      <div className="app-publica">
        <EncabezadoPublico ahora={ahora} />
        <main className="contenido">
          <CarteleraPublica catalogo={catalogo} funciones={funciones} dia={dia} setDia={cambiarDia} ahora={ahora} peliculaPedida={peliculaPedida} atenderPedida={atenderPedida} />
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca">
          <div className="marca-logo">66</div>
          <div><p className="marca-nombre">ORDEN 66</p><p className="marca-sub">CINE INTELIGENTE</p></div>
        </div>
        <nav className="menu">
          {MENU.map(([clave, Icono, etiqueta]) => (
            <a key={clave} href={clave === 'salas' ? hashSalas(dia) : `#/${clave}`} className={vista === clave ? 'activo' : ''} aria-current={vista === clave ? 'page' : undefined}><Icono size={18} />{etiqueta}</a>
          ))}
        </nav>
        <a className="enlace-publico" href="#/publico" target="_blank" rel="noopener">Ver cartelera pública ↗</a>
        <div className="nota-motor"><span className="punto-dorado" /> Motor operativo<br /><small>PSR · RB · AG</small></div>
      </aside>
      <main className="contenido">
        {vista === 'cartelera' && <VistaCartelera catalogo={catalogo} funciones={funciones} convergencia={convergencia} dia={dia} setDia={setDia} estado={estado} generando={generando} generar={generar} ahora={ahora} />}
        {vista === 'salas' && !ruta.salaId && <VistaSalas funciones={funciones} dia={dia} setDia={cambiarDia} ahora={ahora} generar={generar} generando={generando} />}
        {vista === 'salas' && ruta.salaId && <PaginaSala salaId={ruta.salaId} funciones={funciones} dia={dia} setDia={cambiarDia} ahora={ahora} generar={generar} generando={generando} />}
        {vista === 'catalogo' && <VistaCatalogo catalogo={catalogo} guardarPelicula={guardarPelicula} guardando={guardando} />}
        {vista === 'evaluacion' && <VistaEvaluacion convergencia={convergencia} irACartelera={() => navegar('#/cartelera')} />}
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>);
