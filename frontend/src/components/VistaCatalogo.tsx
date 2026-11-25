import { useState } from 'react';
import type { FormEvent } from 'react';
import { Film, Plus, Search, Upload, X } from 'lucide-react';
import { Poster } from './VistaCartelera';
import { duracionTexto, etiquetaTipo } from '../lib/dominio';
import type { Catalogo } from '../lib/dominio';

type Props = { catalogo: Catalogo; guardarPelicula: (event: FormEvent<HTMLFormElement>) => Promise<boolean>; guardando: boolean };

export function VistaCatalogo({ catalogo, guardarPelicula, guardando }: Props) {
  const [busqueda, setBusqueda] = useState('');
  const [modal, setModal] = useState(false);
  const filtradas = catalogo.filter((p) => p.titulo.toLowerCase().includes(busqueda.toLowerCase()));

  return (
    <>
      <header className="encabezado-vista">
        <div><p className="antetitulo">ORDEN 66 / CATÁLOGO</p><h1>CATÁLOGO DE PELÍCULAS</h1></div>
      </header>
      <div className="barra-catalogo">
        <label className="buscador"><Search size={17} /><input placeholder="Buscar película…" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} /></label>
        <button className="btn-dorado" onClick={() => setModal(true)}><Plus size={17} /> Dar de alta película</button>
      </div>
      <section className="grilla-catalogo">
        {filtradas.map((p) => (
          <article className="tarjeta-catalogo" key={p.id}>
            <Poster pelicula={p} />
            <div className="catalogo-info">
              <p className="pelicula-meta">{p.id} · {etiquetaTipo(p.tipo)} · {duracionTexto(p.duracion)}</p>
            </div>
          </article>
        ))}
        {!filtradas.length && <div className="estado-vacio"><Film size={30} /><p>No hay películas que coincidan.</p></div>}
      </section>

      {modal && (
        <div className="modal-fondo" onClick={() => setModal(false)}>
          <form className="modal formulario" onClick={(e) => e.stopPropagation()} onSubmit={async (e) => { if (await guardarPelicula(e)) setModal(false); }}>
            <div className="modal-cabecera">
              <div><p className="antetitulo">NUEVO REGISTRO</p><h2>DAR DE ALTA PELÍCULA</h2></div>
              <button type="button" className="btn-icono" onClick={() => setModal(false)} aria-label="Cerrar"><X size={18} /></button>
            </div>
            <div className="formulario-grilla">
              <label>ID<input name="id" required placeholder="P13" /></label>
              <label>Título<input name="titulo" required placeholder="Nombre de la película" /></label>
              <label>Duración (min)<input name="duracion" required type="number" min="60" max="240" placeholder="110" /></label>
              <label>Clasificación<select name="clasificacion" defaultValue="TP"><option>TP</option><option>+13</option><option>+18</option></select></label>
              <label>Formato<select name="formato" defaultValue="2D"><option>2D</option><option>3D</option><option>XD</option></select></label>
              <label>Tipo<select name="tipo" defaultValue="otra_extranjera"><option>familiar_animada</option><option>superheroes_accion</option><option>otra_extranjera</option><option>nacional</option></select></label>
            </div>
            <label className="subir"><Upload size={18} /> Póster (opcional)<input name="poster" type="file" accept="image/*" /></label>
            <button className="btn-dorado ancho" disabled={guardando}>{guardando ? 'Guardando…' : 'Guardar película'}</button>
          </form>
        </div>
      )}
    </>
  );
}
