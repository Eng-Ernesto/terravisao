"""python -m geoexplora.web [--port 8501] [--host 0.0.0.0]"""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    p = argparse.ArgumentParser(prog="geoexplora.web")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8501)
    args = p.parse_args()
    uvicorn.run("geoexplora.web.api:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
