import { useEffect, useState } from "react"
import { CircleMarker, GeoJSON, Tooltip } from "react-leaflet"
import { Range, Segmented, PanelSection, ToggleRow } from "@/components/LayerControls"
import { CLASS_COLORS, MapCanvas, OverlayLayer } from "@/components/MapCanvas"
import { api, type Analysis, type Overlay } from "@/lib/api"

const DERIV_LABEL: Record<string, string> = {
  valor: "Valor",
  sinal_analitico: "Sinal analítico",
  derivada_vertical: "1.ª derivada vertical",
  gradiente_horizontal: "Gradiente horizontal",
}

export function MapPage({ a }: { a: Analysis }) {
  const [sat, setSat] = useState(Boolean(a.satellite))
  const [surface, setSurface] = useState(false)
  const [zones, setZones] = useState(true)
  const [allZones, setAllZones] = useState(false)
  const [points, setPoints] = useState(true)
  const [grid, setGrid] = useState<string>("")
  const [deriv, setDeriv] = useState("valor")
  const [opacity, setOpacity] = useState(0.8)
  const [gridOverlay, setGridOverlay] = useState<Overlay | null>(null)
  const [gridError, setGridError] = useState<string | null>(null)

  useEffect(() => {
    if (!grid) {
      setGridOverlay(null)
      return
    }
    let alive = true
    api
      .grid(a.id, grid, deriv)
      .then((o) => alive && (setGridOverlay(o), setGridError(null)))
      .catch((e: Error) => alive && setGridError(e.message))
    return () => {
      alive = false
    }
  }, [a.id, grid, deriv])

  const zoneList = a.zones.filter((z) => z.significant || allZones)

  return (
    <div className="flex min-h-0 flex-1">
      <div className="relative min-w-0 flex-1">
        <MapCanvas bounds={a.bounds}>
          {sat && <OverlayLayer overlay={a.satellite} z={1} />}
          {gridOverlay && <OverlayLayer overlay={gridOverlay} opacity={opacity} z={2} />}
          {surface && <OverlayLayer overlay={a.surface} opacity={opacity} z={3} />}
          {zones &&
            zoneList.map((z) => (
              <GeoJSON
                key={`${z.id}-${allZones}`}
                data={{ type: "Feature", geometry: z.polygon, properties: {} } as GeoJSON.Feature}
                style={{
                  color: z.significant ? "#B4532A" : "#5B6B82",
                  weight: z.significant ? 2.5 : 1.2,
                  dashArray: z.significant ? undefined : "5 4",
                  fillColor: "#B4532A",
                  fillOpacity: z.significant ? 0.1 : 0,
                }}
              >
                <Tooltip sticky>
                  Zona {z.id}: {z.n_samples} amostras elevadas, {z.area_km2.toFixed(1)} km², média {Math.round(z.mean)} ppm
                  {z.significant ? "" : " (compatível com o acaso)"}
                </Tooltip>
              </GeoJSON>
            ))}
          {points &&
            a.points.features.map((f) => {
              const p = f.properties
              const [lon, lat] = f.geometry.coordinates
              return (
                <CircleMarker
                  key={p.id}
                  center={[lat, lon]}
                  radius={p.classe === "elevada" ? 6 : 4}
                  pathOptions={{ color: "#0F1B2D", weight: 0.8, fillColor: CLASS_COLORS[p.classe], fillOpacity: 0.95 }}
                >
                  <Tooltip>
                    {p.id}: {Math.round(p.valor)} ppm · {p.classe}
                    {p.ndpr != null ? ` · NdPr ${Math.round(p.ndpr * 100)} %` : ""}
                  </Tooltip>
                </CircleMarker>
              )
            })}
        </MapCanvas>
        <div className="pointer-events-none absolute bottom-4 left-4 z-[500] rounded-xl border bg-card/95 px-3 py-2 text-xs shadow-md">
          <div className="flex gap-3">
            {(["baixa", "moderada", "elevada"] as const).map((k) => (
              <span key={k} className="flex items-center gap-1.5">
                <span className="size-2.5 rounded-full border border-black/40" style={{ background: CLASS_COLORS[k] }} />
                {k[0].toUpperCase() + k.slice(1)}
              </span>
            ))}
          </div>
        </div>
      </div>

      <aside className="w-80 shrink-0 overflow-y-auto border-l bg-card">
        <PanelSection title="Camadas">
          <ToggleRow label="Amostras por classe" checked={points} onChange={setPoints} />
          <ToggleRow label="Zonas de interesse" checked={zones} onChange={setZones} />
          <ToggleRow label="Incluir zonas não significativas" checked={allZones} disabled={!zones} onChange={setAllZones} />
          <ToggleRow label="Superfície interpolada" hint={a.metric_label} checked={surface} onChange={setSurface} />
          <ToggleRow
            label="Imagem de satélite"
            hint={a.satellite ? "Do módulo TerraVisão" : "Sem imagem para esta área"}
            checked={sat}
            disabled={!a.satellite}
            onChange={setSat}
          />
        </PanelSection>
        <PanelSection title="Grelha geofísica">
          {a.grids.length === 0 ? (
            <p className="text-sm text-muted-foreground">Este conjunto não tem grelhas. Carregue um GeoTIFF junto das amostras.</p>
          ) : (
            <>
              <Segmented
                value={grid}
                onChange={setGrid}
                options={[{ value: "", label: "Nenhuma" }, ...a.grids.map((g) => ({ value: g, label: g }))]}
              />
              {grid && (
                <Segmented
                  className="mt-2"
                  value={deriv}
                  onChange={setDeriv}
                  options={a.derivatives.map((d) => ({ value: d, label: DERIV_LABEL[d] ?? d }))}
                />
              )}
              {gridError && <p className="mt-2 text-xs text-destructive">{gridError}</p>}
            </>
          )}
        </PanelSection>
        <PanelSection title="Aparência">
          <Range label="Opacidade das camadas" value={opacity} onChange={setOpacity} />
        </PanelSection>
      </aside>
    </div>
  )
}
