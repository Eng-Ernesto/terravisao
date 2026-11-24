import type { LatLng } from "leaflet"
import { CheckCircle2, Eraser, FileUp, Loader2, MousePointer2, Pentagon, Square, TriangleAlert, WifiOff } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { GeoJSON, useMap } from "react-leaflet"
import { PanelSection, Segmented } from "@/components/LayerControls"
import { MapCanvas } from "@/components/MapCanvas"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { api, type Job } from "@/lib/api"
import { cn } from "@/lib/utils"
import { DrawTool, toPolygon, type DrawMode } from "./DrawTool"

const TARGETS = [
  { id: "ferro", label: "Ferro" },
  { id: "cobre", label: "Cobre" },
  { id: "ouro", label: "Ouro" },
  { id: "agua", label: "Água subterrânea" },
]
const PLACES: Record<string, [number, number, number]> = {
  Angola: [-12.3, 17.5, 6],
  Longonjo: [-12.92, 15.27, 12],
  Huambo: [-12.78, 15.74, 11],
  Lubango: [-14.92, 13.49, 11],
  Benguela: [-12.58, 13.41, 11],
  Luanda: [-8.84, 13.23, 10],
}

function FlyTo({ place }: { place: string }) {
  const map = useMap()
  useEffect(() => {
    const [lat, lon, z] = PLACES[place]
    map.flyTo([lat, lon], z, { duration: 0.8 })
  }, [map, place])
  return null
}

