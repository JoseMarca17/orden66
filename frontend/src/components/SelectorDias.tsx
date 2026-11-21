import { DIAS, DIAS_CORTOS, fechaDia, indiceHoy } from '../lib/dominio';

type Props = { dia: number; setDia: (dia: number) => void; ahora: Date; sobrio?: boolean };

export function SelectorDias({ dia, setDia, ahora, sobrio = false }: Props) {
  const hoy = indiceHoy(ahora);
  return (
    <div className={`selector-dias${sobrio ? ' sobrio' : ''}`} role="tablist" aria-label="Día de la semana">
      {DIAS_CORTOS.map((corto, i) => (
        <button key={corto} role="tab" aria-selected={dia === i} aria-label={DIAS[i]} className={dia === i ? 'activo' : ''} onClick={() => setDia(i)}>
          <span>{corto}</span>
          <b>{String(fechaDia(ahora, i).getDate()).padStart(2, '0')}</b>
          {i === hoy && <small>HOY</small>}
        </button>
      ))}
    </div>
  );
}
