from pathlib import Path

import pytest

from terravisao.cli import main

pytest.importorskip("reportlab")

DEMO = Path(__file__).resolve().parents[1] / "data" / "demo" / "longonjo"


def test_report_is_generated_from_demo(tmp_path):
    from terravisao.report import generate_report

    out = generate_report(DEMO, tmp_path / "r.pdf")
    data = out.read_bytes()
    assert data.startswith(b"%PDF")
    assert 50_000 < len(data) < 5_000_000  # tem mapas, mas não é pesado


def test_report_cli(tmp_path, capsys):
    out = tmp_path / "cli.pdf"
    assert main(["report", str(DEMO), "--out", str(out)]) == 0
    assert out.exists() and str(out) in capsys.readouterr().out


def test_report_contains_disclaimer_and_zones(tmp_path):
    pymupdf = pytest.importorskip("pymupdf")
    from terravisao.report import generate_report

    out = generate_report(DEMO, tmp_path / "r.pdf")
    text = "".join(page.get_text() for page in pymupdf.open(out))
    flat = " ".join(text.split()).lower()
    assert "não confirma a existência de minerais" in flat
    assert "zonas prioritárias" in flat
    assert "longonjo" in flat
