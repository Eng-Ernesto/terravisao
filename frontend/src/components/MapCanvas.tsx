import { useEffect, useState, type ReactNode } from "react"
import { GeoJSON, ImageOverlay, MapContainer, TileLayer, useMap } from "react-leaflet"
import { api, type LatLngBounds, type Overlay } from "@/lib/api"
import { cn } from "@/lib/utils"

let provincesCache: Promise<GeoJSON.FeatureCollection> | null = null
const loadProvinces = () => (provincesCache ??= api.provinces())

function useProvinces() {
  const [data, setData] = useState<GeoJSON.FeatureCollection | null>(null)
  useEffect(() => {
    loadProvinces().then(setData).catch(() => setData(null))
  }, [])
  return data
}

function FitBounds({ bounds }: { bounds?: LatLngBounds }) {
  const map = useMap()
  const key = bounds ? JSON.stringify(bounds) : ""
  useEffect(() => {
    if (!bounds) return
    // O contentor pode ainda não ter tamanho: medir de novo antes de ajustar.
    const fit = () => {
      map.invalidateSize()
      map.fitBounds(bounds, { padding: [32, 32] })
    }
    fit()
    const t = setTimeout(fit, 250)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return null
}

/** Mapa base offline: fundo claro e limites das províncias de Angola (domínio público). */
export function MapCanvas({
  bounds,
  children,
  className,
  online = false,
}: {
  bounds?: LatLngBounds
  children?: ReactNode
  className?: string
  /** Com internet, mostra um mapa base online por baixo (opcional). */
  online?: boolean
}) {
  const provinces = useProvinces()
  return (
    <MapContainer
      center={[-12.3, 17.5]}
      zoom={6}
      zoomControl
      scrollWheelZoom
      // isolate: as camadas internas do Leaflet (z-index 400+) não passam à frente de diálogos
      className={cn("isolate z-0 h-full w-full", className)}
      attributionControl
    >
      {online && (
        <TileLayer
          url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          attribution="Esri"
          maxZoom={16}
        />
      )}
      {provinces && (
        <GeoJSON
          data={provinces}
          style={{ color: "#9DB4DA", weight: 1, fillOpacity: 0 }}
          onEachFeature={(f, layer) => layer.bindTooltip(String(f.properties?.shapeName ?? ""), { sticky: true })}
        />
      )}
      <FitBounds bounds={bounds} />
      {children}
    </MapContainer>
  )
}

/** Camada de imagem. `z` fixa a ordem (as imagens chegam em tempos diferentes). */
export function OverlayLayer({
  overlay,
  opacity = 1,
  z = 1,
}: {
  overlay: Overlay | null | undefined
  opacity?: number
  z?: number
}) {
  if (!overlay) return null
  return <ImageOverlay key={overlay.png.slice(-40)} url={overlay.png} bounds={overlay.bounds} opacity={opacity} zIndex={z} />
}

export const CLASS_COLORS = { baixa: "#5E7A63", moderada: "#C9A227", elevada: "#B4532A" } as const
