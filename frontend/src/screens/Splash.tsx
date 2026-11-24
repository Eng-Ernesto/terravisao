import { motion } from "motion/react"
import { ArrowRight, FileChartColumn, FolderUp, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { LogoMark } from "@/components/Logo"

const PILLARS = [
  { icon: FolderUp, title: "Os seus dados", text: "Amostras, mapas e grelhas geofísicas exportados do QGIS." },
  { icon: Sparkles, title: "Análise explicável", text: "Anomalias, zonas de interesse e relação com a geofísica, com IA." },
  { icon: FileChartColumn, title: "Relatório técnico", text: "Mapas, métodos e limitações prontos a partilhar." },
]

const fade = (delay: number) => ({
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] as const },
})

export function Splash({ onStart }: { onStart: () => void }) {
  return (
    <div className="relative flex min-h-svh flex-col overflow-hidden bg-[radial-gradient(1200px_600px_at_15%_-10%,#DCE8FF_0%,transparent_60%),radial-gradient(900px_500px_at_110%_110%,#E4EEFF_0%,transparent_55%)] bg-background">
      <div className="pointer-events-none absolute -top-40 -right-40 size-[520px] rounded-full bg-primary/10 blur-3xl" />
      <header className="relative z-10 flex items-center justify-end px-8 pt-6">
        <Button variant="ghost" size="sm" onClick={onStart} className="text-muted-foreground">
          Saltar
        </Button>
      </header>

      <main className="relative z-10 mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center px-6 text-center">
        <motion.div {...fade(0.1)}>
          <LogoMark animated className="size-20 text-primary drop-shadow-[0_10px_25px_rgba(26,91,215,0.35)]" />
        </motion.div>
        <motion.h1 {...fade(0.45)} className="mt-6 text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
          GeoExplora <span className="text-primary">IA</span>
        </motion.h1>
        <motion.p {...fade(1.0)} className="mt-4 max-w-xl text-lg text-muted-foreground">
          Interprete dados de exploração de minerais críticos em minutos, para a transição energética de Angola.
        </motion.p>

        <div className="mt-12 grid w-full gap-4 sm:grid-cols-3">
          {PILLARS.map((p, i) => (
            <motion.div
              key={p.title}
              {...fade(1.6 + i * 0.35)}
              className="rounded-2xl border border-white/70 bg-white/70 p-5 text-left shadow-[0_10px_30px_-12px_rgba(15,27,45,0.18)] backdrop-blur"
            >
              <div className="flex size-9 items-center justify-center rounded-xl bg-secondary text-primary">
                <p.icon className="size-5" />
              </div>
              <div className="mt-3 font-semibold">{p.title}</div>
              <div className="mt-1 text-sm text-muted-foreground">{p.text}</div>
            </motion.div>
          ))}
        </div>

        <motion.div {...fade(2.9)} className="mt-12">
          <Button size="lg" onClick={onStart} className="h-12 rounded-full px-8 text-base shadow-[0_12px_30px_-10px_rgba(26,91,215,0.6)]">
            Iniciar <ArrowRight className="size-5" />
          </Button>
        </motion.div>
      </main>

      <motion.footer {...fade(3.2)} className="relative z-10 pb-6 text-center text-xs text-muted-foreground">
        3.ª Semana Académica de Geociências · Do petróleo aos minerais críticos
      </motion.footer>
    </div>
  )
}
