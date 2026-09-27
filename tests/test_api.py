"""Tests de l'API avec un faux moteur : aucun appel Gemini, aucun modèle chargé."""
import pytest
from fastapi.testclient import TestClient

from api import main
from app.pipeline import Answer

DOC = {"meta": {"title": "CNI", "organisme": "DAF", "url": "https://example.sn", "collected_at": "2026-09-26",
                "updated_at": ""}, "full_text": "Le timbre coûte 500 FCFA.", "similarity": 0.9}


class FakeRetriever:
    def search(self, query, **_):
        return [DOC]


class FakeEngine:
    llm = object()
    retriever = FakeRetriever()

    def ask(self, question, history, force_lang=None):
        return Answer("Le timbre coûte 500 FCFA [S1].", "answer", force_lang or "fr",
                      [{"n": 1, "title": "CNI"}], docs=[DOC], question_fr=question)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main.voice, "speak", lambda llm, text, lang: (b"RIFF", "audio/wav"))
    monkeypatch.setattr(main.voice, "transcribe", lambda llm, data, mime, lang: "Combien coûte la carte ?")
    monkeypatch.setattr(main, "generate_checklist", lambda llm, docs, q, lang: {"titre": "CNI", "resume": "x"})
    monkeypatch.setattr(main, "checklist_pdf", lambda fiche, sources, lang: b"%PDF")
    with TestClient(main.create_app(FakeEngine)) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask(client):
    r = client.post("/api/ask", json={"question": "Prix CNI ?", "lang": "en"})
    body = r.json()
    assert r.status_code == 200 and body["kind"] == "answer" and body["language"] == "en"
    assert body["can_checklist"] and body["sources"]


def test_ask_refuse_question_vide(client):
    assert client.post("/api/ask", json={"question": ""}).status_code == 422


def test_transcribe(client):
    r = client.post("/api/transcribe", files={"audio": ("q.wav", b"RIFFxxxx", "audio/wav")})
    assert r.json()["text"] == "Combien coûte la carte ?"


def test_speak(client):
    r = client.post("/api/speak", json={"text": "Bonjour", "lang": "fr"})
    assert r.status_code == 200 and r.headers["content-type"] == "audio/wav"


def test_checklist(client):
    body = client.post("/api/checklist", json={"question_fr": "CNI", "lang": "fr"}).json()
    assert body["fiche"]["titre"] == "CNI" and body["pdf"]


def test_front_servi(client):
    r = client.get("/")
    assert r.status_code == 200 and "TEKTALMA" in r.text
    assert client.get("/manifest.json").status_code == 200
