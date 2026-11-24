import { KeyRound, ShieldCheck, Sparkles } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import type { AiCreds } from "@/lib/api"
import { aiCreds } from "@/lib/storage"

/** Definições da IA: conta Cloudflare Workers AI do utilizador, guardada só nesta sessão. */
export function AiSettings({
  open,
  onOpenChange,
  onSaved,
}: {
  open: boolean
  onOpenChange: (o: boolean) => void
  onSaved: (c: AiCreds | null) => void
}) {
  const current = aiCreds.get()
  const [accountId, setAccountId] = useState(current?.accountId ?? "")
  const [token, setToken] = useState(current?.token ?? "")

  const save = (c: AiCreds | null) => {
    aiCreds.set(c)
    onSaved(c)
    onOpenChange(false)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[420px] sm:max-w-md">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="size-5 text-primary" /> Assistente de IA
          </SheetTitle>
          <SheetDescription>
            Sem conta, o assistente responde em modo automático (offline). Com a sua conta gratuita do Cloudflare
            Workers AI, responde em linguagem livre.
          </SheetDescription>
        </SheetHeader>
        <div className="flex flex-col gap-4 px-4">
          <div className="grid gap-2">
            <Label htmlFor="cf-account">Account ID</Label>
            <Input id="cf-account" value={accountId} onChange={(e) => setAccountId(e.target.value)} autoComplete="off" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="cf-token">Token da API (permissão Workers AI)</Label>
            <Input
              id="cf-token"
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              autoComplete="off"
            />
          </div>
          <div className="flex gap-3 rounded-xl bg-muted p-3 text-xs leading-relaxed text-muted-foreground">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
            <span>
              Guardado só nesta sessão do navegador. Em cada pergunta, o resumo dos resultados (não os seus ficheiros)
              é enviado à Cloudflare para gerar a resposta.
            </span>
          </div>
          <div className="flex gap-2">
            <Button className="flex-1" onClick={() => save({ accountId: accountId.trim(), token: token.trim() })} disabled={!accountId || !token}>
              <KeyRound className="size-4" /> Guardar
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setAccountId("")
                setToken("")
                save(null)
              }}
            >
              Usar modo offline
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  )
}
