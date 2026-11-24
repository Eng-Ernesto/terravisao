import { Search } from "lucide-react"
import { useMemo, useState } from "react"
import { Segmented } from "@/components/LayerControls"
import { CLASS_COLORS } from "@/components/MapCanvas"
import { Input } from "@/components/ui/input"
import type { Analysis, ClassName } from "@/lib/api"

const n = (v: number, d = 1) => v.toLocaleString("pt-PT", { maximumFractionDigits: d })

/** Análise de dados: estatística, histograma com limiares e tabela de amostras. */
export function DataPage({ a }: { a: Analysis }) {
  const [filter, setFilter] = useState<"todas" | ClassName>("todas")
  const [q, setQ] = useState("")
  const th = a.summary.classificacao.limiares_ppm
  const values = a.points.features.map((f) => f.properties.valor)

  const bins = useMemo(() => {
    const min = Math.min(...values)
    const max = Math.max(...values)
    const k = 30
    const w = (max - min) / k || 1
    const counts = Array.from({ length: k }, (_, i) => ({ x0: min + i * w, x1: min + (i + 1) * w, c: 0 }))
    values.forEach((v) => counts[Math.min(k - 1, Math.floor((v - min) / w))].c++)
    return { counts, min, max, top: Math.max(...counts.map((b) => b.c)) }
  }, [values])

  const rows = a.points.features
    .map((f) => f.properties)
    .filter((p) => (filter === "todas" || p.classe === filter) && p.id.toLowerCase().includes(q.toLowerCase()))
    .sort((x, y) => y.valor - x.valor)

  const pos = (v: number) => ((v - bins.min) / (bins.max - bins.min || 1)) * 100

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <div className="rounded-2xl border bg-card p-5">
        <div className="flex items-baseline justify-between">
          <span className="font-semibold">Distribuição: {a.metric_label}</span>
          <span className="text-xs text-muted-foreground">limiares do método «{a.summary.classificacao.metodo}»</span>
        </div>
        <div className="relative mt-4 flex h-44 items-end gap-[2px]">
          {bins.counts.map((b, i) => {
            const mid = (b.x0 + b.x1) / 2
            const cls: ClassName = mid >= th.elevada ? "elevada" : mid >= th.moderada ? "moderada" : "baixa"
            return (
              <div
                key={i}
                title={`${n(b.x0, 0)}–${n(b.x1, 0)} ppm: ${b.c} amostras`}
                className="flex-1 rounded-t-sm"
                style={{ height: `${(b.c / (bins.top || 1)) * 100}%`, background: CLASS_COLORS[cls], opacity: 0.85 }}
              />
            )
          })}
          {(["moderada", "elevada"] as const).map((k) => (
            <div key={k} className="pointer-events-none absolute inset-y-0 border-l-2 border-dashed" style={{ left: `${pos(th[k])}%`, borderColor: CLASS_COLORS[k] }}>
              <span className="font-num absolute -top-1 left-1 text-[11px]" style={{ color: CLASS_COLORS[k] }}>
                {n(th[k], 0)}
              </span>
            </div>
          ))}
        </div>
        <div className="font-num mt-1 flex justify-between text-[11px] text-muted-foreground">
          <span>{n(bins.min, 0)} ppm</span>
          <span>{n(bins.max, 0)} ppm</span>
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-2xl border bg-card">
        <div className="border-b px-5 py-3 font-semibold">Estatística descritiva</div>
        <table className="w-full text-sm">
          <thead className="bg-muted/60 text-xs text-muted-foreground">
            <tr>
              {["Variável", "n", "Mínimo", "Mediana", "Média", "Máximo", "Desvio"].map((h) => (
                <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="font-num">
            {a.stats.map((s) => (
              <tr key={s.variavel} className="border-t">
                <td className="px-4 py-2 font-sans font-medium">{s.variavel}</td>
                <td className="px-4 py-2">{s.n}</td>
                <td className="px-4 py-2">{n(s.min, 2)}</td>
                <td className="px-4 py-2">{n(s.mediana, 2)}</td>
                <td className="px-4 py-2">{n(s.media, 2)}</td>
                <td className="px-4 py-2">{n(s.max, 2)}</td>
                <td className="px-4 py-2">{n(s.desvio, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-5 overflow-hidden rounded-2xl border bg-card">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-3">
          <span className="font-semibold">Amostras ({rows.length})</span>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute top-2 left-2.5 size-4 text-muted-foreground" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Procurar amostra" className="h-8 w-44 pl-8" />
            </div>
            <Segmented
              value={filter}
              onChange={setFilter}
              options={[
                { value: "todas", label: "Todas" },
                { value: "elevada", label: "Elevada" },
                { value: "moderada", label: "Moderada" },
                { value: "baixa", label: "Baixa" },
              ]}
            />
          </div>
        </div>
        <div className="max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-card text-xs text-muted-foreground">
              <tr>
                {["Amostra", a.metric_label.split(" (")[0] + " (ppm)", "NdPr/TREO", "Classe"].map((h) => (
                  <th key={h} className="px-4 py-2 text-left font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.slice(0, 300).map((p) => (
                <tr key={p.id} className="border-t">
                  <td className="px-4 py-1.5 font-medium">{p.id}</td>
                  <td className="font-num px-4 py-1.5">{n(p.valor, 0)}</td>
                  <td className="font-num px-4 py-1.5">{p.ndpr != null ? `${n(p.ndpr * 100)} %` : "—"}</td>
                  <td className="px-4 py-1.5">
                    <span className="inline-flex items-center gap-1.5">
                      <span className="size-2 rounded-full" style={{ background: CLASS_COLORS[p.classe] }} />
                      {p.classe[0].toUpperCase() + p.classe.slice(1)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
