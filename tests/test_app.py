"""A app inteira renderiza sem excepções, nos dois módulos (teste sem navegador)."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def _fresh() -> AppTest:
    return AppTest.from_file(APP, default_timeout=180).run()


def _no_errors(at: AppTest) -> None:
    assert not at.exception, [e.value for e in at.exception]


def test_analysis_module_renders_both_demo_datasets():
    at = _fresh()
    _no_errors(at)
    for source in at.selectbox(key="geo_source").options[:2]:
        at.selectbox(key="geo_source").select(source).run()
        _no_errors(at)


def test_chat_answers_with_numbers():
    at = _fresh()
    at.selectbox(key="geo_source").select("Longonjo: modelo sintético coerente (fictício)").run()
    next(b for b in at.button if b.label == "Onde estão as zonas?").click().run()
    _no_errors(at)
    texts = " ".join(m.markdown[0].value for m in at.chat_message if m.markdown)
    assert "Zona A" in texts and "maior do que o acaso" in texts


def test_terravisao_module_still_works():
    at = _fresh()
    at.radio(key="module").set_value("TerraVisão (satélite)").run()
    _no_errors(at)
    at.radio(key="mode").set_value("Nova análise").run()
    _no_errors(at)
