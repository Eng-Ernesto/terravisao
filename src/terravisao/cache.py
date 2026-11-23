"""Cache em disco por chave (docs/04 §6). Guarda arrays .npz e metadados JSON."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

CACHE_VERSION = "1"


def cache_dir() -> Path:
    path = Path(os.environ.get("TERRAVISAO_CACHE_DIR", "data/cache"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def make_key(source: str, **params: Any) -> str:
    payload = json.dumps(
        {"v": CACHE_VERSION, "source": source, **params}, sort_keys=True, default=str
    )
    return f"{source}-{hashlib.sha256(payload.encode()).hexdigest()[:16]}"


def load(key: str) -> tuple[dict[str, np.ndarray], dict[str, Any]] | None:
    base = cache_dir() / key
    npz, meta = base.with_suffix(".npz"), base.with_suffix(".json")
    if not (npz.exists() and meta.exists()):
        return None
    with np.load(npz) as data:
        arrays = {k: data[k] for k in data.files}
    return arrays, json.loads(meta.read_text(encoding="utf-8"))


def save(key: str, arrays: dict[str, np.ndarray], meta: dict[str, Any]) -> None:
    base = cache_dir() / key
    np.savez_compressed(str(base.with_suffix(".npz")), **arrays)  # type: ignore[arg-type]
    base.with_suffix(".json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")


def clear() -> int:
    n = 0
    for p in cache_dir().glob("*"):
        if p.suffix in {".npz", ".json"}:
            p.unlink()
            n += 1
    return n
