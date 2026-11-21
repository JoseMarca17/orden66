import type { CSSProperties, ReactNode } from 'react';

type Props = { arriba: number; lado: number; children: ReactNode; className?: string; borde?: number };

const PASO = 0.16; // s entre bombillas; 5 pasos = 0.8 s = un ciclo de `chase` (2 encendidas, 3 apagadas)

/**
 * Marco rojo vino con bombillas que recorren el perímetro (arriba → derecha → abajo → izquierda).
 * Total de bombillas = 2·arriba + 2·lado; conviene que sea múltiplo de 5 para que el patrón cierre.
 */
export function MarcoLuces({ arriba, lado, children, className = '', borde = 28 }: Props) {
  const m = borde / 2; // centro del grosor del marco
  const largo = (t: number) => `calc(${m}px + (100% - ${borde}px) * ${t})`;
  const tramo = (n: number, k: number) => (n <= 1 ? 0.5 : k / (n - 1));
  const posiciones: { left: string; top: string }[] = [];
  for (let k = 0; k < arriba; k++) posiciones.push({ left: largo(tramo(arriba, k)), top: `${m}px` });
  for (let j = 0; j < lado; j++) posiciones.push({ left: `calc(100% - ${m}px)`, top: largo((j + 1) / (lado + 1)) });
  for (let k = 0; k < arriba; k++) posiciones.push({ left: largo(1 - tramo(arriba, k)), top: `calc(100% - ${m}px)` });
  for (let j = 0; j < lado; j++) posiciones.push({ left: `${m}px`, top: largo(1 - (j + 1) / (lado + 1)) });
  const total = posiciones.length;

  return (
    <div className={`marco-luces ${className}`} style={{ '--marco': `${borde}px` } as CSSProperties}>
      {posiciones.map((p, k) => (
        <span key={k} aria-hidden className={`bulb${k % 2 === 0 ? ' alterna' : ''}`} style={{ ...p, animationDelay: `-${((total - k) * PASO).toFixed(2)}s` }} />
      ))}
      <div className="marco-contenido">{children}</div>
    </div>
  );
}
