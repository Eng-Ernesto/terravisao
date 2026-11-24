import { FileDown, FileSpreadsheet, TriangleAlert } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { api, type Analysis } from "@/lib/api"

export function ReportPage({ a }: { a: Analysis }) {
  const s = a.summary
  const stats = [
    { label: "Amostras", value: s.conjunto.n_amostras.toLocaleString("pt-PT") },
    { label: "Mediana", value: `${Math.round(s.metrica_ppm.mediana).toLocaleString("pt-PT")} ppm` },
    { label: "Máximo", value: `${Math.round(s.metrica_ppm.max).toLocaleString("pt-PT")} ppm` },
    {
      label: "Zonas significativas",
      value: String(a.zones.filter((z) => z.significant).length),
    },
  ]
  return (
    <div className="mx-auto w-full max-w-4xl flex-1 overflow-y-auto px-8 py-8">
      <div className="grid gap-4 sm:grid-cols-4">
        {stats.map((x) => (
          <div key={x.label} className="rounded-2xl border bg-card p-4">
            <div className="text-xs text-muted-foreground">{x.label}</div>
            <div className="font-num mt-1 text-xl font-medium">{x.value}</div>
          </div>
        ))}
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="flex flex-col rounded-3xl border bg-card p-6">
          <div className="flex size-11 items-center justify-center rounded-2xl bg-secondary text-primary">
            <FileDown className="size-6" />
          </div>
          <h2 className="mt-4 text-lg font-semibold">Relatório técnico (PDF)</h2>
          <p className="mt-1 flex-1 text-sm text-muted-foreground">
            Interpretação, mapas das amostras e das zonas, superfície, grelhas e derivadas, estatística, relação com a
            geofísica, modelo, metodologia e limitações.
          </p>
          <Button className="mt-5 w-fit" render={<a href={api.reportUrl(a.id)} />}>
            <FileDown className="size-4" /> Descarregar PDF
          </Button>
        </div>
        <div className="flex flex-col rounded-3xl border bg-card p-6">
          <div className="flex size-11 items-center justify-center rounded-2xl bg-secondary text-primary">
            <FileSpreadsheet className="size-6" />
          </div>
          <h2 className="mt-4 text-lg font-semibold">Amostras classificadas (CSV)</h2>
          <p className="mt-1 flex-1 text-sm text-muted-foreground">
            As suas amostras com coordenadas, {a.metric_label}, NdPr/TREO e a classe de anomalia, para abrir no QGIS ou
            no Excel.
          </p>
          <Button variant="outline" className="mt-5 w-fit" render={<a href={api.csvUrl(a.id)} />}>
            <FileSpreadsheet className="size-4" /> Descarregar CSV
          </Button>
        </div>
      </div>

      {(a.fictitious || a.warnings.length > 0) && (
        <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          <div className="flex items-center gap-2 font-semibold">
            <TriangleAlert className="size-4" /> Antes de usar estes resultados
          </div>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {a.fictitious && <li>Os dados são fictícios: servem só para demonstração.</li>}
            {a.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
            <li>As classes são relativas ao conjunto de dados, não são teores económicos.</li>
          </ul>
          {a.fictitious && <Badge className="mt-3" variant="outline">Dados fictícios</Badge>}
        </div>
      )}
    </div>
  )
}
