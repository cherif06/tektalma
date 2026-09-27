"""API TEKTALMA AI + service du front PWA.  Lancer :  uvicorn api.main:app --port 8000"""
import base64
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import voice
from app.checklist import checklist_pdf, generate_checklist
from app.pipeline import source_card

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
LANGS = ("fr", "wo", "en")
MAX_AUDIO_BYTES = 10 * 1024 * 1024


def _default_engine():
    from app.pipeline import Tektalma

    return Tektalma()


def create_app(engine_factory=_default_engine) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine_factory()   # chargé une seule fois (modèle + index)
        yield

    app = FastAPI(title="TEKTALMA AI", lifespan=lifespan)
    _routes(app)
    if WEB_DIR.exists():
        app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


def get_engine(request: Request):
    return request.app.state.engine


def _lang(value: str | None) -> str | None:
    return value if value in LANGS else None


class HistoryItem(BaseModel):
    role: str
    content: str = Field(max_length=4000)
    sources: list | None = None


class AskIn(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryItem] = Field(default_factory=list, max_length=20)
    lang: str | None = None


class SpeakIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    lang: str = "fr"


class ChecklistIn(BaseModel):
    question_fr: str = Field(min_length=1, max_length=1000)
    lang: str = "fr"


def _routes(app: FastAPI):
    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/ask")
    def ask(body: AskIn, engine=Depends(get_engine)):
        ans = engine.ask(body.question, [h.model_dump() for h in body.history],
                         force_lang=_lang(body.lang))
        return {"text": ans.text, "kind": ans.kind, "language": ans.language,
                "sources": ans.sources, "question_fr": ans.question_fr,
                "can_checklist": ans.kind == "answer" and bool(ans.docs)}

    @app.post("/api/transcribe")
    async def transcribe(audio: UploadFile = File(...), lang: str | None = Form(None),
                         engine=Depends(get_engine)):
        data = await audio.read()
        if not data:
            raise HTTPException(400, "Audio vide")
        if len(data) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio trop long")
        mime = (audio.content_type or "audio/webm").split(";")[0]
        try:
            text = voice.transcribe(engine.llm, data, mime, _lang(lang))
        except RuntimeError:
            raise HTTPException(503, "Transcription indisponible") from None
        return {"text": text}

    @app.post("/api/speak")
    def speak(body: SpeakIn, engine=Depends(get_engine)):
        audio, mime = voice.speak(engine.llm, body.text, _lang(body.lang) or "fr")
        if not audio:
            raise HTTPException(503, "Voix indisponible")
        return Response(audio, media_type=mime)

    @app.post("/api/checklist")
    def checklist(body: ChecklistIn, engine=Depends(get_engine)):
        lang = _lang(body.lang) or "fr"
        # On relit les fiches côté serveur : le client n'envoie jamais le contexte au LLM.
        docs = engine.retriever.search(body.question_fr)
        if not docs:
            raise HTTPException(404, "Aucune fiche trouvée")
        sources = [source_card(n, d) for n, d in enumerate(docs, start=1)]
        try:
            fiche = generate_checklist(engine.llm, docs, body.question_fr, lang)
        except (RuntimeError, ValueError):
            raise HTTPException(503, "Fiche indisponible") from None
        try:
            pdf = base64.b64encode(checklist_pdf(fiche, sources, lang)).decode()
        except Exception:  # noqa: BLE001
            pdf = None
        return {"fiche": fiche, "sources": sources, "pdf": pdf}


app = create_app()
