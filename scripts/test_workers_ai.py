"""Testa modelos do Workers AI com o pedido real do assistente, usando a CLI `cf` já autenticada.

Não lê nem copia nenhum token: a CLI usa a sessão do utilizador.
Uso: python scripts/test_workers_ai.py <modelo> [<modelo> ...]
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from geoexplora import analysis, assistant, demo

QUESTION = "Há relação entre a geofísica e o teor de terras raras? Responde em 4 frases."


def build_body() -> dict:
    folder = demo.list_datasets()["Longonjo: modelo sintético coerente (fictício)"]
    pts, grids, _ = demo.load(folder)
    summary = analysis.run(pts, grids=grids).summary()
    context = "DADOS (JSON):\n" + json.dumps(summary, ensure_ascii=False)
    return {
        "messages": [
            {"role": "system", "content": assistant.SYSTEM_PROMPT + "\n\n" + context},
            {"role": "user", "content": QUESTION},
        ],
        "max_tokens": 500,
    }


def call(model: str, body: dict) -> tuple[float, str, dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(body, fh, ensure_ascii=False)
        path = fh.name
    t0 = time.time()
    proc = subprocess.run(
        [shutil.which("cf") or "cf", "ai", "run", model, "--body", f"@{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    dt = time.time() - t0
    Path(path).unlink(missing_ok=True)
    if proc.returncode != 0:
        return dt, "ERRO: " + (proc.stderr or proc.stdout).strip()[:300], {}
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        return dt, "SAÍDA NÃO JSON: " + proc.stdout[:300], {}
    return dt, "", data


def extract_text(data: dict) -> str:
    r = data.get("result", data)
    if isinstance(r, dict):
        if "response" in r and r["response"]:
            return str(r["response"])
        ch = r.get("choices")
        if ch:
            return str(ch[0].get("message", {}).get("content") or ch[0].get("text") or "")
    ch = data.get("choices")
    if ch:
        return str(ch[0].get("message", {}).get("content") or "")
    return ""


if __name__ == "__main__":
    body = build_body()
    print("tamanho do pedido:", len(json.dumps(body, ensure_ascii=False)), "caracteres\n")
    for model in sys.argv[1:]:
        dt, err, data = call(model, body)
        print("=" * 70, f"\n{model}  ({dt:.1f} s)")
        if err:
            print(err)
            continue
        usage = (data.get("result", data) or {}).get("usage") or data.get("usage")
        print("uso:", usage)
        print(
            extract_text(data).strip() or ("(vazio) " + json.dumps(data, ensure_ascii=False)[:400])
        )
