"""API do GeoExplora IA (FastAPI). Expõe os pacotes `geoexplora` e `terravisao` ao frontend.

Executar:  python -m geoexplora.web   (ou: uvicorn geoexplora.web.api:app)
"""

from __future__ import annotations

import io
import json
import re
import tempfile
import threading
import uuid
import zipfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .. import __version__, demo, geophysics
from ..analysis import CLASS_LABEL, Analysis, Params
from ..analysis import run as run_analysis
from ..assistant import Assistant, brief
from ..loaders import LoadError, read_grid, read_points
from . import overlays

app = FastAPI(title="GeoExplora IA", version=__version__)

MAX_ANALYSES = 20
_analyses: OrderedDict[str, Analysis] = OrderedDict()
_lock = threading.Lock()
DERIVATIVES = {
    "valor": None,
    "sinal_analitico": geophysics.analytic_signal,
    "derivada_vertical": geophysics.vertical_derivative,
    "gradiente_horizontal": geophysics.horizontal_gradient,
}


def _store(a: Analysis) -> str:
    aid = uuid.uuid4().hex[:12]
    with _lock:
        _analyses[aid] = a
        while len(_analyses) > MAX_ANALYSES:
            _analyses.popitem(last=False)
    return aid


def _get(aid: str) -> Analysis:
    a = _analyses.get(aid)
    if a is None:
        raise HTTPException(404, "Análise não encontrada (o servidor pode ter sido reiniciado).")
    return a


# --------------------------------------------------------------------------------- geral
@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "version": __version__}


@app.get("/api/reference/provinces")
def provinces() -> Response:
    path = overlays.reference_dir() / "angola_provincias.geojson"
    if not path.exists():
        raise HTTPException(404, "Ficheiro de províncias em falta.")
    return Response(path.read_bytes(), media_type="application/geo+json")


# ----------------------------------------------------------------------- análise de mapa
@app.get("/api/datasets")
def datasets() -> list[dict[str, Any]]:
    out = []
    for title, folder in demo.list_datasets().items():
        meta = json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        out.append(
            {
                "id": folder.name,
                "title": title,
                "fictitious": bool(meta.get("fictitious", True)),
                "note": meta.get("note", ""),
                "grids": list(meta.get("grids", {})),
            }
        )
    return out


def _payload(aid: str, a: Analysis) -> dict[str, Any]:
    df = a.points.df
    s = a.summary()
    points = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(r.lon), float(r.lat)]},
                "properties": {
                    "id": str(r.id),
                    "valor": round(float(r.metrica_ppm), 1),
                    "classe": str(r.classe),
                    "ndpr": (round(float(r.ndpr_share), 3) if "ndpr_share" in df.columns else None),
                },
            }
            for r in df.itertuples()
        ],
    }
    sf = a.surface
    rows, cols = sf.array.shape
    surface = {
        "png": overlays.array_png(sf.array, "YlOrBr", 0.85),
        "bounds": overlays.lonlat_bounds(
            sf.x0, sf.y1 - rows * sf.dx, sf.x0 + cols * sf.dx, sf.y1, sf.epsg
        ),
    }
    sat = overlays.satellite_for(df["lon"].to_numpy(), df["lat"].to_numpy())
    return {
        "id": aid,
        "title": a.points.title or "Análise",
        "fictitious": a.points.fictitious,
        "metric_label": a.treo_label,
        "summary": s,
        "intro": brief(s),
        "class_labels": CLASS_LABEL,
        "points": points,
        "zones": [
            {
                "id": z.id,
                "n_samples": z.n_samples,
                "area_km2": round(z.area_km2, 3),
                "mean": round(z.mean_value_ppm, 1),
                "max": round(z.max_value_ppm, 1),
                "ndpr": None if z.ndpr_share is None else round(z.ndpr_share, 3),
                "significant": z.significant,
                "centroid": list(z.centroid_lonlat),
                "polygon": z.polygon,
            }
            for z in a.zones
        ],
        "surface": surface,
        "satellite": overlays.raster_overlay(sat, "layer_rgb", "rgb", 1.0) if sat else None,
        "grids": list(a.grids),
        "derivatives": list(DERIVATIVES),
        "bounds": [
            [float(df["lat"].min()), float(df["lon"].min())],
            [float(df["lat"].max()), float(df["lon"].max())],
        ],
        "warnings": list(dict.fromkeys(a.warnings)),
        "stats": _stats(a),
    }


