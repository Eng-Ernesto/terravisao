import { Brain, FlaskConical, Layers, MessagesSquare, Target, TriangleAlert } from "lucide-react"
import { CircleMarker, GeoJSON } from "react-leaflet"
import { CLASS_COLORS, MapCanvas, OverlayLayer } from "@/components/MapCanvas"
import { Button } from "@/components/ui/button"
import type { Analysis } from "@/lib/api"

const n = (v: number, d = 0) => v.toLocaleString("pt-PT", { maximumFractionDigits: d, minimumFractionDigits: d })

/** Visão geral: indicadores principais e mapa de relance. */
export function OverviewPage({ a, onGo }: { a: Analysis; onGo: (page: "conversa" | "mapa" | "dados" | "ia") => void }) {
  const s = a.summary
  const sig = a.zones.filter((z) => z.significant)
  const m = s.modelo
  const kpis = [
    { icon: FlaskConical, label: "Amostras", value: n(s.conjunto.n_amostras), hint: s.conjunto.elementos.join(", ") },
    { icon: Layers, label: "Mediana", value: `${n(s.metrica_ppm.mediana)} ppm`, hint: a.metric_label },
    { icon: Target, label: "Zonas de interesse", value: String(sig.length), hint: sig.length ? `Principal: ${sig[0].id}` : "Nenhuma acima do acaso" },
    {
      icon: Brain,
      label: "Modelo",
      value: m.executado ? `${n((m.exatidao ?? 0) * 100)} %` : "—",
      hint: m.executado ? (m.supera_acaso ? "Supera o acaso" : "Não supera o acaso") : (m.motivo ?? ""),
    },
  ]
  const counts = s.classificacao.contagem
  const total = counts.baixa + counts.moderada + counts.elevada || 1

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="rounded-2xl border bg-card p-5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{k.label}</span>
              <span className="flex size-9 items-center justify-center rounded-xl bg-secondary text-primary">
                <k.icon className="size-4" />
              </span>
            </div>
            <div className="font-num mt-2 text-2xl font-medium">{k.value}</div>
            <div className="mt-1 truncate text-xs text-muted-foreground">{k.hint}</div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <div className="overflow-hidden rounded-2xl border bg-card lg:col-span-3">
          <div className="flex items-center justify-between border-b px-5 py-3">
            <span className="font-semibold">Mapa de relance</span>
            <Button variant="ghost" size="sm" onClick={() => onGo("mapa")}>Abrir mapa</Button>
          </div>
          <div className="h-80">
            <MapCanvas bounds={a.bounds}>
              <OverlayLayer overlay={a.satellite} z={1} />
              {sig.map((z) => (
                <GeoJSON
                  key={z.id}
                  data={{ type: "Feature", geometry: z.polygon, properties: {} } as GeoJSON.Feature}
                  style={{ color: "#B4532A", weight: 2.5, fillColor: "#B4532A", fillOpacity: 0.12 }}
                />
              ))}
              {a.points.features
                .filter((f) => f.properties.classe === "elevada")
                .map((f) => (
                  <CircleMarker
                    key={f.properties.id}
                    center={[f.geometry.coordinates[1], f.geometry.coordinates[0]]}
                    radius={4}
                    pathOptions={{ color: "#0F1B2D", weight: 0.7, fillColor: CLASS_COLORS.elevada, fillOpacity: 0.95 }}
                  />
                ))}
            </MapCanvas>
          </div>
        </div>

        <div className="flex flex-col gap-5 lg:col-span-2">
          <div className="rounded-2xl border bg-card p-5">
            <div className="font-semibold">Classes de anomalia</div>
            <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-muted">
              {(["baixa", "moderada", "elevada"] as const).map((k) => (
                <span key={k} style={{ width: `${(counts[k] / total) * 100}%`, background: CLASS_COLORS[k] }} />
              ))}
            </div>
            <div className="mt-3 grid grid-cols-3 text-sm">
              {(["baixa", "moderada", "elevada"] as const).map((k) => (
                <div key={k}>
                  <div className="text-xs text-muted-foreground">{k[0].toUpperCase() + k.slice(1)}</div>
                  <div className="font-num">{counts[k]}</div>
                </div>
              ))}
            </div>
            {s.ndpr_sobre_treo != null && (
              <div className="mt-4 rounded-xl bg-secondary px-3 py-2 text-sm text-secondary-foreground">
                NdPr/TREO médio <span className="font-num font-semibold">{n(s.ndpr_sobre_treo * 100, 1)} %</span> · elementos
                para ímanes permanentes
              </div>
            )}
          </div>
          <div className="rounded-2xl border bg-card p-5">
            <div className="font-semibold">Próximos passos</div>
            <div className="mt-3 grid gap-2">
              <Button variant="outline" className="justify-start" onClick={() => onGo("conversa")}>
                <MessagesSquare className="size-4" /> Perguntar à IA
              </Button>
              <Button variant="outline" className="justify-start" onClick={() => onGo("dados")}>
                <Layers className="size-4" /> Ver a análise de dados
              </Button>
              <Button variant="outline" className="justify-start" onClick={() => onGo("ia")}>
                <Brain className="size-4" /> Ver o modelo de IA
              </Button>
            </div>
          </div>
          {(a.fictitious || a.warnings.length > 0) && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-900">
              <div className="flex items-center gap-2 font-semibold">
                <TriangleAlert className="size-4" /> Avisos
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4">
                {a.fictitious && <li>Dados fictícios: demonstração.</li>}
                {a.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
