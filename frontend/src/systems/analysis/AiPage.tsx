import { Brain, CheckCircle2, Info, XCircle } from "lucide-react"
import type { Analysis } from "@/lib/api"
import { cn } from "@/lib/utils"

const n = (v: number, d = 0) => v.toLocaleString("pt-PT", { maximumFractionDigits: d, minimumFractionDigits: d })

/** Inteligência artificial: o que o modelo faz, se funciona e que variáveis pesam. */
export function AiPage({ a }: { a: Analysis }) {
  const m = a.summary.modelo
  const rel = a.summary.relacoes
  const imp = Object.entries(m.importancia ?? {})
  const maxImp = Math.max(0.0001, ...imp.map(([, v]) => Math.abs(v)))

  return (
    <div className="flex-1 overflow-y-auto px-8 py-6">
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5 lg:col-span-2">
          <div className="flex items-center gap-2 font-semibold">
            <Brain className="size-5 text-primary" /> Modelo de apoio (Random Forest)
          </div>
          {!m.executado ? (
            <p className="mt-3 text-sm text-muted-foreground">Não executado: {m.motivo}</p>
          ) : (
            <>
              <div
                className={cn(
                  "mt-4 flex items-start gap-3 rounded-xl p-4",
                  m.supera_acaso ? "bg-emerald-50 text-emerald-900" : "bg-orange-50 text-orange-900"
                )}
              >
                {m.supera_acaso ? <CheckCircle2 className="mt-0.5 size-5 shrink-0" /> : <XCircle className="mt-0.5 size-5 shrink-0" />}
                <p className="text-sm leading-relaxed">{m.leitura}</p>
              </div>
              <div className="mt-6 space-y-4">
                {[
                  { label: "Exatidão do modelo", v: m.exatidao ?? 0, cls: "bg-primary" },
                  { label: "Acaso (classe mais frequente)", v: m.acaso ?? 0, cls: "bg-muted-foreground/40" },
                ].map((b) => (
                  <div key={b.label}>
                    <div className="flex justify-between text-sm">
                      <span>{b.label}</span>
                      <span className="font-num">{n(b.v * 100)} %</span>
                    </div>
                    <div className="mt-1.5 h-3 overflow-hidden rounded-full bg-muted">
                      <div className={cn("h-full rounded-full", b.cls)} style={{ width: `${b.v * 100}%` }} />
                    </div>
                  </div>
                ))}
                <p className="text-xs text-muted-foreground">
                  p = <span className="font-num">{n(m.p_valor_vs_acaso ?? 1, 3)}</span> contra o acaso · validação cruzada por blocos espaciais
                  (o modelo nunca é avaliado em zonas que viu no treino).
                </p>
              </div>
            </>
          )}
        </div>

        <div className="rounded-2xl border bg-card p-5">
          <div className="flex items-center gap-2 font-semibold">
            <Info className="size-4 text-primary" /> Como funciona
          </div>
          <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted-foreground">
            <li>As amostras são classificadas pelo teor (baixa, moderada, elevada).</li>
            <li>O modelo tenta prever essa classe só com a geofísica (magnetometria, radiometria, grelhas), sem usar os elementos.</li>
            <li>Se acertar mais do que o acaso, a geofísica ajuda a encontrar zonas onde ainda não há amostras.</li>
            <li>O assistente de chat só lê estes resultados: não calcula nem inventa.</li>
          </ol>
        </div>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border bg-card p-5">
          <div className="font-semibold">Importância das variáveis</div>
          <p className="mt-1 text-xs text-muted-foreground">Quanto piora o modelo quando a variável é baralhada (permutação).</p>
          {imp.length === 0 ? (
            <p className="mt-3 text-sm text-muted-foreground">Sem variáveis geofísicas.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {imp.map(([k, v]) => (
                <li key={k}>
                  <div className="flex justify-between text-sm">
                    <span className="truncate">{k.replace("grelha:", "")}</span>
                    <span className="font-num">{n(v, 3)}</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${(Math.max(v, 0) / maxImp) * 100}%` }} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="rounded-2xl border bg-card p-5">
          <div className="font-semibold">Relação com o teor (Spearman)</div>
          <p className="mt-1 text-xs text-muted-foreground">De −1 a +1. Perto de 0 = sem relação.</p>
          <ul className="mt-4 space-y-3">
            {rel.map((r) => (
              <li key={r.variavel}>
                <div className="flex justify-between text-sm">
                  <span className="truncate">{r.variavel.replace("grelha:", "")}</span>
                  <span className="font-num">{r.rho_spearman >= 0 ? "+" : ""}{n(r.rho_spearman, 2)}</span>
                </div>
                <div className="relative mt-1 h-2 rounded-full bg-muted">
                  <div className="absolute inset-y-0 left-1/2 w-px bg-border" />
                  <div
                    className="absolute inset-y-0 rounded-full bg-primary"
                    style={
                      r.rho_spearman >= 0
                        ? { left: "50%", width: `${r.rho_spearman * 50}%` }
                        : { right: "50%", width: `${-r.rho_spearman * 50}%` }
                    }
                  />
                </div>
                <div className="mt-0.5 text-xs text-muted-foreground">{r.leitura} · n = {r.n}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