def _stats(a: Analysis) -> list[dict[str, Any]]:
    """Estatística descritiva por variável (elementos, métrica e covariáveis)."""
    df = a.points.df
    cols = [(f"{e}_ppm", f"{e} (ppm)") for e in a.points.elements]
    cols += [("metrica_ppm", a.treo_label)]
    if "ndpr_share" in df.columns:
        cols += [("ndpr_share", "NdPr/TREO")]
    cols += [
        (c, c.replace("grelha:", "") + " (grelha)" if c.startswith("grelha:") else c)
        for c in a.points.covariates
    ]
    out = []
    for col, label in cols:
        if col not in df.columns:
            continue
        v = df[col].dropna()
        if v.empty:
            continue
        out.append(
            {
                "variavel": label,
                "n": int(v.size),
                "min": round(float(v.min()), 3),
                "mediana": round(float(v.median()), 3),
                "media": round(float(v.mean()), 3),
                "max": round(float(v.max()), 3),
                "desvio": round(float(v.std()), 3),
            }
        )
    return out


@app.post("/api/analyses")
async def create_analysis(
    dataset: str | None = Form(None),
    points: UploadFile | None = File(None),
    grids: list[UploadFile] | None = File(None),
    epsg: int | None = Form(None),
    method: str = Form("quantis"),
    q_moderada: float = Form(0.50),
    q_elevada: float = Form(0.85),
) -> dict[str, Any]:
    """Analisa um exemplo (`dataset`) ou ficheiros carregados (`points`, `grids`)."""
    if method not in ("quantis", "estatistico"):
        raise HTTPException(422, "Método desconhecido.")
    params = Params(method=method, q_moderada=q_moderada, q_elevada=q_elevada)
    try:
        if dataset:
            folders = {f.name: f for f in demo.list_datasets().values()}
            if dataset not in folders:
                raise HTTPException(404, "Conjunto de demonstração desconhecido.")
            pts, grid_layers, _ = demo.load(folders[dataset])
        elif points is not None:
            pts = read_points(await points.read(), points.filename or "dados.csv", epsg=epsg)
            pts.title = Path(points.filename or "dados").stem
            grid_layers = {}
            for g in grids or []:
                name = Path(g.filename or "grelha").stem
                grid_layers[name] = read_grid(await g.read(), name)
        else:
            raise HTTPException(422, "Escolha um exemplo ou carregue um ficheiro de amostras.")
        a = run_analysis(pts, params, grid_layers)
    except (LoadError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    aid = _store(a)
    return _payload(aid, a)


@app.get("/api/analyses/{aid}")
def get_analysis(aid: str) -> dict[str, Any]:
    return _payload(aid, _get(aid))


@app.get("/api/analyses/{aid}/grid")
def analysis_grid(aid: str, name: str, derivative: str = "valor") -> dict[str, Any]:
    a = _get(aid)
    if name not in a.grids or derivative not in DERIVATIVES:
        raise HTTPException(404, "Grelha ou derivada desconhecida.")
    g = a.grids[name]
    arr = g.array
    fn = DERIVATIVES[derivative]
    if fn is not None:
        arr = fn(arr, g.resolution)
    lo, hi = np.nanpercentile(arr, [2, 98])
    cmap = "RdBu_r" if lo < 0 < hi else "viridis"
    x0, y0, x1, y1 = g.bounds()
    return {
        "png": overlays.array_png(arr, cmap, 0.8),
        "bounds": overlays.lonlat_bounds(x0, y0, x1, y1, g.epsg),
        "min": float(lo),
        "max": float(hi),
    }


class ChatIn(BaseModel):
    question: str = Field(..., max_length=2000)
    history: list[dict[str, str]] = Field(default_factory=list)
    account_id: str | None = None
    token: str | None = None


@app.post("/api/analyses/{aid}/chat")
def chat(aid: str, body: ChatIn) -> dict[str, str]:
    a = _get(aid)
    bot = Assistant(a.summary(), account_id=body.account_id or None, token=body.token or None)
    history = [
        {"role": m.get("role", ""), "content": m.get("content", "")}
        for m in body.history
        if m.get("role") in ("user", "assistant")
    ]
    answer, origin = bot.ask(body.question, history)
    return {"answer": answer, "origin": origin}


@app.get("/api/analyses/{aid}/report.pdf")
def analysis_report(aid: str) -> Response:
    from ..report import generate_analysis_report

    a = _get(aid)
    with tempfile.TemporaryDirectory() as tmp:
        data = generate_analysis_report(a, Path(tmp) / "r.pdf").read_bytes()
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="geoexplora_relatorio.pdf"'},
    )


