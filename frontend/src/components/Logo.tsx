import { useMemo, type CSSProperties } from "react"
import { cn } from "@/lib/utils"

const N = 23 // grelha N×N de pixels
const C = (N - 1) / 2
const RINGS = [9.4, 7.0, 4.6] // anéis concêntricos do «G» (estratos)

type Px = { x: number; y: number; order: number; ring: number }

/** Pixels do «G»: três anéis abertos no canto superior direito, fechados por uma barra horizontal. */
function buildG(): Px[] {
  const out: Px[] = []
  for (let gy = 0; gy < N; gy++) {
    for (let gx = 0; gx < N; gx++) {
      const x = gx - C
      const y = C - gy // y para cima
      const r = Math.hypot(x, y)
      const ang = (Math.atan2(y, x) * 180) / Math.PI // 0° = direita, 90° = cima
      const ring = RINGS.findIndex((R) => Math.abs(r - R) < 0.55)
      const open = ang > 2 && ang < 52 // abertura do G
      const bar = Math.abs(y) < 0.5 && x >= 1.5 && x <= RINGS[0] + 0.5 // braço horizontal
      const hook = x > RINGS[0] - 0.6 && x < RINGS[0] + 0.6 && y < 0 && y > -2.5 // descida à direita
      if ((ring >= 0 && !open) || bar || hook) {
        // ordem de desenho: à volta do G, a partir da abertura
        const t = (((52 - ang) % 360) + 360) % 360
        out.push({ x: gx, y: gy, order: bar ? 360 + x : t, ring: ring < 0 ? 0 : ring })
      }
    }
  }
  return out
}

/** Marca em pixel art. `animated`: desenho pixel a pixel e cintilar contínuo. */
export function LogoMark({ className, animated = false }: { className?: string; animated?: boolean }) {
  const pixels = useMemo(buildG, [])
  const maxOrder = Math.max(...pixels.map((p) => p.order))
  return (
    <svg
      viewBox={`-2 -2 ${N + 4} ${N + 4}`}
      className={cn("size-10", className)}
      role="img"
      aria-label="GeoExplora IA"
      shapeRendering="crispEdges"
    >
      <rect x={-2} y={-2} width={N + 4} height={N + 4} rx={6} fill="currentColor" />
      {pixels.map((p, i) => (
        <rect
          key={i}
          x={p.x + 0.08}
          y={p.y + 0.08}
          width={0.84}
          height={0.84}
          fill="white"
          className={animated ? "gx-px gx-px-anim" : "gx-px"}
          style={
            {
              "--d": `${(p.order / maxOrder) * 1.4}s`,
              "--t": `${1.6 + ((i * 37) % 23) / 6}s`,
              opacity: animated ? undefined : 1 - p.ring * 0.12,
            } as CSSProperties
          }
        />
      ))}
    </svg>
  )
}

export function Logo({ className, light = false }: { className?: string; light?: boolean }) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <LogoMark className={light ? "text-white/20" : "text-primary"} />
      <div className="leading-tight">
        <div className={cn("text-[15px] font-bold tracking-tight", light ? "text-white" : "text-foreground")}>
          GeoExplora IA
        </div>
        <div className={cn("text-[11px] font-medium", light ? "text-white/70" : "text-muted-foreground")}>
          Minerais críticos · Angola
        </div>
      </div>
    </div>
  )
}
