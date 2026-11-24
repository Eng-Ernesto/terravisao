// Preferências locais. As credenciais da IA ficam só na sessão do navegador (sessionStorage):
// desaparecem ao fechar o separador e nunca vão para o servidor fora de uma pergunta.
import type { AiCreds } from "./api"

const GUIDE_KEY = (system: string) => `geoexplora.guia.${system}`

export const guide = {
  seen: (system: string) => localStorage.getItem(GUIDE_KEY(system)) === "1",
  markSeen: (system: string) => localStorage.setItem(GUIDE_KEY(system), "1"),
}

const AI_KEY = "geoexplora.ia"

export const aiCreds = {
  get(): AiCreds | null {
    try {
      const raw = sessionStorage.getItem(AI_KEY)
      return raw ? (JSON.parse(raw) as AiCreds) : null
    } catch {
      return null
    }
  },
  set(c: AiCreds | null) {
    if (c && c.accountId && c.token) sessionStorage.setItem(AI_KEY, JSON.stringify(c))
    else sessionStorage.removeItem(AI_KEY)
  },
}