@app.get("/api/analyses/{aid}/samples.csv")
def analysis_csv(aid: str) -> Response:
    df = _get(aid).points.df.drop(columns=["x", "y"])
    return Response(
        df.to_csv(index=False).encode("utf-8"),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="amostras_classificadas.csv"'},
    )


# ------------------------------------------------------------------------------ TerraVisão
TV_LAYERS = {
    "classe": ("class", "class_{t}"),
    "pontuacao": ("score", "score_{t}"),
    "oxido": ("index", "layer_iron_oxide"),
    "argila": ("index", "layer_clay"),
    "relevo": ("relief", "layer_hillshade"),
    "satelite": ("rgb", "layer_rgb"),
}


def _folder(rid: str) -> Path:
    try:
        return overlays.result_folder(rid)
    except KeyError as exc:
        raise HTTPException(404, "Resultado não encontrado.") from exc


@app.get("/api/terravisao/results")
def tv_results() -> list[dict[str, Any]]:
    return overlays.list_results()


@app.get("/api/terravisao/results/{rid}")
def tv_result(rid: str) -> dict[str, Any]:
    folder = _folder(rid)
    run = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    meta = (
        json.loads((folder / "meta.json").read_text(encoding="utf-8"))
        if (folder / "meta.json").exists()
        else {}
    )
    zones = {}
    for t in run["summary"]["targets"]:
        zf = folder / f"zones_{t}.geojson"
        zones[t] = json.loads(zf.read_text(encoding="utf-8")) if zf.exists() else None
    layers = [
        k for k, (_, pat) in TV_LAYERS.items() if any(folder.glob(pat.format(t="*") + ".tif"))
    ]
    return {
        "id": rid,
        "title": meta.get("title", folder.name),
        "region": meta.get("region", ""),
        "geometry": run["request"]["geometry"],
        "summary": run["summary"],
        "zones": zones,
        "layers": layers,
        "created_at": run.get("provenance", {}).get("created_at"),
    }


@app.get("/api/terravisao/results/{rid}/layer")
def tv_layer(
    rid: str, layer: str, target: str = "terras_raras", opacity: float = 0.8
) -> dict[str, Any]:
    folder = _folder(rid)
    if layer not in TV_LAYERS or not re.fullmatch(r"[a-z_]+", target):
        raise HTTPException(404, "Camada desconhecida.")
    kind, pattern = TV_LAYERS[layer]
    name = pattern.format(t=target)
    if not (folder / f"{name}.tif").exists():
        raise HTTPException(404, "Camada indisponível para este resultado.")
    return overlays.raster_overlay(folder, name, kind, max(0.1, min(opacity, 1.0)))


@app.get("/api/terravisao/results/{rid}/report.pdf")
def tv_report(rid: str) -> Response:
    from terravisao.report import generate_report

    folder = _folder(rid)
    with tempfile.TemporaryDirectory() as tmp:
        data = generate_report(folder, Path(tmp) / "r.pdf").read_bytes()
    return Response(
        data,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="terravisao_relatorio.pdf"'},
    )


