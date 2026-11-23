"""Linha de comandos: `terravisao check-aoi` e `terravisao run`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__, cache
from .aoi import AoiError, area_km2, validate_aoi
from .config import Target


def _read_geometry(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("type") == "FeatureCollection":
        data = data["features"][0]
    return dict(data.get("geometry", data)) if data.get("type") == "Feature" else dict(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="terravisao", description="TerraVisão")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    check = sub.add_parser("check-aoi", help="Valida um terreno em GeoJSON")
    check.add_argument("geojson", type=Path)

    run = sub.add_parser("run", help="Analisa um terreno e grava mapas e zonas")
    run.add_argument("geojson", type=Path)
    run.add_argument("--targets", default="ferro,cobre,ouro,agua")
    run.add_argument("--out", type=Path, default=Path("output"))

    sub.add_parser("cache-clear", help="Apaga a cache de descargas")
    args = parser.parse_args(argv)

    if args.cmd == "cache-clear":
        print(f"{cache.clear()} ficheiros apagados")
        return 0

    geometry = _read_geometry(args.geojson)
    try:
        geom = validate_aoi(geometry)
    except AoiError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if args.cmd == "check-aoi":
        print(f"Terreno válido: {area_km2(geom):,.1f} km²")
        return 0

    # Importação tardia: o pipeline precisa dos extras geoespaciais.
    from .export import export_all
    from .models import AnalysisRequest
    from .pipeline import run as run_pipeline
    from .pipeline import summary

    targets = [Target(t.strip()) for t in args.targets.split(",") if t.strip()]
    request = AnalysisRequest(geometry=geometry, targets=targets, name=args.geojson.stem)
    result = run_pipeline(request, progress=lambda m, f: print(f"[{f:4.0%}] {m}", flush=True))
    files = export_all(result, args.out)
    print(json.dumps(summary(result), ensure_ascii=False, indent=2))
    print(f"{len(files)} ficheiros em {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
