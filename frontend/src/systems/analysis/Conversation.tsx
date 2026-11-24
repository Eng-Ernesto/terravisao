import { motion } from "motion/react"
import { ArrowUp, FileDown, Map as MapIcon, Sparkles, User } from "lucide-react"
import { Fragment, useEffect, useRef, useState, type ReactNode } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import type { Analysis, ChatMessage } from "@/lib/api"
import { cn } from "@/lib/utils"
import { ResultCards } from "./ResultCards"

const SUGGESTIONS = [
  "Resume o resultado",
  "Onde estão as zonas?",
  "Há relação com a geofísica?",
  "O modelo funciona?",
  "Qual a fracção de NdPr?",
  "Qual o próximo passo?",
]

/** Negrito (**texto**) e listas («- item») sem HTML: o texto vem sempre como texto. */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : <Fragment key={i}>{part}</Fragment>
  )
}

function RichText({ text }: { text: string }) {
  return (
    <div className="space-y-2.5">
      {text.split(/\n{2,}/).map((block, i) => {
        const lines = block.split("\n")
        if (lines.every((l) => l.trim().startsWith("- ") || l.trim() === "") || lines.slice(1).every((l) => l.trim().startsWith("- "))) {
          const head = lines[0].trim().startsWith("- ") ? null : lines[0]
          const items = lines.filter((l) => l.trim().startsWith("- "))
          if (items.length)
            return (
              <div key={i}>
                {head && <p>{inline(head)}</p>}
                <ul className="mt-1 list-disc space-y-1 pl-5">
                  {items.map((l, k) => (
                    <li key={k}>{inline(l.trim().slice(2))}</li>
                  ))}
                </ul>
              </div>
            )
        }
        return (
          <p key={i} className="whitespace-pre-line">
            {inline(block)}
          </p>
        )
      })}
    </div>
  )
}

export type Turn = ChatMessage & { cards?: boolean }

export function Conversation({
  analysis,
  turns,
  thinking,
  aiMode,
  onAsk,
  onShowMap,
}: {
  analysis: Analysis
  turns: Turn[]
  thinking: boolean
  aiMode: boolean
  onAsk: (q: string) => void
  onShowMap: () => void
}) {
  const [text, setText] = useState("")
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [turns.length, thinking])

  const send = (q: string) => {
    const t = q.trim()
    if (!t || thinking) return
    onAsk(t)
    setText("")
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
          {turns.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={cn("flex gap-3", t.role === "user" && "flex-row-reverse")}
            >
              <div
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full",
                  t.role === "user" ? "bg-muted text-muted-foreground" : "bg-primary text-white"
                )}
              >
                {t.role === "user" ? <User className="size-4" /> : <Sparkles className="size-4" />}
              </div>
              <div className={cn("min-w-0", t.role === "user" ? "max-w-[75%]" : "flex-1")}>
                <div
                  className={cn(
                    "text-[15px] leading-relaxed",
                    t.role === "user" ? "rounded-2xl rounded-tr-md bg-primary px-4 py-2.5 text-white" : "text-foreground"
                  )}
                >
                  <RichText text={t.content} />
                </div>
                {t.cards && (
                  <>
                    <ResultCards a={analysis} />
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button variant="outline" size="sm" onClick={onShowMap}>
                        <MapIcon className="size-4" /> Ver no mapa
                      </Button>
                      <Button variant="outline" size="sm" render={<a href={`/api/analyses/${analysis.id}/report.pdf`} />}>
                        <FileDown className="size-4" /> Relatório técnico (PDF)
                      </Button>
                    </div>
                  </>
                )}
                {t.role === "assistant" && t.origin === "ia" && (
                  <div className="mt-1.5 text-xs text-muted-foreground">Resposta da IA, com base nos resultados calculados</div>
                )}
              </div>
            </motion.div>
          ))}
          {thinking && (
            <div className="flex items-center gap-3 text-sm text-muted-foreground">
              <div className="flex size-8 items-center justify-center rounded-full bg-primary text-white">
                <Sparkles className="size-4" />
              </div>
              <span className="flex gap-1">
                {[0, 1, 2].map((d) => (
                  <motion.span
                    key={d}
                    className="size-1.5 rounded-full bg-primary"
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1, repeat: Infinity, delay: d * 0.2 }}
                  />
                ))}
              </span>
              A analisar…
            </div>
          )}
          <div ref={end} />
        </div>
      </div>

      <div className="border-t bg-card/70 px-6 pt-3 pb-5 backdrop-blur">
        <div className="mx-auto max-w-3xl">
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                disabled={thinking}
                onClick={() => send(s)}
                className="rounded-full border bg-card px-3 py-1.5 text-xs font-medium text-foreground/80 transition hover:border-primary/40 hover:bg-secondary hover:text-primary disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-[0_8px_30px_-20px_rgba(15,27,45,0.4)] focus-within:border-primary/50">
            <Textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  send(text)
                }
              }}
              placeholder="Pergunte sobre os resultados…"
              rows={1}
              className="max-h-40 min-h-10 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0"
            />
            <Button size="icon-lg" className="rounded-xl" onClick={() => send(text)} disabled={!text.trim() || thinking} aria-label="Enviar">
              <ArrowUp className="size-5" />
            </Button>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>A IA só usa os resultados calculados e não confirma mineralização.</span>
            <Badge variant={aiMode ? "default" : "secondary"}>{aiMode ? "IA ligada (Cloudflare)" : "Modo offline"}</Badge>
          </div>
        </div>
      </div>
    </div>
  )
}
