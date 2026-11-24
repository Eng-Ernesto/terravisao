import type { LucideIcon } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"

export type GuideStep = { icon: LucideIcon; title: string; text: string }

/** Guia de entrada num sistema: passos curtos, com Saltar. Fechar ou saltar conta como visto. */
export function Guide({ open, steps, onClose }: { open: boolean; steps: GuideStep[]; onClose: () => void }) {
  const [i, setI] = useState(0)
  const last = i === steps.length - 1
  const close = () => {
    setI(0)
    onClose()
  }
  const step = steps[i]

  return (
    <Dialog open={open} onOpenChange={(o) => !o && close()}>
      <DialogContent className="max-w-md gap-0 p-0 sm:max-w-md" showCloseButton={false}>
        <div className="rounded-t-xl bg-[linear-gradient(135deg,#1A5BD7,#5B8DEF)] px-6 pt-6 pb-8 text-white">
          <div className="flex items-center justify-between text-xs font-medium text-white/80">
            <span>
              Passo {i + 1} de {steps.length}
            </span>
            <button type="button" onClick={close} className="rounded-md px-2 py-1 hover:bg-white/15">
              Saltar
            </button>
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={{ duration: 0.2 }}
              className="mt-6"
            >
              <div className="flex size-12 items-center justify-center rounded-2xl bg-white/20">
                <step.icon className="size-6" />
              </div>
              <DialogTitle className="mt-4 text-xl font-semibold text-white">{step.title}</DialogTitle>
            </motion.div>
          </AnimatePresence>
        </div>
        <div className="px-6 pt-5 pb-6">
          <DialogDescription className="min-h-16 text-[15px] leading-relaxed text-muted-foreground">
            {step.text}
          </DialogDescription>
          <div className="mt-6 flex items-center justify-between">
            <div className="flex gap-1.5">
              {steps.map((s, k) => (
                <span
                  key={s.title}
                  className={cn("h-1.5 rounded-full transition-all", k === i ? "w-6 bg-primary" : "w-1.5 bg-border")}
                />
              ))}
            </div>
            <div className="flex gap-2">
              {i > 0 && (
                <Button variant="ghost" onClick={() => setI(i - 1)}>
                  Anterior
                </Button>
              )}
              <Button onClick={() => (last ? close() : setI(i + 1))}>{last ? "Começar" : "Seguinte"}</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
