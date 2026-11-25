import { MarcoLuces } from './MarcoLuces';

/** Letrero de marquesina con luces y el cartel vertical "CINE". Lo usan la cartelera del admin y la pública. */
export function Letrero({ presenta, titulo, fecha }: { presenta: string; titulo: string; fecha: string }) {
  return (
    <div className="letrero-fila">
      <MarcoLuces arriba={20} lado={5} className="marco-letrero">
        <div className="letrero">
          <p className="letrero-presenta">{presenta}</p>
          <h1 className="letrero-titulo">{titulo}</h1>
          <div className="letrero-linea" />
          <p className="letrero-fecha">{fecha}</p>
        </div>
      </MarcoLuces>
      <MarcoLuces arriba={3} lado={12} className="marco-cine">
        <div className="letrero-cine" aria-label="Cine">{['C', 'I', 'N', 'E'].map((l) => <span key={l}>{l}</span>)}</div>
      </MarcoLuces>
    </div>
  );
}
