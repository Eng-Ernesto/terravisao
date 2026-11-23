"""Linha de comandos. Por agora só valida um terreno; o pipeline completo vem na fase 1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .aoi import AoiError, area_km2, validate_aoi


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="terravisao", description="TerraVisão")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check-aoi", help="Valida um terreno em GeoJSON")
    check.add_argument("geojson", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "check-aoi":
        data = json.loads(args.geojson.read_text(encoding="utf-8"))
        geometry = data.get("geometry", data) if data.get("type") == "Feature" else data
        try:
            geom = validate_aoi(geometry)
        except AoiError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            return 1
        print(f"Terreno válido: {area_km2(geom):,.1f} km²")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
