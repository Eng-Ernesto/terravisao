// Cliente da API do GeoExplora IA (FastAPI em /api).

export type LatLngBounds = [[number, number], [number, number]]
export type Overlay = { png: string; bounds: LatLngBounds }
export type ClassName = "baixa" | "moderada" | "elevada"

export type Dataset = { id: string; title: string; fictitious: boolean; note: string; grids: string[] }

export type Zone = {
  id: string
  n_samples: number
  area_km2: number
  mean: number
  max: number
  ndpr: number | null
  significant: boolean
  centroid: [number, number]
  polygon: GeoJSON.Geometry
}

export type Correlation = { variavel: string; rho_spearman: number; p_valor: number; leitura: string; n: number }

export type Summary = {
  conjunto: { titulo: string; ficticio: boolean; n_amostras: number; elementos: string[]; covariaveis: string[]; metrica: string }
  metrica_ppm: { min: number; mediana: number; media: number; max: number }
  ndpr_sobre_treo: number | null
  classificacao: { metodo: string; limiares_ppm: { moderada: number; elevada: number }; contagem: Record<ClassName, number> }
  relacoes: Correlation[]
  modelo: {
    executado: boolean
    motivo?: string
    exatidao?: number
    acaso?: number
    p_valor_vs_acaso?: number
    supera_acaso?: boolean
    importancia?: Record<string, number>
    leitura?: string
  }
  avisos: string[]
}

export type PointProps = { id: string; valor: number; classe: ClassName; ndpr: number | null }

export type Analysis = {
  id: string
  title: string
  fictitious: boolean
  metric_label: string
  summary: Summary
  intro: string
  points: GeoJSON.FeatureCollection<GeoJSON.Point, PointProps>
  zones: Zone[]
  surface: Overlay
  satellite: Overlay | null
  grids: string[]
  derivatives: string[]
  bounds: LatLngBounds
  warnings: string[]
  stats: Stat[]
}

export type Stat = { variavel: string; n: number; min: number; mediana: number; media: number; max: number; desvio: number }

export type ChatMessage = { role: "user" | "assistant"; content: string; origin?: string }

export type TvResultItem = { id: string; title: string; region: string; kind: "demo" | "run"; has_rgb: boolean }
export type TvTarget = {
  classe_final: "baixa" | "media" | "alta"
  confianca: "baixa" | "media" | "alta"
  area_por_classe_km2: Record<"baixa" | "media" | "alta", number>
  zonas: { id: string; area_km2: number; score_medio: number }[]
}
export type TvResult = {
  id: string
  title: string
  region: string
  geometry: GeoJSON.Polygon | GeoJSON.MultiPolygon
  summary: { warnings: string[]; targets: Record<string, TvTarget> }
  zones: Record<string, GeoJSON.FeatureCollection | null>
  layers: string[]
  created_at?: string
}
export type Job = { id: string; status: "running" | "done" | "error"; progress: number; message: string; result_id?: string; error?: string }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    let detail = `Erro ${res.status}`
    try {
      const body = await res.json()
      if (typeof body.detail === "string") detail = body.detail
    } catch {
      /* resposta sem JSON */
    }
    throw new Error(detail)
  }
  return (await res.json()) as T
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
})

export const api = {
  online: () => request<{ online: boolean }>("/api/online"),
  provinces: () => request<GeoJSON.FeatureCollection>("/api/reference/provinces"),
  datasets: () => request<Dataset[]>("/api/datasets"),
  analyseDataset: (dataset: string) => {
    const f = new FormData()
    f.append("dataset", dataset)
    return request<Analysis>("/api/analyses", { method: "POST", body: f })
  },
  analyseFiles: (points: File, grids: File[], epsg?: number) => {
    const f = new FormData()
    f.append("points", points)
    grids.forEach((g) => f.append("grids", g))
    if (epsg) f.append("epsg", String(epsg))
    return request<Analysis>("/api/analyses", { method: "POST", body: f })
  },
  grid: (id: string, name: string, derivative: string) =>
    request<Overlay & { min: number; max: number }>(
      `/api/analyses/${id}/grid?name=${encodeURIComponent(name)}&derivative=${derivative}`
    ),
  chat: (id: string, question: string, history: ChatMessage[], creds: AiCreds | null) =>
    request<{ answer: string; origin: string }>(
      `/api/analyses/${id}/chat`,
      json({
        question,
        history: history.map(({ role, content }) => ({ role, content })),
        account_id: creds?.accountId || null,
        token: creds?.token || null,
      })
    ),
  reportUrl: (id: string) => `/api/analyses/${id}/report.pdf`,
  csvUrl: (id: string) => `/api/analyses/${id}/samples.csv`,

  tvResults: () => request<TvResultItem[]>("/api/terravisao/results"),
  tvResult: (id: string) => request<TvResult>(`/api/terravisao/results/${encodeURIComponent(id)}`),
  tvLayer: (id: string, layer: string, target: string, opacity: number) =>
    request<Overlay>(
      `/api/terravisao/results/${encodeURIComponent(id)}/layer?layer=${layer}&target=${target}&opacity=${opacity}`
    ),
  tvReportUrl: (id: string) => `/api/terravisao/results/${encodeURIComponent(id)}/report.pdf`,
  tvZipUrl: (id: string) => `/api/terravisao/results/${encodeURIComponent(id)}/data.zip`,
  tvValidate: (geometry: GeoJSON.Polygon) =>
    request<{ ok: boolean; area_km2?: number; error?: string }>("/api/terravisao/validate", json({ geometry })),
  tvStartJob: (geometry: GeoJSON.Polygon, targets: string[], name: string) =>
    request<Job>("/api/terravisao/jobs", json({ geometry, targets, name })),
  tvJob: (id: string) => request<Job>(`/api/terravisao/jobs/${id}`),
}

export type AiCreds = { accountId: string; token: string }
