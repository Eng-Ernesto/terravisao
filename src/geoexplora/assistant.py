"""Assistente de interpretação (docs/14 §5).

Regras:
- só vê o resumo estruturado da análise (`Analysis.summary()`), nunca os ficheiros do utilizador;
- não calcula nem inventa: cita valores do resumo;
- é opcional: sem token, sem internet ou com erro, responde em modo offline e nunca levanta excepção.

Fornecedor de linguagem: Cloudflare Workers AI (endpoint compatível com OpenAI), com o token
da conta do próprio utilizador.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_MODEL = "@cf/meta/llama-3.1-8b-instruct"
ENDPOINT = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"
TIMEOUT_S = 30
MAX_TURNS = 6

SYSTEM_PROMPT = """És o assistente do GeoExplora IA, uma plataforma de apoio à exploração de minerais \
críticos (terras raras) em Angola. Falas português de Angola, de forma simples e directa.

REGRAS:
1. Usa APENAS os dados do bloco DADOS. Nunca inventes números, zonas, locais ou conclusões.
2. Cita sempre os valores que usas (zona, ppm, área, correlação).
3. Isto é uma ferramenta de triagem. Nunca afirmes que existe minério; fala em probabilidade e em \
onde vale a pena confirmar no campo.
4. Se os dados forem fictícios (campo "ficticio": true), diz que são de demonstração.
5. Se o modelo não superar o acaso ou não houver relação significativa, di-lo claramente.
6. Se não souberes responder com os DADOS, diz que não tens essa informação.
7. Respostas curtas (até 8 frases)."""


class AssistantError(RuntimeError):
    """Falha do fornecedor de linguagem (mensagem mostrável ao utilizador)."""


def _fmt(x: float | None, nd: int = 1) -> str:
    return "n/d" if x is None else f"{x:,.{nd}f}".replace(",", " ").replace(".", ",")


# ------------------------------------------------------------------ interpretação automática
def interpretation(summary: dict[str, Any]) -> str:
    """Texto de interpretação gerado só a partir dos números (sem IA externa)."""
    c, t, cl = summary["conjunto"], summary["metrica_ppm"], summary["classificacao"]
    parts: list[str] = []
    if c["ficticio"]:
        parts.append("DADOS FICTÍCIOS: esta é uma demonstração.")
    parts.append(
        f"Foram analisadas {c['n_amostras']} amostras. A métrica é {c['metrica']}: mediana de "
        f"{_fmt(t['mediana'])} ppm, entre {_fmt(t['min'])} e {_fmt(t['max'])} ppm."
    )
    n = cl["contagem"]
    parts.append(
        f"Classificação ({cl['metodo']}): {n['elevada']} amostras elevadas "
        f"(≥ {_fmt(cl['limiares_ppm']['elevada'])} ppm), {n['moderada']} moderadas e "
        f"{n['baixa']} baixas. As classes são relativas a este conjunto, não são teores económicos."
    )
    zones = summary["zonas"]
    sig = [z for z in zones if z["significativa_vs_acaso"]]
    if sig:
        z = sig[0]
        parts.append(
            f"Há {len(sig)} zona(s) com concentração maior do que o acaso. A principal é a zona "
            f"{z['id']}: {z['n_amostras']} amostras elevadas em {_fmt(z['area_km2'])} km², com "
            f"{_fmt(z['valor_medio_ppm'], 0)} ppm de média e máximo de {_fmt(z['valor_max_ppm'], 0)} ppm."
        )
    elif zones:
        parts.append(
            f"Foram delimitados {len(zones)} grupos de amostras elevadas, mas nenhum é maior do que "
            "o esperado por acaso: não há concentração espacial real."
        )
    else:
        parts.append("Não foi delimitada nenhuma zona de interesse.")
    if c["metrica"].startswith("TREO") and summary["ndpr_sobre_treo"] is not None:
        extra = ""
        if sig and sig[0]["ndpr_sobre_treo"] is not None:
            extra = f" Na zona {sig[0]['id']} é {_fmt(sig[0]['ndpr_sobre_treo'] * 100)} %."
        parts.append(
            f"A fracção NdPr/TREO média é {_fmt(summary['ndpr_sobre_treo'] * 100)} %: é a parte "
            f"útil para ímanes permanentes (turbinas eólicas, motores eléctricos).{extra}"
        )
    rel = [r for r in summary["relacoes"] if r["leitura"] != "sem relação relevante"]
    if rel:
        r = rel[0]
        parts.append(
            f"A variável que mais se relaciona com o teor é «{r['variavel']}» (Spearman "
            f"{_fmt(r['rho_spearman'], 2)}, relação {r['leitura']})."
        )
    elif summary["relacoes"]:
        parts.append("Nenhuma das variáveis geofísicas se relaciona de forma relevante com o teor.")
    m = summary["modelo"]
    if m.get("executado"):
        parts.append(
            f"O modelo acerta {_fmt(m['exatidao'] * 100, 0)} % na classe (acaso: "
            f"{_fmt(m['acaso'] * 100, 0)} %). "
            + (
                "Supera o acaso: a geofísica ajuda a prever a geoquímica."
                if m["supera_acaso"]
                else "Não supera o acaso: com estes dados, a geofísica não prevê a geoquímica."
            )
        )
    parts.append(
        "Próximo passo: "
        + (
            "amostragem de detalhe (malha mais apertada) na zona principal e furos de verificação, "
            "depois de confirmar no campo."
            if sig
            else "recolher mais dados ou rever as coordenadas e as variáveis antes de decidir; "
            "confirmar sempre no campo."
        )
    )
    return "\n\n".join(parts)


def brief(summary: dict[str, Any]) -> str:
    """Mensagem de boas-vindas curta com o essencial (a análise completa vem com «Resume»)."""
    c, zones = summary["conjunto"], summary["zonas"]
    sig = [z for z in zones if z["significativa_vs_acaso"]]
    m = summary["modelo"]
    lines = [
        ("DADOS FICTÍCIOS (demonstração). " if c["ficticio"] else "")
        + f"Analisei {c['n_amostras']} amostras ({c['metrica']}).",
    ]
    if sig:
        z = sig[0]
        lines.append(
            f"Principal zona de interesse: **{z['id']}**, com {z['n_amostras']} amostras elevadas "
            f"em {_fmt(z['area_km2'])} km² (média {_fmt(z['valor_medio_ppm'], 0)} ppm)."
        )
    else:
        lines.append("Não há nenhuma zona maior do que o esperado por acaso.")
    if m.get("executado"):
        lines.append(
            "O modelo supera o acaso."
            if m["supera_acaso"]
            else "A geofísica não prevê a geoquímica com estes dados (o modelo não supera o acaso)."
        )
    lines.append("Pergunte o que quiser ou use as sugestões abaixo.")
    return "\n\n".join(lines)


# ----------------------------------------------------------------------- respostas offline
_INTENTS: list[tuple[tuple[str, ...], str]] = [
    (("zona", "zonas", "onde", "alvo", "alvos", "prioridade", "furo", "sondagem"), "zonas"),
    (
        (
            "correla",
            "relaç",
            "relac",
            "magnét",
            "magnet",
            "tório",
            "torio",
            "radiom",
            "geofís",
            "geofis",
        ),
        "relacoes",
    ),
    (("modelo", "random", "ia ", "previs", "acaso", "aprend", "machine"), "modelo"),
    (
        (
            "ndpr",
            "magnete",
            "íman",
            "iman",
            "turbina",
            "transição",
            "transicao",
            "neodímio",
            "praseod",
        ),
        "ndpr",
    ),
    (("limita", "confia", "fiável", "fiavel", "risco", "fictíc", "fictic", "real"), "limites"),
    (("próximo", "proximo", "recomend", "fazer", "seguinte", "sugest"), "proximo"),
]


def offline_answer(question: str, summary: dict[str, Any]) -> str:
    q = f" {question.lower()} "
    intent = next((name for keys, name in _INTENTS if any(k in q for k in keys)), "resumo")
    zones, sig = summary["zonas"], [z for z in summary["zonas"] if z["significativa_vs_acaso"]]
    m = summary["modelo"]
    if intent == "zonas":
        if not zones:
            return "Não foi delimitada nenhuma zona de interesse neste conjunto."
        rows = "\n".join(
            f"- Zona {z['id']}: {z['n_amostras']} amostras, {_fmt(z['area_km2'])} km², "
            f"média {_fmt(z['valor_medio_ppm'], 0)} ppm"
            + (
                " (maior do que o acaso)"
                if z["significativa_vs_acaso"]
                else " (compatível com o acaso)"
            )
            for z in zones[:6]
        )
        head = (
            f"{len(sig)} zona(s) com concentração real:"
            if sig
            else "Nenhuma zona é maior do que o acaso; estes são os grupos encontrados:"
        )
        return f"{head}\n{rows}"
    if intent == "relacoes":
        if not summary["relacoes"]:
            return "Não há variáveis geofísicas para relacionar com o teor."
        return "Relação com o teor (Spearman):\n" + "\n".join(
            f"- {r['variavel']}: {_fmt(r['rho_spearman'], 2)} ({r['leitura']}, n = {r['n']})"
            for r in summary["relacoes"]
        )
    if intent == "modelo":
        if not m.get("executado"):
            return f"O modelo não foi executado: {m.get('motivo', 'sem dados suficientes')}."
        imp = ", ".join(f"{k} ({_fmt(v, 3)})" for k, v in list(m["importancia"].items())[:3])
        return (
            f"{m['leitura']} Exatidão {_fmt(m['exatidao'] * 100, 0)} % contra {_fmt(m['acaso'] * 100, 0)} % "
            f"do acaso (p = {_fmt(m['p_valor_vs_acaso'], 3)}), validação por blocos espaciais. "
            f"Variáveis mais importantes: {imp}."
        )
    if intent == "ndpr":
        s = summary["ndpr_sobre_treo"]
        if s is None:
            return "Os dados não têm Nd e Pr, por isso não é possível calcular a fracção NdPr/TREO."
        return (
            f"NdPr/TREO médio: {_fmt(s * 100)} %. O Nd e o Pr são os elementos usados em ímanes "
            "permanentes de turbinas eólicas e motores eléctricos, por isso são centrais na "
            "transição energética."
        )
    if intent == "limites":
        fic = "Os dados são fictícios (demonstração). " if summary["conjunto"]["ficticio"] else ""
        return (
            fic
            + "As classes são relativas ao conjunto, não são teores económicos. "
            + "O TREO pode ser parcial se faltarem elementos. A análise indica onde confirmar no "
            "campo; não prova a existência de minério."
        )
    if intent == "proximo":
        return interpretation(summary).split("Próximo passo:")[-1].strip().capitalize()
    return interpretation(summary)


# ---------------------------------------------------------------------------- fornecedor
class CloudflareProvider:
    def __init__(self, account_id: str, token: str, model: str = DEFAULT_MODEL) -> None:
        self.account_id, self.token, self.model = account_id.strip(), token.strip(), model

    def chat(self, messages: list[dict[str, str]]) -> str:
        body = json.dumps({"model": self.model, "messages": messages, "max_tokens": 600}).encode()
        req = urllib.request.Request(
            ENDPOINT.format(account=self.account_id),
            data=body,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return str(data["choices"][0]["message"]["content"]).strip()
        except urllib.error.HTTPError as exc:
            hint = {
                401: "token inválido",
                403: "modelo não permitido neste plano",
                429: "quota esgotada",
            }
            raise AssistantError(hint.get(exc.code, f"erro {exc.code}")) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise AssistantError("sem ligação à internet") from exc
        except (KeyError, IndexError, ValueError) as exc:
            raise AssistantError("resposta inesperada do serviço") from exc


class Assistant:
    """Responde sobre uma análise. Usa a IA da Cloudflare se estiver configurada; senão, offline."""

    def __init__(
        self,
        summary: dict[str, Any],
        account_id: str | None = None,
        token: str | None = None,
        model: str | None = None,
    ) -> None:
        self.summary = summary
        account_id = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
        token = token or os.environ.get("CLOUDFLARE_API_TOKEN", "")
        self.provider = (
            CloudflareProvider(
                account_id, token, model or os.environ.get("GEOEXPLORA_AI_MODEL", DEFAULT_MODEL)
            )
            if account_id and token
            else None
        )

    @property
    def mode(self) -> str:
        return "ia" if self.provider else "offline"

    def ask(self, question: str, history: list[dict[str, str]] | None = None) -> tuple[str, str]:
        """Devolve (resposta, origem) com origem «ia» ou «offline». Nunca levanta excepção."""
        question = question.strip()
        if not question:
            return "Escreva uma pergunta sobre os resultados.", "offline"
        if self.provider is None:
            return offline_answer(question, self.summary), "offline"
        context = "DADOS (JSON):\n" + json.dumps(self.summary, ensure_ascii=False)
        messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context}]
        messages += (history or [])[-2 * MAX_TURNS :]
        messages.append({"role": "user", "content": question})
        try:
            return self.provider.chat(messages), "ia"
        except AssistantError as exc:
            note = f"(Assistente de IA indisponível: {exc}. Resposta automática.)\n\n"
            return note + offline_answer(question, self.summary), "offline"
        except Exception:
            return offline_answer(question, self.summary), "offline"
