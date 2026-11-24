import { cn } from "@/lib/utils"

/** Marca: estratos geológicos estilizados num quadrado arredondado. */
export function LogoMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={cn("size-10", className)} aria-hidden="true">
      <rect width="40" height="40" rx="11" fill="currentColor" />
      <path d="M7 26c4-6 8-9 13-9s9 3 13 9" fill="none" stroke="white" strokeWidth="2.6" strokeLinecap="round" />
      <path d="M7 31c4-3 8-4.5 13-4.5S29 28 33 31" fill="none" stroke="white" strokeOpacity=".7" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="26" cy="13" r="3" fill="white" />
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
