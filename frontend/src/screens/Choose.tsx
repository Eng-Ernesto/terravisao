import { motion } from "motion/react"
import { ArrowRight, MessagesSquare, Satellite } from "lucide-react"
import type { Screen } from "@/App"
import { Logo } from "@/components/Logo"
import { Button } from "@/components/ui/button"

const SYSTEMS = [
  {
    id: "analysis" as const,
    icon: MessagesSquare,
    tag: "Principal",
    title: "Análise de mapa",
    text: "Carregue as suas amostras e grelhas geofísicas. A IA classifica anomalias, delimita zonas e explica o resultado numa conversa.",
    cta: "Analisar dados",
  },
  {
    id: "terra" as const,
    icon: Satellite,
    tag: "Satélite",
    title: "TerraVisão",
    text: "Desenhe um terreno no mapa. A plataforma usa imagens de satélite e relevo públicos para uma triagem rápida.",
    cta: "Abrir TerraVisão",
  },
]

export function Choose({ onPick }: { onPick: (s: Screen) => void }) {
  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="flex items-center justify-between px-8 py-6">
        <Logo />
        <Button variant="ghost" size="sm" onClick={() => onPick("splash")} className="text-muted-foreground">
          Ver apresentação
        </Button>
      </header>
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col justify-center px-6 pb-16">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <h1 className="text-3xl font-bold tracking-tight">O que quer fazer hoje?</h1>
          <p className="mt-2 text-muted-foreground">Escolha um dos dois sistemas. Pode trocar a qualquer momento pelo menu.</p>
        </motion.div>
        <div className="mt-8 grid gap-6 md:grid-cols-2">
          {SYSTEMS.map((s, i) => (
            <motion.button
              key={s.id}
              type="button"
              onClick={() => onPick(s.id)}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.12 }}
              whileHover={{ y: -4 }}
              className="group relative flex flex-col overflow-hidden rounded-3xl border bg-card p-7 text-left shadow-[0_12px_40px_-20px_rgba(15,27,45,0.35)] outline-none transition-shadow hover:shadow-[0_24px_50px_-22px_rgba(26,91,215,0.45)] focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <div className={i === 0 ? "absolute inset-x-0 top-0 h-1.5 bg-primary" : "absolute inset-x-0 top-0 h-1.5 bg-[#5B8DEF]"} />
              <div className="flex items-center justify-between">
                <div className="flex size-12 items-center justify-center rounded-2xl bg-secondary text-primary">
                  <s.icon className="size-6" />
                </div>
                <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">{s.tag}</span>
              </div>
              <h2 className="mt-6 text-2xl font-semibold tracking-tight">{s.title}</h2>
              <p className="mt-2 flex-1 text-[15px] leading-relaxed text-muted-foreground">{s.text}</p>
              <span className="mt-7 inline-flex items-center gap-2 font-semibold text-primary">
                {s.cta} <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
              </span>
            </motion.button>
          ))}
        </div>
      </main>
    </div>
  )
}