@app.get("/api/terravisao/results/{rid}/data.zip")
def tv_zip(rid: str) -> Response:
    folder = _folder(rid)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(folder.iterdir()):
            if f.suffix in {".tif", ".geojson", ".json"}:
                zf.write(f, f.name)
    return Response(
        buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="terravisao_dados.zip"'},
    )


class GeometryIn(BaseModel):
    geometry: dict[str, Any]


@app.post("/api/terravisao/validate")
def tv_validate(body: GeometryIn) -> dict[str, Any]:
    from terravisao.aoi import AoiError, area_km2, validate_aoi

    try:
        geom = validate_aoi(body.geometry)
    except AoiError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "area_km2": round(area_km2(geom), 2)}


class JobIn(BaseModel):
    geometry: dict[str, Any]
    targets: list[str] = Field(
        default_factory=lambda: ["terras_raras", "cobre", "litio", "manganes"]
    )
    name: str = "Meu terreno"


_jobs: dict[str, dict[str, Any]] = {}


def _run_job(jid: str, body: JobIn) -> None:
    from terravisao.config import Target
    from terravisao.export import export_all
    from terravisao.models import AnalysisRequest
    from terravisao.pipeline import run as run_pipeline

    job = _jobs[jid]

    def progress(msg: str, frac: float) -> None:
        job.update(message=msg, progress=round(frac, 3))

    try:
        req = AnalysisRequest(
            geometry=body.geometry,
            targets=[Target(t) for t in body.targets],
            name=body.name.strip() or "terreno",
        )
        result = run_pipeline(req, progress=progress)
        if not result.targets:
            raise RuntimeError("Sem dados para este terreno. " + " ".join(result.warnings))
        stamp = datetime.now()
        name = req.name or "terreno"
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "terreno"
        folder = overlays.runs_dir() / f"{slug}-{stamp:%Y%m%d-%H%M%S}"
        export_all(result, folder)
        (folder / "meta.json").write_text(
            json.dumps(
                {"title": f"{name} · {stamp:%d/%m %H:%M}", "region": "Análise nova"},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        job.update(status="done", progress=1.0, message="Concluído", result_id=f"run:{folder.name}")
    except Exception as exc:  # o erro é mostrado ao utilizador
        job.update(status="error", error=str(exc))


@app.post("/api/terravisao/jobs")
def tv_job(body: JobIn) -> dict[str, Any]:
    from terravisao.aoi import AoiError, validate_aoi
    from terravisao.config import Target

    try:
        validate_aoi(body.geometry)
        [Target(t) for t in body.targets]
    except (AoiError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    if not body.targets:
        raise HTTPException(422, "Escolha pelo menos um alvo.")
    jid = uuid.uuid4().hex[:12]
    _jobs[jid] = {"id": jid, "status": "running", "progress": 0.0, "message": "A preparar…"}
    threading.Thread(target=_run_job, args=(jid, body), daemon=True).start()
    return _jobs[jid]


@app.get("/api/terravisao/jobs/{jid}")
def tv_job_status(jid: str) -> dict[str, Any]:
    if jid not in _jobs:
        raise HTTPException(404, "Tarefa não encontrada.")
    return _jobs[jid]


@app.get("/api/online")
def online() -> dict[str, bool]:
    """Há internet? (as análises novas de satélite e a IA em linguagem livre precisam)."""
    import socket

    try:
        socket.create_connection(("api.cloudflare.com", 443), timeout=1.5).close()
        return {"online": True}
    except OSError:
        return {"online": False}


# ------------------------------------------------------------------------------ frontend
def _dist() -> Path:
    return overlays.root() / "frontend" / "dist"


if (_dist() / "assets").exists():
    app.mount("/assets", StaticFiles(directory=_dist() / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def spa(path: str) -> Response:
    """Serve o frontend compilado (aplicação de página única)."""
    if path.startswith("api/"):
        return JSONResponse({"detail": "Não encontrado."}, status_code=404)
    dist = _dist()
    candidate = (dist / path).resolve()
    if path and candidate.is_file() and dist.resolve() in candidate.parents:
        return FileResponse(candidate)
    index = dist / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"detail": "Frontend não compilado. Corra `npm run build` em frontend/."}, status_code=503
    )
