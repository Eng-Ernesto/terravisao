import { BookOpen, Layers, PencilRuler, Satellite, Square, Wand2 } from "lucide-react"
import { useState } from "react"
import type { Screen } from "@/App"
import { Guide, type GuideStep } from "@/components/Guide"
import { PageHeader, Shell } from "@/components/Shell"
import { guide } from "@/lib/storage"
import { DrawPage } from "./DrawPage"
import { ResultsPage } from "./ResultsPage"

const STEPS: GuideStep[] = [
  {
    icon: Square,
    title: "Desenhe o terreno",
    text: "Escolha uma zona no mapa e desenhe um rectângulo ou polígono, ou carregue um GeoJSON. A plataforma confirma que está dentro de Angola e mostra a área.",
  },
  {
    icon: Satellite,
    title: "Análise por satélite",
    text: "Com internet, a plataforma descarrega imagens Sentinel-2 e o relevo, calcula óxido de ferro, argila, drenagem e lineamentos, e delimita zonas prioritárias.",
  },
  {
    icon: Wand2,
    title: "Explore e exporte",
    text: "Em «Resultados», troque de alvo e de camada, veja as zonas e descarregue o relatório PDF. É uma triagem: indica onde confirmar no campo.",
  },
]

type Page = "nova" | "resultados"

export function TerraSystem({ onNavigate }: { onNavigate: (s: Screen) => void }) {
  const [page, setPage] = useState<Page>("resultados")
  const [resultId, setResultId] = useState<string | undefined>()
  const [guideOpen, setGuideOpen] = useState(!guide.seen("terravisao"))

  return (
    <Shell
      system="TerraVisão"
      subtitle="Triagem por satélite"
      primary={{ label: "Desenhar terreno", icon: PencilRuler, onClick: () => setPage("nova") }}
      menu={[
        { id: "resultados", label: "Resultados", icon: Layers },
        { id: "nova", label: "Nova análise", icon: PencilRuler },
        { id: "guia", label: "Guia", icon: BookOpen },
      ]}
      active={page}
      onSelect={(id) => (id === "guia" ? setGuideOpen(true) : setPage(id as Page))}
      switchLabel="Ir para a Análise de mapa"
      onSwitch={() => onNavigate("analysis")}
      onHome={() => onNavigate("choose")}
    >
      <PageHeader
        title={page === "nova" ? "Nova análise" : "Resultados"}
        description={
          page === "nova"
            ? "Desenhe o terreno, escolha os alvos e analise com imagens de satélite públicas."
            : "Terrenos analisados: exemplos incluídos e as suas análises."
        }
      />
      {page === "nova" ? (
        <DrawPage
          onDone={(id) => {
            setResultId(id)
            setPage("resultados")
          }}
        />
      ) : (
        <ResultsPage key={resultId ?? "inicio"} initialId={resultId} />
      )}
      <Guide
        open={guideOpen}
        steps={STEPS}
        onClose={() => {
          guide.markSeen("terravisao")
          setGuideOpen(false)
        }}
      />
    </Shell>
  )
}
