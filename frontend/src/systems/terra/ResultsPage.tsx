import { Archive, FileDown, Loader2, MapPinned } from "lucide-react"
import { useEffect, useState } from "react"
import { GeoJSON, Tooltip } from "react-leaflet"
import { PanelSection, Range, Segmented, ToggleRow } from "@/components/LayerControls"
import { MapCanvas, OverlayLayer } from "@/components/MapCanvas"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api, type LatLngBounds, type Overlay, type TvResult, type TvResultItem } from "@/lib/api"
import { cn } from "@/lib/utils"

const TARGET_LABEL: Record<string, string> = { terras_raras: "Terras raras", cobre: "Cobre", litio: "Lítio", manganes: "Manganês" }
const LAYER_LABEL: Record<string, string> = {
  classe: "Classe",
  pontuacao: "Pontuação",
  oxido: "Óxido de ferro",
  argila: "Argila",
  relevo: "Relevo",
  satelite: "Satélite",
}
const LEVEL = {
  baixa: { label: "Baixa", color: "#5E7A63" },
  media: { label: "Média", color: "#C9A227" },
  alta: { label: "Alta", color: "#B4532A" },
} as const

function boundsOf(g: GeoJSON.Polygon | GeoJSON.MultiPolygon): LatLngBounds {
  const rings = g.type === "Polygon" ? g.coordinates : g.coordinates.flat()
  const pts = rings.flat()
  const lons = pts.map((p) => p[0])
  const lats = pts.map((p) => p[1])
  return [
    [Math.min(...lats), Math.min(...lons)],
    [Math.max(...lats), Math.max(...lons)],
  ]
}

