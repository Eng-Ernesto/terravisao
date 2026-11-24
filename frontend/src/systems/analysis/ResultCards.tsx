import { ChevronDown, Layers, Magnet, ShieldCheck, ShieldX, Target } from "lucide-react"
import { CLASS_COLORS } from "@/components/MapCanvas"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import type { Analysis } from "@/lib/api"
import { cn } from "@/lib/utils"

const n = (v: number, d = 0) => v.toLocaleString("pt-PT", { maximumFractionDigits: d, minimumFractionDigits: d })

function CardShell({ icon: Icon, title, children }: { icon: typeof Layers; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border bg-card p-4">
      <div className="flex items-center gap-2 text-sm font-semibold">
        <Icon className="size-4 text-primary" /> {title}
      </div>
      <div className="mt-3">{children}</div>
    </div>
  )
}

/** Cartões de resultado mostrados na primeira resposta do assistente. */
export function ResultCards({ a }: { a: Analysis }) {
  const s = a.summary
  const counts = s.classificacao.contagem
  const total = counts.baixa + counts.moderada + counts.elevada || 1
  const sig = a.zones.filter((z) => z.significant)
  const others = a.zones.filter((z) => !z.significant)
  const m = s.modelo

  return (
    <div className="mt-3 grid gap-3 md:grid-cols-2">
      <CardShell icon={Layers} title="Classificação das amostras">
        <div className="flex h-2.5 overflow-hidden rounded-full bg-muted">
          {(["baixa", "moderada", "elevada"] as const).map((k) => (
            <span key={k} style={{ width: `${(counts[k] / total) * 100}%`, background: CLASS_COLORS[k] }} />
          ))}
        </div>
        <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
          {(["baixa", "moderada", "elevada"] as const).map((k) => (
            <div key={k}>
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <span className="size-2 rounded-full" style={{ background: CLASS_COLORS[k] }} />
                {k[0].toUpperCase() + k.slice(1)}
              </div>
              <div className="font-num text-base font-medium">{counts[k]}</div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-xs text-muted-foreground">
          Elevada ≥ <span className="font-num">{n(s.classificacao.limiares_ppm.elevada)}</span> ppm · {a.metric_label}
        </div>
      </CardShell>

      <CardShell icon={Target} title="Zonas de interesse">
        {sig.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhuma zona é maior do que o esperado por acaso.</p>
        ) : (
          <ul className="space-y-2">
            {sig.map((z) => (
              <li key={z.id} className="flex items-center gap-3">
                <span className="flex size-7 items-center justify-center rounded-lg bg-[#B4532A] text-sm font-bold text-white">{z.id}</span>
                <div className="text-sm">
                  <span className="font-num">{z.n_samples}</span> amostras · <span className="font-num">{n(z.area_km2, 1)}</span> km² ·
                  média <span className="font-num">{n(z.mean)}</span> ppm
                  {z.ndpr != null && (
                    <span className="text-muted-foreground"> · NdPr {n(z.ndpr * 100)} %</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
        {others.length > 0 && (
          <Collapsible className="mt-3">
            <CollapsibleTrigger className="group flex items-center gap-1 text-xs font-medium text-primary">
              {others.length} grupo(s) compatíveis com o acaso
              <ChevronDown className="size-3.5 transition group-data-[panel-open]:rotate-180" />
            </CollapsibleTrigger>
            <CollapsibleContent>
              <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                {others.map((z) => (
                  <li key={z.id}>
                    Grupo {z.id}: {z.n_samples} amostras, {n(z.area_km2, 1)} km², média {n(z.mean)} ppm
                  </li>
                ))}
              </ul>
            </CollapsibleContent>
          </Collapsible>
        )}
      </CardShell>

      <CardShell icon={Magnet} title="Relação com a geofísica">
        {s.relacoes.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem variáveis geofísicas para comparar.</p>
        ) : (
          <ul className="space-y-2">
            {s.relacoes.slice(0, 4).map((r) => (
              <li key={r.variavel} className="text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="truncate">{r.variavel.replace("grelha:", "")}</span>
                  <span className="font-num">{r.rho_spearman >= 0 ? "+" : ""}{n(r.rho_spearman, 2)}</span>
                </div>
                <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted">
                  <span
                    className="block h-full rounded-full bg-primary"
                    style={{ width: `${Math.min(Math.abs(r.rho_spearman), 1) * 100}%`, opacity: r.leitura === "sem relação relevante" ? 0.35 : 1 }}
                  />
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">{r.leitura}</div>
              </li>
            ))}
          </ul>
        )}
      </CardShell>

      <CardShell icon={m.supera_acaso ? ShieldCheck : ShieldX} title="Modelo de apoio (Random Forest)">
        {!m.executado ? (
          <p className="text-sm text-muted-foreground">Não executado: {m.motivo}</p>
        ) : (
          <>
            <span
              className={cn(
                "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
                m.supera_acaso ? "bg-emerald-50 text-emerald-700" : "bg-orange-50 text-orange-700"
              )}
            >
              {m.supera_acaso ? "Supera o acaso" : "Não supera o acaso"}
            </span>
            <div className="mt-3 flex items-end gap-6 text-sm">
              <div>
                <div className="text-xs text-muted-foreground">Exatidão</div>
                <div className="font-num text-xl font-medium">{n((m.exatidao ?? 0) * 100)} %</div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground">Acaso</div>
                <div className="font-num text-xl font-medium text-muted-foreground">{n((m.acaso ?? 0) * 100)} %</div>
              </div>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">Validação por blocos espaciais.</p>
          </>
        )}
      </CardShell>
    </div>
  )
}
