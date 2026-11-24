import type { LucideIcon } from "lucide-react"
import { Home, Repeat } from "lucide-react"
import type { ReactNode } from "react"
import { LogoMark } from "@/components/Logo"
import { cn } from "@/lib/utils"

export type MenuItem = { id: string; label: string; icon: LucideIcon; disabled?: boolean; hint?: string }

type Props = {
  system: string
  subtitle: string
  primary?: { label: string; icon: LucideIcon; onClick: () => void }
  menu: MenuItem[]
  active: string
  onSelect: (id: string) => void
  switchLabel: string
  onSwitch: () => void
  onHome: () => void
  children: ReactNode
}

/** Estrutura de um sistema: menu lateral azul (referência Drive) e painel claro arredondado. */
export function Shell({ system, subtitle, primary, menu, active, onSelect, switchLabel, onSwitch, onHome, children }: Props) {
  return (
    <div className="flex h-svh bg-sidebar text-sidebar-foreground">
      <aside className="flex w-64 shrink-0 flex-col px-4 py-6">
        <div className="flex items-center gap-2.5 px-2">
          <LogoMark className="size-9 text-white/15" />
          <div className="leading-tight">
            <div className="text-[15px] font-bold tracking-tight">{system}</div>
            <div className="text-[11px] text-white/70">{subtitle}</div>
          </div>
        </div>

        {primary && (
          <button
            type="button"
            onClick={primary.onClick}
            className="mt-7 flex h-11 items-center justify-center gap-2 rounded-full bg-white px-4 text-sm font-semibold text-primary shadow-[0_8px_20px_-8px_rgba(0,0,0,0.35)] transition hover:bg-white/90 focus-visible:ring-3 focus-visible:ring-white/50 focus-visible:outline-none"
          >
            <primary.icon className="size-4" /> {primary.label}
          </button>
        )}

        <nav className="mt-7 flex flex-col gap-1" aria-label="Menu">
          {menu.map((m) => (
            <button
              key={m.id}
              type="button"
              disabled={m.disabled}
              title={m.hint}
              onClick={() => onSelect(m.id)}
              aria-current={active === m.id ? "page" : undefined}
              className={cn(
                "flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium text-white/80 transition hover:bg-sidebar-accent hover:text-white focus-visible:ring-2 focus-visible:ring-white/60 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent",
                active === m.id && "bg-white text-primary hover:bg-white hover:text-primary"
              )}
            >
              <m.icon className="size-[18px]" /> {m.label}
            </button>
          ))}
        </nav>

        <div className="mt-auto flex flex-col gap-1 border-t border-sidebar-border pt-4">
          <button
            type="button"
            onClick={onSwitch}
            className="flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium text-white/80 transition hover:bg-sidebar-accent hover:text-white"
          >
            <Repeat className="size-[18px]" /> {switchLabel}
          </button>
          <button
            type="button"
            onClick={onHome}
            className="flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium text-white/80 transition hover:bg-sidebar-accent hover:text-white"
          >
            <Home className="size-[18px]" /> Início
          </button>
          <p className="px-3 pt-3 text-[11px] leading-snug text-white/60">
            Ferramenta de apoio. Indica onde confirmar no campo; não confirma mineralização.
          </p>
        </div>
      </aside>

      <main className="my-3 mr-3 flex min-w-0 flex-1 flex-col overflow-hidden rounded-[28px] bg-background text-foreground">
        {children}
      </main>
    </div>
  )
}

export function PageHeader({ title, description, actions }: { title: string; description?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 border-b bg-card/60 px-8 py-5">
      <div className="min-w-0">
        <h1 className="truncate text-2xl font-bold tracking-tight">{title}</h1>
        {description && <div className="mt-1 text-sm text-muted-foreground">{description}</div>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
