"""Client Gemini : texte (avec réessais + modèle de secours) et synthèse vocale."""
import time

from google import genai
from google.genai import types

from config import settings

RETRYABLE = {429, 500, 502, 503, 504}


class LLMClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY manquante dans .env")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.models = [m for m in dict.fromkeys(
            [settings.GEMINI_MODEL, settings.GEMINI_FALLBACK_MODEL]) if m]

    def _call(self, models, contents, config):
        last_error = None
        for model in models:
            for attempt in range(2):
                try:
                    return self.client.models.generate_content(
                        model=model, contents=contents, config=config)
                except Exception as e:  # noqa: BLE001
                    last_error = e
                    if getattr(e, "code", None) in RETRYABLE and attempt == 0:
                        time.sleep(1.0)
                        continue
                    break  # erreur non temporaire ou 2e échec : modèle suivant
        raise RuntimeError(f"LLM indisponible : {last_error}")

    def generate(self, contents, system: str | None = None,
                 json_mode: bool = False, temperature: float = 0.1) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        resp = self._call(self.models, contents, config)
        return (resp.text or "").strip()

    def synthesize(self, text: str) -> tuple[bytes, str]:
        """Renvoie (données audio brutes, mime_type) via le modèle TTS de Gemini."""
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=settings.GEMINI_TTS_VOICE))),
        )
        resp = self._call([settings.GEMINI_TTS_MODEL], text, config)
        part = resp.candidates[0].content.parts[0].inline_data
        return part.data, part.mime_type or "audio/L16;rate=24000"
