import { BarChart3, BookOpen, Brain, FileText, LayoutDashboard, Map as MapIcon, MessagesSquare, Plus, Sparkles, UploadCloud, Wand2 } from "lucide-react"
import { useEffect, useState } from "react"
import type { Screen } from "@/App"
import { AiSettings } from "@/components/AiSettings"
import { Guide, type GuideStep } from "@/components/Guide"
import { PageHeader, Shell } from "@/components/Shell"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api, type AiCreds, type Analysis, type Dataset } from "@/lib/api"
import { aiCreds, guide } from "@/lib/storage"
import { AiPage } from "./AiPage"
import { Conversation, type Turn } from "./Conversation"
import { DataPage } from "./DataPage"
import { OverviewPage } from "./OverviewPage"
import { MapPage } from "./MapPage"
import { ReportPage } from "./ReportPage"
import { Welcome } from "./Welcome"

const STEPS: GuideStep[] = [
  {
    icon: UploadCloud,
    title: "Carregue os seus dados",
    text: "Amostras em CSV, GeoJSON ou Shapefile (.zip), exportadas do QGIS ou do Excel, e, se tiver, grelhas geofísicas em GeoTIFF. Coordenadas em UTM 33S ou em lon e lat.",
  },
  {
    icon: Wand2,
    title: "A plataforma analisa",
    text: "Calcula o TREO e o NdPr/TREO, classifica as anomalias, delimita zonas e testa-as contra o acaso, e mede a relação com a magnetometria e a radiometria.",
  },
  {
    icon: MessagesSquare,
    title: "Converse e exporte",
    text: "Pergunte à IA o que quiser sobre os resultados. Veja o mapa no menu e descarregue o relatório técnico em PDF.",
  },
]

type Page = "visao" | "conversa" | "mapa" | "dados" | "ia" | "relatorio"

export function AnalysisSystem({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [page, setPage] = useState<Page>("conversa")
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [turns, setTurns] = useState<Turn[]>([])
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [thinking, setThinking] = useState(false)
  const [guideOpen, setGuideOpen] = useState(!guide.seen("analise"))
  const [aiOpen, setAiOpen] = useState(false)
  const [creds, setCreds] = useState<AiCreds | null>(aiCreds.get())

  useEffect(() => {
    api.datasets().then(setDatasets).catch(() => setDatasets([]))
  }, [])

  const start = (a: Analysis) => {
    setAnalysis(a)
    setTurns([{ role: "assistant", content: a.intro, origin: "offline", cards: true }])
    setPage("conversa")
  }

  const run = async (key: string, job: () => Promise<Analysis>) => {
    setBusy(key)
    setError(null)
    try {
      start(await job())
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(null)
    }
  }

  const ask = async (q: string) => {
    if (!analysis) return
    const history = turns.slice(1)
    setTurns((t) => [...t, { role: "user", content: q }])
    setThinking(true)
    try {
      const r = await api.chat(analysis.id, q, history, creds)
      setTurns((t) => [...t, { role: "assistant", content: r.answer, origin: r.origin }])
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", content: `Não consegui responder: ${(e as Error).message}`, origin: "offline" }])
    } finally {
      setThinking(false)
    }
  }

  const reset = () => {
    setAnalysis(null)
    setTurns([])
    setError(null)
    setPage("conversa")
  }

  const hint = analysis ? undefined : "Carregue dados primeiro"
  const menu = [
    { id: "visao", label: "Visão geral", icon: LayoutDashboard, disabled: !analysis, hint },
    { id: "conversa", label: "Assistente geológico", icon: MessagesSquare },
    { id: "mapa", label: "Cartografia", icon: MapIcon, disabled: !analysis, hint },
    { id: "dados", label: "Análise de dados", icon: BarChart3, disabled: !analysis, hint },
    { id: "ia", label: "Inteligência artificial", icon: Brain, disabled: !analysis, hint },
    { id: "relatorio", label: "Relatório", icon: FileText, disabled: !analysis, hint },
    { id: "guia", label: "Guia", icon: BookOpen },
    { id: "definicoes", label: "Definições da IA", icon: Sparkles },
  ]

  const titles: Record<Page, string> = {
    conversa: analysis ? analysis.title : "Nova análise",
    visao: "Visão geral",
    mapa: "Visualização cartográfica",
    dados: "Análise de dados",
    ia: "Inteligência artificial",
    relatorio: "Relatório e dados",
  }

  return (
    <Shell
      system="Análise de mapa"
      subtitle="GeoExplora IA"
      primary={{ label: "Nova análise", icon: Plus, onClick: reset }}
      menu={menu}
      active={page}
      onSelect={(id) => {
        if (id === "guia") setGuideOpen(true)
        else if (id === "definicoes") setAiOpen(true)
        else setPage(id as Page)
      }}
      switchLabel="Ir para o TerraVisão"
      onSwitch={() => onNavigate("terra")}
      onHome={() => onNavigate("choose")}
    >
      {analysis && (
        <PageHeader
          title={titles[page]}
          description={
            <span className="flex flex-wrap items-center gap-2">
              {analysis.summary.conjunto.n_amostras} amostras · {analysis.metric_label}
              {analysis.fictitious && <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-800">Dados fictícios</Badge>}
            </span>
          }
          actions={
            page !== "conversa" && (
              <Button variant="outline" size="sm" onClick={() => setPage("conversa")}>
                <MessagesSquare className="size-4" /> Voltar à conversa
              </Button>
            )
          }
        />
      )}

      {!analysis && (
        <Welcome
          datasets={datasets}
          busy={busy}
          error={error}
          onDataset={(id) => run(id, () => api.analyseDataset(id))}
          onFiles={(points, grids) => run("upload", () => api.analyseFiles(points, grids))}
        />
      )}
      {analysis && page === "conversa" && (
        <Conversation
          analysis={analysis}
          turns={turns}
          thinking={thinking}
          aiMode={Boolean(creds)}
          onAsk={ask}
          onShowMap={() => setPage("mapa")}
        />
      )}
      {analysis && page === "visao" && <OverviewPage a={analysis} onGo={setPage} />}
      {analysis && page === "mapa" && <MapPage a={analysis} />}
      {analysis && page === "dados" && <DataPage a={analysis} />}
      {analysis && page === "ia" && <AiPage a={analysis} />}
      {analysis && page === "relatorio" && <ReportPage a={analysis} />}

      <Guide
        open={guideOpen}
        steps={STEPS}
        onClose={() => {
          guide.markSeen("analise")
          setGuideOpen(false)
        }}
      />
      <AiSettings open={aiOpen} onOpenChange={setAiOpen} onSaved={setCreds} />
    </Shell>
  )
}
