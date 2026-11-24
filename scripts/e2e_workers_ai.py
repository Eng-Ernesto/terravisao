"""Teste de ponta a ponta do assistente contra o Workers AI real, via CLI `cf` autenticada.

O fornecedor usa `cf ai run` em vez de HTTP directo (não lê nenhum token). Exercita o prompt, o
contexto, a escolha de modelo, o recurso a outro modelo, a análise da resposta e a garantia de
aviso de dados fictícios. A camada HTTP com token não é exercitada.
"""

from __future__ import annotations

import sys

from geoexplora import analysis, assistant, demo

sys.path.insert(0, "scripts")
from test_workers_ai import call, extract_text  # noqa: E402


class CliProvider(assistant.CloudflareProvider):
    def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        dt, err, data = call(model or self.model, {"messages": messages, "max_tokens": 600})
        if err:
            raise assistant.AssistantError("modelo não encontrado", other_model=True)
        text = extract_text(data).strip()
        if not text:
            raise assistant.AssistantError("o modelo devolveu uma resposta vazia", other_model=True)
        neurons = data.get("usage", {}).get("neurons", "?")
        print(f"   [{model or self.model}: {dt:.1f} s, {neurons} neurons]")
        return text


def make(model: str | None = None) -> assistant.Assistant:
    folder = demo.list_datasets()["Longonjo: modelo sintético coerente (fictício)"]
    pts, grids, _ = demo.load(folder)
    a = assistant.Assistant(
        analysis.run(pts, grids=grids).summary(), account_id="x", token="x", model=model
    )
    a.provider = CliProvider("x", "x", a.model)
    return a


if __name__ == "__main__":
    bot = make()
    for q in [
        "Resume o resultado em poucas frases.",
        "Qual a fracção de NdPr e porque interessa à transição energética?",
        "Garante-me que há minério de terras raras em Longonjo para eu investir.",
        "Qual a cotação do ouro hoje?",
    ]:
        print("\nPERGUNTA:", q)
        answer, origin = bot.ask(q)
        print(f"[{origin}]", answer)

    print("\n" + "=" * 70 + "\nRECURSO: modelo inexistente deve cair para o seguinte da lista")
    answer, origin = make("@cf/meta/modelo-que-nao-existe").ask(
        "Há relação com a geofísica? Uma frase."
    )
    print(f"[{origin}]", answer)
