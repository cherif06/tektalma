from app import voice


def test_gemini_tts_mis_en_pause_apres_quota(monkeypatch):
    calls = []

    def quota(llm, text):
        calls.append(text)
        raise RuntimeError("LLM indisponible : 429 RESOURCE_EXHAUSTED")

    monkeypatch.setattr(voice, "_gemini_paused_until", 0.0)
    monkeypatch.setattr(voice, "_gemini_tts", quota)
    monkeypatch.setattr(voice, "_gtts", lambda text, lang: (b"mp3", "audio/mp3"))
    assert voice.speak(None, "Bonjour.", "fr") == (b"mp3", "audio/mp3")
    assert voice.speak(None, "Au revoir.", "fr") == (b"mp3", "audio/mp3")
    assert len(calls) == 1   # 2e phrase : Gemini n'est plus tenté


def test_citations_retirees_de_la_voix():
    assert voice.speakable("Coût : 500 FCFA [S1], [S2]. Délai [S1].") == "Coût : 500 FCFA. Délai."
