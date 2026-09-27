from app import voice


def test_gemini_tts_mis_en_pause_apres_quota(monkeypatch):
    calls = []

    def quota(llm, text):
        calls.append(text)
        raise RuntimeError("LLM indisponible : 429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(voice, "_paused_until", {})
    monkeypatch.setattr(voice, "_gemini_tts", quota)
    monkeypatch.setattr(voice, "_gtts", lambda text, lang: (b"mp3", "audio/mp3"))
    assert voice.speak(None, "Bonjour.", "fr") == (b"mp3", "audio/mp3")
    assert voice.speak(None, "Au revoir.", "fr") == (b"mp3", "audio/mp3")
    assert len(calls) == 1   # 2e phrase : Gemini n'est plus tenté


def test_citations_retirees_de_la_voix():
    assert voice.speakable("Coût : 500 FCFA [S1], [S2]. Délai [S1].") == "Coût : 500 FCFA. Délai."


def test_wolof_sans_voix_disponible(monkeypatch):
    calls = []

    def quota(*args):
        calls.append(1)
        raise RuntimeError("You have exceeded your free ZeroGPU quota")

    monkeypatch.setattr(voice, "_paused_until", {})
    monkeypatch.setattr(voice, "_gemini_tts", quota)
    monkeypatch.setattr(voice, "_oolel", quota)
    assert voice.speak(None, "Salaam aleekum.", "wo") == (None, None)
    assert voice.speak(None, "Jërëjëf.", "wo") == (None, None)
    assert len(calls) == 2   # 2e phrase : les deux moteurs sont en pause