export function ResultsPage({ initialId }: { initialId?: string }) {
  const [items, setItems] = useState<TvResultItem[]>([])
  const [selected, setSelected] = useState<string | undefined>(initialId)
  const [detail, setDetail] = useState<TvResult | null>(null)
  const [target, setTarget] = useState("terras_raras")
  const [layer, setLayer] = useState("classe")
  const [opacity, setOpacity] = useState(0.8)
  const [underlay, setUnderlay] = useState(true)
  const [overlay, setOverlay] = useState<Overlay | null>(null)
  const [sat, setSat] = useState<Overlay | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.tvResults().then((r) => {
      setItems(r)
      setSelected((s) => s ?? r[0]?.id)
    })
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    api
      .tvResult(selected)
      .then((d) => {
        setDetail(d)
        const ts = Object.keys(d.summary.targets)
        setTarget((t) => (ts.includes(t) ? t : ts[0]))
        setLayer((l) => (d.layers.includes(l) ? l : "classe"))
      })
      .finally(() => setLoading(false))
  }, [selected])

  useEffect(() => {
    if (!detail) return
    let alive = true
    api.tvLayer(detail.id, layer, target, opacity).then((o) => alive && setOverlay(o)).catch(() => alive && setOverlay(null))
    return () => {
      alive = false
    }
  }, [detail, layer, target, opacity])

  useEffect(() => {
    if (!detail || !detail.layers.includes("satelite")) return setSat(null)
    api.tvLayer(detail.id, "satelite", target, 1).then(setSat).catch(() => setSat(null))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detail])

  const t = detail?.summary.targets[target]
  const zones = detail?.zones[target]
  const total = t ? t.area_por_classe_km2.baixa + t.area_por_classe_km2.media + t.area_por_classe_km2.alta || 1 : 1

  return (
    <div className="flex min-h-0 flex-1">
      <aside className="w-64 shrink-0 overflow-y-auto border-r bg-card/60 p-3">
        <div className="px-2 pt-1 pb-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">Terrenos</div>
        {items.map((it) => (
          <button
            key={it.id}
            type="button"
            onClick={() => setSelected(it.id)}
            className={cn(
              "mb-1 flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-muted",
              selected === it.id && "bg-secondary text-primary hover:bg-secondary"
            )}
          >
            <MapPinned className="mt-0.5 size-4 shrink-0" />
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium">{it.title}</span>
              <span className="block text-xs text-muted-foreground">{it.kind === "demo" ? `Exemplo · ${it.region}` : it.region}</span>
            </span>
          </button>
        ))}
      </aside>

      <div className="relative min-w-0 flex-1">
        <MapCanvas bounds={detail ? boundsOf(detail.geometry) : undefined}>
          {underlay && layer !== "satelite" && <OverlayLayer overlay={sat} z={1} />}
          <OverlayLayer overlay={overlay} z={2} />
          {detail && (
            <GeoJSON
              key={detail.id}
              data={detail.geometry}
              style={{ color: "#0F1B2D", weight: 1.4, dashArray: "6 5", fillOpacity: 0 }}
            />
          )}
          {zones && (
            <GeoJSON
              key={`${detail?.id}-${target}`}
              data={zones}
              style={{ color: "#B4532A", weight: 2.2, fillColor: "#B4532A", fillOpacity: 0.08 }}
            >
              <Tooltip sticky>Zona prioritária</Tooltip>
            </GeoJSON>
          )}
        </MapCanvas>
        {loading && (
          <div className="absolute inset-0 z-[600] flex items-center justify-center bg-background/40">
            <Loader2 className="size-7 animate-spin text-primary" />
          </div>
        )}
      </div>

      <aside className="w-80 shrink-0 overflow-y-auto border-l bg-card">
        {detail && t && (
          <>
            <div className="border-b px-5 py-4">
              <div className="text-lg font-semibold">{detail.title}</div>
              <div className="text-xs text-muted-foreground">{detail.region}</div>
            </div>
            <PanelSection title="Alvo">
              <Segmented
                value={target}
                onChange={setTarget}
                options={Object.keys(detail.summary.targets).map((k) => ({ value: k, label: TARGET_LABEL[k] ?? k }))}
              />
              <div className="mt-4 flex items-center gap-3">
                <span className="size-3 rounded-full" style={{ background: LEVEL[t.classe_final].color }} />
                <div>
                  <div className="font-semibold">Probabilidade {LEVEL[t.classe_final].label.toLowerCase()}</div>
                  <div className="text-xs text-muted-foreground">Confiança dos dados: {LEVEL[t.confianca].label.toLowerCase()}</div>
                </div>
              </div>
              <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-muted">
                {(["baixa", "media", "alta"] as const).map((k) => (
                  <span key={k} style={{ width: `${(t.area_por_classe_km2[k] / total) * 100}%`, background: LEVEL[k].color }} />
                ))}
              </div>
              <div className="mt-2 flex justify-between text-xs text-muted-foreground">
                {(["baixa", "media", "alta"] as const).map((k) => (
                  <span key={k}>
                    {LEVEL[k].label} <span className="font-num">{t.area_por_classe_km2[k].toFixed(1)}</span> km²
                  </span>
                ))}
              </div>
            </PanelSection>
            <PanelSection title="Camada">
              <Segmented
                value={layer}
                onChange={setLayer}
                options={detail.layers.map((l) => ({ value: l, label: LAYER_LABEL[l] ?? l }))}
              />
              <div className="mt-2">
                <ToggleRow
                  label="Satélite por baixo"
                  checked={underlay}
                  disabled={!sat || layer === "satelite"}
                  onChange={setUnderlay}
                />
                <Range label="Opacidade" value={opacity} onChange={setOpacity} />
              </div>
            </PanelSection>
            <PanelSection title="Zonas prioritárias">
              {t.zonas.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhuma zona acima da área mínima (5 ha).</p>
              ) : (
                <ul className="space-y-2">
                  {t.zonas.map((z) => (
                    <li key={z.id} className="flex items-center gap-3 text-sm">
                      <span className="flex size-7 items-center justify-center rounded-lg bg-[#B4532A] font-bold text-white">{z.id}</span>
                      <span>
                        <span className="font-num">{(z.area_km2 * 100).toFixed(1)}</span> ha · pontuação{" "}
                        <span className="font-num">{z.score_medio.toFixed(2)}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              {detail.summary.warnings.some((w) => w.includes("Geologia")) && (
                <Badge variant="outline" className="mt-3">Sem mapa geológico: confiança limitada</Badge>
              )}
            </PanelSection>
            <PanelSection title="Exportar">
              <div className="grid gap-2">
                <Button render={<a href={api.tvReportUrl(detail.id)} />}>
                  <FileDown className="size-4" /> Relatório (PDF)
                </Button>
                <Button variant="outline" render={<a href={api.tvZipUrl(detail.id)} />}>
                  <Archive className="size-4" /> Dados (GeoTIFF e GeoJSON)
                </Button>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Pontuação relativa à área analisada. Triagem: confirme sempre no campo.
              </p>
            </PanelSection>
          </>
        )}
      </aside>
    </div>
  )
}
