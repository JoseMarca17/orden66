import { BarChart3, RefreshCw } from 'lucide-react';

const DEMO = [6120, 6940, 7480, 7810, 8090, 8350, 8520, 8670, 8790, 8910, 8990, 9060];

function GraficoLinea({ valores }: { valores: number[] }) {
  const datos = valores.length ? valores : DEMO;
  const max = Math.max(...datos); const min = Math.min(...datos); const rango = max - min || 1;
  const x = (i: number) => (i / Math.max(datos.length - 1, 1)) * 100;
  const y = (v: number) => 88 - ((v - min) / rango) * 72;
  const puntos = datos.map((v, i) => `${x(i)},${y(v)}`).join(' ');
  return (
    <div className="grafico">
      <div className="grafico-guias"><span>máximo</span><span>promedio</span><span>mínimo</span></div>
      <svg className="grafico-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs><linearGradient id="relleno-dorado" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#f5c542" stopOpacity=".35" /><stop offset="1" stopColor="#f5c542" stopOpacity="0" /></linearGradient></defs>
        <polygon points={`0,100 ${puntos} 100,100`} fill="url(#relleno-dorado)" />
        <polyline points={puntos} fill="none" stroke="#f5c542" strokeWidth="2" vectorEffect="non-scaling-stroke" />
        {datos.map((v, i) => <circle key={i} cx={x(i)} cy={y(v)} r="1.6" fill="#ffe08a" stroke="#26040f" strokeWidth=".8" />)}
      </svg>
      <div className="grafico-x"><span>Generación 1</span><span>Generación {datos.length}</span></div>
      {!valores.length && <span className="etiqueta-demo">Vista demostrativa · genera una cartelera para actualizar</span>}
    </div>
  );
}

export function VistaEvaluacion({ convergencia, irACartelera }: { convergencia: number[]; irACartelera: () => void }) {
  const datos = convergencia.length ? convergencia : DEMO;
  const maxU = Math.max(...datos, 1); const minU = Math.min(...datos, 0);
  const metricas = [Math.max(28, (minU / maxU) * 100), Math.max(44, (minU / maxU) * 100 + 12), Math.min(98, (maxU / maxU) * 100)];
  const hay = convergencia.length > 0;
  return (
    <>
      <header className="encabezado-vista">
        <div><p className="antetitulo">RESULTADOS DEL AGENTE</p><h1>RENDIMIENTO Y CONVERGENCIA</h1></div>
        <button className="btn-contorno" onClick={irACartelera}><RefreshCw size={16} /> Usar última ejecución</button>
      </header>
      <div className="grilla-evaluacion">
        <section className="panel">
          <div className="panel-cabecera">
            <div><span className="antetitulo">ALGORITMO GENÉTICO</span><h3>UTILIDAD POR GENERACIÓN</h3></div>
            <span className="cifra-chip">{hay ? convergencia[convergencia.length - 1].toFixed(0) : '—'} <small>U(C)</small></span>
          </div>
          <GraficoLinea valores={convergencia} />
          <div className="panel-pie"><span>Inicio</span><span>{hay ? `${convergencia.length} generaciones evaluadas` : 'Sin datos todavía'}</span></div>
        </section>
        <section className="panel">
          <div className="panel-cabecera">
            <div><span className="antetitulo">COMPARATIVA</span><h3>MÉTODOS</h3></div>
            <BarChart3 size={20} className="icono-tenue" />
          </div>
          <div className="metodos">
            {['M1 · Manual', 'M2 · Aleatoria', 'M3 · Agente'].map((nombre, i) => (
              <div className="metodo" key={nombre}>
                <div><span>{nombre}</span><b>{hay ? `${metricas[i].toFixed(0)}%` : '—'}</b></div>
                <div className="uso-barra"><i style={{ width: `${hay ? metricas[i] : 0}%` }} /></div>
              </div>
            ))}
          </div>
          <p className="panel-nota"><span className="punto-dorado" /> M3 combina PSR + red bayesiana + AG</p>
        </section>
      </div>
    </>
  );
}
