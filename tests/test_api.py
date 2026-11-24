from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from geoexplora.web.api import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


@pytest.fixture(scope="module")
def coherent():
    r = client.post("/api/analyses", data={"dataset": "longonjo_modelo"})
    assert r.status_code == 200, r.text
    return r.json()


def test_health_and_datasets():
    assert client.get("/api/health").json()["ok"] is True
    ids = {d["id"] for d in client.get("/api/datasets").json()}
    assert {"longonjo_equipa", "longonjo_modelo"} <= ids


def test_analysis_payload_shape(coherent):
    a = coherent
    assert a["fictitious"] is True and a["metric_label"].startswith("TREO")
    assert len(a["points"]["features"]) == 500
    assert {f["properties"]["classe"] for f in a["points"]["features"]} == {
        "baixa",
        "moderada",
        "elevada",
    }
    assert any(z["significant"] for z in a["zones"])
    assert a["surface"]["png"].startswith("data:image/png;base64,")
    assert a["satellite"] is not None  # base de satélite do TerraVisão cobre Longonjo
    assert a["grids"] == ["Magnética (nT)"]
    assert "Analisei 500 amostras" in a["intro"]


def test_grid_and_derivative(coherent):
    r = client.get(
        f"/api/analyses/{coherent['id']}/grid",
        params={"name": "Magnética (nT)", "derivative": "sinal_analitico"},
    )
    assert r.status_code == 200 and r.json()["png"].startswith("data:image/png")
    assert (
        client.get(f"/api/analyses/{coherent['id']}/grid", params={"name": "x"}).status_code == 404
    )


def test_chat_offline_and_exports(coherent, monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    r = client.post(
        f"/api/analyses/{coherent['id']}/chat", json={"question": "Onde estão as zonas?"}
    )
    assert (
        r.status_code == 200 and r.json()["origin"] == "offline" and "Zona A" in r.json()["answer"]
    )
    pdf = client.get(f"/api/analyses/{coherent['id']}/report.pdf")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    csv = client.get(f"/api/analyses/{coherent['id']}/samples.csv")
    assert csv.status_code == 200 and b"classe" in csv.content.splitlines()[0]


def test_upload_csv_and_readable_error():
    csv = (ROOT / "data/geoexplora/demo/longonjo_modelo/amostras.csv").read_bytes()
    r = client.post(
        "/api/analyses", files={"points": ("meu.csv", csv, "text/csv")}, data={"epsg": "32733"}
    )
    assert r.status_code == 200 and r.json()["title"] == "meu"
    bad = client.post("/api/analyses", files={"points": ("x.csv", b"a,b\n1,2\n", "text/csv")})
    assert bad.status_code == 422 and "coordenadas" in bad.json()["detail"]
    assert client.post("/api/analyses").status_code == 422
    assert client.get("/api/analyses/naoexiste").status_code == 404


def test_terravisao_results_layers_and_exports():
    results = client.get("/api/terravisao/results").json()
    rid = next(r["id"] for r in results if r["id"] == "demo:longonjo")
    detail = client.get(f"/api/terravisao/results/{rid}").json()
    assert detail["title"] == "Longonjo" and "ferro" in detail["summary"]["targets"]
    assert {"classe", "satelite"} <= set(detail["layers"])
    layer = client.get(f"/api/terravisao/results/{rid}/layer", params={"layer": "classe"})
    assert layer.status_code == 200 and len(layer.json()["bounds"]) == 2
    assert client.get(f"/api/terravisao/results/{rid}/report.pdf").content.startswith(b"%PDF")
    assert client.get(f"/api/terravisao/results/{rid}/data.zip").content[:2] == b"PK"
    assert client.get("/api/terravisao/results/demo:..%2Fsecret").status_code == 404


def test_terravisao_validate_and_job_rejects_bad_geometry():
    square = {
        "type": "Polygon",
        "coordinates": [
            [[15.25, -12.95], [15.3, -12.95], [15.3, -12.9], [15.25, -12.9], [15.25, -12.95]]
        ],
    }
    ok = client.post("/api/terravisao/validate", json={"geometry": square}).json()
    assert ok["ok"] and 20 < ok["area_km2"] < 40
    out = {"type": "Polygon", "coordinates": [[[30, 10], [30.1, 10], [30.1, 10.1], [30, 10]]]}
    bad = client.post("/api/terravisao/validate", json={"geometry": out}).json()
    assert not bad["ok"] and "Angola" in bad["error"]
    assert client.post("/api/terravisao/jobs", json={"geometry": out}).status_code == 422


def test_provinces_reference():
    r = client.get("/api/reference/provinces")
    assert r.status_code == 200 and len(r.json()["features"]) >= 18