export function DrawPage({ onDone }: { onDone: (resultId: string) => void }) {
  const [mode, setMode] = useState<DrawMode>("none")
  const [vertices, setVertices] = useState<LatLng[]>([])
  const [shape, setShape] = useState<GeoJSON.Polygon | null>(null)
  const [check, setCheck] = useState<{ ok: boolean; area_km2?: number; error?: string } | null>(null)
  const [targets, setTargets] = useState<string[]>(TARGETS.map((t) => t.id))
  const [name, setName] = useState("Meu terreno")
  const [place, setPlace] = useState("Angola")
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [online, setOnline] = useState<boolean | null>(null)
  const [startedAt, setStartedAt] = useState<number | null>(null)
  const [, tick] = useState(0)
  const file = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.online().then((r) => setOnline(r.online)).catch(() => setOnline(false))
  }, [])

  useEffect(() => {
    if (!shape) return setCheck(null)
    api.tvValidate(shape).then(setCheck).catch((e: Error) => setCheck({ ok: false, error: e.message }))
  }, [shape])

  useEffect(() => {
    if (!job || job.status !== "running") return
    const t = setInterval(async () => {
      try {
        const j = await api.tvJob(job.id)
        setJob(j)
        tick((n) => n + 1)
        if (j.status === "done" && j.result_id) onDone(j.result_id)
        if (j.status === "error") setError(j.error ?? "A análise falhou.")
      } catch (e) {
        setError((e as Error).message)
        setJob(null)
      }
    }, 1200)
    return () => clearInterval(t)
  }, [job, onDone])

  const accept = (g: GeoJSON.Polygon) => {
    setShape(g)
    setMode("none")
    setError(null)
  }

  const loadGeojson = async (f: File) => {
    try {
      let gj = JSON.parse(await f.text())
      if (gj.type === "FeatureCollection") gj = gj.features[0]
      const g = gj.type === "Feature" ? gj.geometry : gj
      if (g?.type !== "Polygon") throw new Error("O ficheiro tem de ter um polígono.")
      accept(g)
    } catch (e) {
      setError(`Não consegui ler o GeoJSON: ${(e as Error).message}`)
    }
  }

  const analyse = async () => {
    if (!shape) return
    setError(null)
    try {
      setStartedAt(Date.now())
      setJob(await api.tvStartJob(shape, targets, name))
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const running = job?.status === "running"

  return (
    <div className="flex min-h-0 flex-1">
      <div className="relative min-w-0 flex-1">
        {/* Com internet (que a análise exige), um mapa base online dá contexto ao desenho. */}
        <MapCanvas online={online === true}>
          <FlyTo place={place} />
          <DrawTool mode={mode} vertices={vertices} setVertices={setVertices} onShape={accept} />
          {shape && (
            <GeoJSON
              key={JSON.stringify(shape)}
              data={shape}
              style={{ color: "#1A5BD7", weight: 2.5, fillColor: "#1A5BD7", fillOpacity: 0.12 }}
            />
          )}
        </MapCanvas>

        <div className="absolute top-4 left-1/2 z-[500] flex -translate-x-1/2 items-center gap-1 rounded-2xl border bg-card/95 p-1.5 shadow-lg">
          {(
            [
              ["none", MousePointer2, "Mover"],
              ["rect", Square, "Rectângulo"],
              ["poly", Pentagon, "Polígono"],
            ] as const
          ).map(([m, Icon, label]) => (
            <Button
              key={m}
              size="sm"
              variant={mode === m ? "default" : "ghost"}
              onClick={() => {
                setMode(m)
                setVertices([])
              }}
            >
              <Icon className="size-4" /> {label}
            </Button>
          ))}
          {mode === "poly" && vertices.length >= 3 && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => {
                accept(toPolygon(vertices))
                setVertices([])
              }}
            >
              <CheckCircle2 className="size-4" /> Concluir
            </Button>
          )}
          <span className="mx-1 h-6 w-px bg-border" />
          <Button size="sm" variant="ghost" onClick={() => file.current?.click()}>
            <FileUp className="size-4" /> GeoJSON
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={!shape && vertices.length === 0}
            onClick={() => {
              setShape(null)
              setVertices([])
            }}
          >
            <Eraser className="size-4" /> Limpar
          </Button>
          <input
            ref={file}
            type="file"
            accept=".geojson,.json"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) loadGeojson(f)
              e.target.value = ""
            }}
          />
        </div>
        {mode !== "none" && (
          <div className="pointer-events-none absolute bottom-5 left-1/2 z-[500] -translate-x-1/2 rounded-full bg-foreground/85 px-4 py-1.5 text-xs text-white">
            {mode === "rect" ? "Clique e arraste para desenhar o rectângulo" : "Clique para cada vértice; duplo clique ou «Concluir» para fechar"}
          </div>
        )}
      </div>

      <aside className="flex w-80 shrink-0 flex-col overflow-y-auto border-l bg-card">
        <PanelSection title="Ir para">
          <Segmented value={place} onChange={setPlace} options={Object.keys(PLACES).map((p) => ({ value: p, label: p }))} />
        </PanelSection>
        <PanelSection title="Terreno">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nome do terreno" />
          <div
            className={cn(
              "mt-3 flex items-start gap-2 rounded-xl px-3 py-2.5 text-sm",
              !check ? "bg-muted text-muted-foreground" : check.ok ? "bg-emerald-50 text-emerald-800" : "bg-orange-50 text-orange-800"
            )}
          >
            {!check ? (
              <>Desenhe o terreno no mapa ou carregue um GeoJSON.</>
            ) : check.ok ? (
              <>
                <CheckCircle2 className="mt-0.5 size-4 shrink-0" /> Terreno válido ·{" "}
                <span className="font-num">{check.area_km2?.toLocaleString("pt-PT")}</span> km²
              </>
            ) : (
              <>
                <TriangleAlert className="mt-0.5 size-4 shrink-0" /> {check.error}
              </>
            )}
          </div>
        </PanelSection>
        <PanelSection title="Alvos">
          <div className="grid gap-2.5">
            {TARGETS.map((t) => (
              <label key={t.id} className="flex items-center gap-2.5 text-sm">
                <Checkbox
                  checked={targets.includes(t.id)}
                  onCheckedChange={(c) =>
                    setTargets((cur) => (c ? [...cur, t.id] : cur.filter((x) => x !== t.id)))
                  }
                />
                {t.label}
              </label>
            ))}
          </div>
        </PanelSection>
        <div className="mt-auto border-t px-5 py-5">
          {online === false && (
            <div className="mb-3 flex gap-2 rounded-xl bg-amber-50 px-3 py-2.5 text-xs text-amber-900">
              <WifiOff className="mt-0.5 size-4 shrink-0" />
              Sem internet: a análise precisa de descarregar imagens de satélite. Os resultados já feitos continuam em
              «Resultados».
            </div>
          )}
          {running && job && (
            <div className="mb-3">
              <Progress value={Math.round(job.progress * 100)} />
              <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" /> {job.message}
              </div>
              {startedAt && Date.now() - startedAt > 180_000 && (
                <p className="mt-2 text-xs text-amber-700">
                  Está a demorar mais do que o normal (rede lenta). Pode continuar à espera ou ver os resultados já feitos.
                </p>
              )}
            </div>
          )}
          {error && <p className="mb-3 text-sm text-destructive">{error}</p>}
          <Button className="h-11 w-full rounded-xl" disabled={!check?.ok || targets.length === 0 || running} onClick={analyse}>
            {running ? "A analisar…" : "Analisar terreno"}
          </Button>
          <p className="mt-2 text-center text-xs text-muted-foreground">Demora cerca de 1 a 3 minutos.</p>
        </div>
      </aside>
    </div>
  )
}
