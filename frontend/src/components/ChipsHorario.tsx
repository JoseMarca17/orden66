import { haPasado, hora } from '../lib/dominio';
import type { Funcion } from '../lib/dominio';

/** Chips dorados de horario (hora + sala); las funciones ya iniciadas se muestran apagadas. */
export function ChipsHorario({ funciones, ahora }: { funciones: Funcion[]; ahora: Date }) {
  return (
    <>
      {funciones.map((f) => {
        const pasada = haPasado(f, ahora);
        return (
          <span key={`${f.sala}-${f.dia}-${f.inicio}`} className={`chip${pasada ? ' pasada' : ''}`} title={pasada ? 'Función ya iniciada' : undefined}>
            <b>{hora(f.inicio)}</b><small>{f.sala}</small>
          </span>
        );
      })}
    </>
  );
}
