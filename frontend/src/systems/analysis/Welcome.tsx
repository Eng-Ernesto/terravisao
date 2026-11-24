import { motion } from "motion/react"
import { FileSpreadsheet, FlaskConical, Loader2, UploadCloud } from "lucide-react"
import { useRef, useState } from "react"
import { Badge } from "@/components/ui/badge"
import type { Dataset } from "@/lib/api"
import { cn } from "@/lib/utils"

const GRID_EXT = /\.(tif|tiff)$/i
const POINTS_EXT = /\.(csv|txt|geojson|json|zip)$/i

export function Welcome({
  datasets,
  busy,
  error,
  onDataset,
  onFiles,
}: {
  datasets: Dataset[]
  busy: string | null
  error: string | null
  onDataset: (id: string) => void
  onFiles: (points: File, grids: File[]) => void
}) {
  const input = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)

  const handle = (files: FileList | null) => {
    if (!files?.length) return
    const all = Array.from(files)
    const points = all.find((f) => POINTS_EXT.test(f.name))
    const grids = all.filter((f) => GRID_EXT.test(f.name))
    if (!points) {
      setLocalError("Falta o ficheiro de amostras (CSV, GeoJSON ou Shapefile em .zip). As grelhas GeoTIFF juntam-se a ele.")
      return
    }
    setLocalError(null)
    onFiles(points, grids)
  }

  const shownError = localError ?? error

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col justify-center px-6 py-10">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }} className="text-center">
        <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-secondary text-primary">
          <FlaskConical className="size-7" />
        </div>
        <h1 className="mt-5 text-3xl font-bold tracking-tight">Que dados quer analisar hoje?</h1>
        <p className="mx-auto mt-2 max-w-lg text-muted-foreground">
          Carregue as amostras do seu levantamento. A IA classifica as anomalias, delimita zonas de interesse e
          explica o resultado.
        </p>
      </motion.div>

      <motion.button
        type="button"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1 }}
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          handle(e.dataTransfer.files)
        }}
        disabled={!!busy}
        className={cn(
          "mt-8 flex flex-col items-center rounded-3xl border-2 border-dashed bg-card px-6 py-10 text-center transition outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
          drag ? "border-primary bg-secondary" : "border-input hover:border-primary/60 hover:bg-secondary/40"
        )}
      >
        {busy === "upload" ? (
          <Loader2 className="size-9 animate-spin text-primary" />
        ) : (
          <UploadCloud className="size-9 text-primary" />
        )}
        <div className="mt-3 font-semibold">{busy === "upload" ? "A analisar os seus dados…" : "Largue aqui os ficheiros ou clique para escolher"}</div>
        <div className="mt-1 text-sm text-muted-foreground">
          Amostras em CSV, GeoJSON ou Shapefile (.zip) · grelhas geofísicas em GeoTIFF (opcional)
        </div>
        <div className="mt-3 text-xs text-muted-foreground">
          Coordenadas X e Y em UTM 33S ou lon e lat · elementos como <span className="font-num">Ce_ppm, Nd_ppm, Cu_ppm</span>
        </div>
      </motion.button>
      <input
        ref={input}
        type="file"
        multiple
        accept=".csv,.txt,.geojson,.json,.zip,.tif,.tiff"
        className="hidden"
        onChange={(e) => {
          handle(e.target.files)
          e.target.value = ""
        }}
      />

      {shownError && (
        <div role="alert" className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          {shownError}
        </div>
      )}

      <div className="mt-8">
        <div className="mb-3 text-xs font-semibold tracking-wider text-muted-foreground uppercase">Ou experimente um exemplo</div>
        <div className="grid gap-3 sm:grid-cols-2">
          {datasets.map((d, i) => (
            <motion.button
              key={d.id}
              type="button"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 + i * 0.08 }}
              disabled={!!busy}
              onClick={() => onDataset(d.id)}
              className="group flex items-start gap-3 rounded-2xl border bg-card p-4 text-left transition hover:border-primary/50 hover:shadow-[0_12px_30px_-18px_rgba(26,91,215,0.5)] disabled:opacity-60"
            >
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-primary">
                {busy === d.id ? <Loader2 className="size-5 animate-spin" /> : <FileSpreadsheet className="size-5" />}
              </div>
              <div className="min-w-0">
                <div className="font-semibold">{d.title.replace(" (fictícios)", "").replace(" (fictício)", "")}</div>
                <div className="mt-1 line-clamp-2 text-xs text-muted-foreground">{d.note}</div>
                <div className="mt-2 flex gap-1.5">
                  {d.fictitious && <Badge variant="secondary">Fictício</Badge>}
                  {d.grids.length > 0 && <Badge variant="outline">+ grelha magnética</Badge>}
                </div>
              </div>
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  )
}
