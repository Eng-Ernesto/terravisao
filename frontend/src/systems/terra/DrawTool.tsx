import { latLng, latLngBounds, type LatLng } from "leaflet"
import { useEffect, useState } from "react"
import { Polygon, Polyline, Rectangle, useMap, useMapEvents } from "react-leaflet"

export type DrawMode = "none" | "rect" | "poly"

export function toPolygon(points: LatLng[]): GeoJSON.Polygon {
  const ring = points.map((p) => [Number(p.lng.toFixed(6)), Number(p.lat.toFixed(6))])
  ring.push(ring[0])
  return { type: "Polygon", coordinates: [ring] }
}

/** Desenho de rectângulo (arrastar) ou polígono (cliques; duplo clique ou «Concluir» fecha). */
export function DrawTool({
  mode,
  vertices,
  setVertices,
  onShape,
}: {
  mode: DrawMode
  vertices: LatLng[]
  setVertices: (v: LatLng[]) => void
  onShape: (g: GeoJSON.Polygon) => void
}) {
  const map = useMap()
  const [start, setStart] = useState<LatLng | null>(null)
  const [cursor, setCursor] = useState<LatLng | null>(null)

  useEffect(() => {
    const drawing = mode !== "none"
    if (drawing) {
      map.dragging.disable()
      map.doubleClickZoom.disable()
    } else {
      map.dragging.enable()
      map.doubleClickZoom.enable()
    }
    map.getContainer().style.cursor = drawing ? "crosshair" : ""
    return () => {
      map.dragging.enable()
      map.doubleClickZoom.enable()
      map.getContainer().style.cursor = ""
    }
  }, [map, mode])

  useMapEvents({
    mousedown(e) {
      if (mode === "rect") {
        setStart(e.latlng)
        setCursor(e.latlng)
      }
    },
    mousemove(e) {
      if (mode !== "none") setCursor(e.latlng)
    },
    mouseup(e) {
      if (mode !== "rect" || !start) return
      const a = map.latLngToContainerPoint(start)
      const b = map.latLngToContainerPoint(e.latlng)
      setStart(null)
      if (Math.abs(a.x - b.x) < 6 || Math.abs(a.y - b.y) < 6) return // clique sem arrastar
      const s = Math.min(start.lat, e.latlng.lat)
      const n = Math.max(start.lat, e.latlng.lat)
      const w = Math.min(start.lng, e.latlng.lng)
      const east = Math.max(start.lng, e.latlng.lng)
      onShape(toPolygon([latLng(s, w), latLng(s, east), latLng(n, east), latLng(n, w)]))
    },
    click(e) {
      if (mode === "poly") setVertices([...vertices, e.latlng])
    },
    dblclick() {
      if (mode === "poly" && vertices.length >= 3) {
        onShape(toPolygon(vertices))
        setVertices([])
      }
    },
  })

  const style = { color: "#1A5BD7", weight: 2, fillColor: "#1A5BD7", fillOpacity: 0.12 }
  return (
    <>
      {mode === "rect" && start && cursor && <Rectangle bounds={latLngBounds(start, cursor)} pathOptions={style} />}
      {mode === "poly" && vertices.length > 0 && (
        <>
          <Polyline positions={cursor ? [...vertices, cursor] : vertices} pathOptions={{ ...style, dashArray: "4 4" }} />
          {vertices.length >= 3 && <Polygon positions={vertices} pathOptions={{ ...style, weight: 0 }} />}
        </>
      )}
    </>
  )
}
