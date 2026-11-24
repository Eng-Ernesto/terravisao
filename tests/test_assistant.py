import io
import json
import urllib.error

import pytest

from geoexplora import analysis, assistant, demo


@pytest.fixture(scope="module")
def summaries():
    out = {}
    for title, folder in demo.list_datasets().items():
        pts, grids, _ = demo.load(folder)
        out[title] = analysis.run(pts, grids=grids).summary()
    return out


@pytest.fixture
def coherent(summaries):
    return summaries["Longonjo: modelo sintético coerente (fictício)"]


@pytest.fixture
def team(summaries):
    return summaries["Longonjo: dados da equipa (fictícios)"]


def test_interpretation_is_honest_for_random_data(team):
    text = assistant.interpretation(team)
    assert "FICTÍCIOS" in text
    assert "acaso" in text
    assert "não supera o acaso" in text.lower()


def test_interpretation_reports_real_structure(coherent):
    text = assistant.interpretation(coherent)
    assert "Th_radiometria_ppm" in text
    assert "Supera o acaso" in text
    assert "NdPr/TREO" in text


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Onde estão as zonas prioritárias?", "Zona"),
        ("Há relação com a magnética?", "Spearman"),
        ("O modelo funciona?", "acaso"),
        ("Qual a fracção de NdPr para ímanes?", "NdPr/TREO"),
        ("Quais as limitações?", "teores económicos"),
    ],
)
def test_offline_answers_use_the_numbers(coherent, question, expected):
    answer, origin = assistant.Assistant(coherent).ask(question)
    assert origin == "offline" and expected in answer


def test_no_token_means_offline(coherent, monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    monkeypatch.delenv("CLOUDFLARE_ACCOUNT_ID", raising=False)
    assert assistant.Assistant(coherent).mode == "offline"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_cloudflare_success_sends_summary_but_not_the_token_in_body(coherent, monkeypatch):
    seen = {}

    def fake_open(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.headers["Authorization"]
        seen["body"] = json.loads(req.data)
        return FakeResponse(
            json.dumps({"choices": [{"message": {"content": "Resposta da IA."}}]}).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    a = assistant.Assistant(coherent, account_id="acc123", token="tok-secret")
    answer, origin = a.ask("Resume.")
    assert origin == "ia" and answer.startswith("Resposta da IA.")
    assert "fictícios" in answer  # os dados da demonstração são fictícios: aviso garantido
    assert "/accounts/acc123/ai/v1/chat/completions" in seen["url"]
    assert seen["auth"] == "Bearer tok-secret"
    body = json.dumps(seen["body"])
    assert "tok-secret" not in body and "n_amostras" in body  # contexto vai, token não
    assert seen["body"]["messages"][0]["role"] == "system"


@pytest.mark.parametrize(
    "error,fragment",
    [
        (urllib.error.HTTPError("u", 401, "x", {}, None), "token inválido"),
        (urllib.error.HTTPError("u", 429, "x", {}, None), "quota esgotada"),
        (urllib.error.URLError("sem rede"), "sem ligação"),
    ],
)
def test_cloudflare_failures_fall_back_to_offline(coherent, monkeypatch, error, fragment):
    def boom(req, timeout):
        raise error

    monkeypatch.setattr("urllib.request.urlopen", boom)
    answer, origin = assistant.Assistant(coherent, account_id="a", token="t").ask(
        "Onde estão as zonas?"
    )
    assert origin == "offline" and fragment in answer and "Zona" in answer


def test_history_is_truncated(coherent, monkeypatch):
    captured = {}

    def fake_open(req, timeout):
        captured["n"] = len(json.loads(req.data)["messages"])
        return FakeResponse(json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    hist = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(40)]
    assistant.Assistant(coherent, account_id="a", token="t").ask("x", hist)
    assert captured["n"] == 1 + 2 * assistant.MAX_TURNS + 1


def test_brief_is_short_and_honest(team, coherent):
    b_team, b_coh = assistant.brief(team), assistant.brief(coherent)
    assert "FICTÍCIOS" in b_team and "não supera o acaso" in b_team
    assert "zona de interesse" in b_coh and "**A**" in b_coh
    assert len(b_coh) < 450


def _ok(text):
    return FakeResponse(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


def test_default_model_is_one_that_exists():
    assert assistant.DEFAULT_MODEL == "@cf/mistralai/mistral-small-3.1-24b-instruct"
    assert "llama-3.1-8b" not in assistant.DEFAULT_MODEL  # já não existe no catálogo


def test_unavailable_model_falls_back_to_the_next_one(coherent, monkeypatch):
    tried = []

    def fake_open(req, timeout):
        model = json.loads(req.data)["model"]
        tried.append(model)
        if model == assistant.DEFAULT_MODEL:
            raise urllib.error.HTTPError("u", 404, "x", {}, None)
        return _ok("Resposta do segundo modelo.")

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    answer, origin = assistant.Assistant(coherent, account_id="a", token="t").ask("Resume.")
    assert origin == "ia" and answer.startswith("Resposta do segundo modelo.")
    assert tried == [assistant.DEFAULT_MODEL, assistant.FALLBACK_MODELS[0]]


def test_empty_answer_from_reasoning_model_is_not_returned(coherent, monkeypatch):
    # gemma-4 e glm-4.7-flash gastam os tokens a pensar e devolvem content vazio
    def fake_open(req, timeout):
        return FakeResponse(
            json.dumps(
                {"choices": [{"message": {"content": "", "reasoning_content": "..."}}]}
            ).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_open)
    answer, origin = assistant.Assistant(coherent, account_id="a", token="t").ask(
        "Onde estão as zonas?"
    )
    assert origin == "offline" and "vazia" in answer and "Zona" in answer


def test_quota_error_does_not_try_other_models(coherent, monkeypatch):
    calls = []

    def boom(req, timeout):
        calls.append(1)
        raise urllib.error.HTTPError("u", 429, "x", {}, None)

    monkeypatch.setattr("urllib.request.urlopen", boom)
    answer, origin = assistant.Assistant(coherent, account_id="a", token="t").ask("Resume.")
    assert origin == "offline" and "quota esgotada" in answer and len(calls) == 1


def test_workers_ai_native_format_is_understood():
    assert assistant._extract_text({"result": {"response": "Olá"}}) == "Olá"
    assert assistant._extract_text({"choices": [{"message": {"content": " Olá "}}]}) == "Olá"
    assert (
        assistant._extract_text({"result": {"choices": [{"message": {"content": "Olá"}}]}}) == "Olá"
    )
