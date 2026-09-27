"""Compréhension : langue, domaine, intention, réécriture en français (1 appel LLM)."""
import json
import re

SYSTEM = """Tu es le module de compréhension de TEKTALMA AI, assistant des démarches administratives au Sénégal.
Analyse le DERNIER message de l'utilisateur (wolof, français, anglais ou mélange), en tenant compte de l'historique.
Le message peut venir d'une transcription vocale avec des fautes : interprète le sens.

Réponds UNIQUEMENT avec un objet JSON ayant exactement ces clés :
{
 "language": "fr" | "wo" | "en",
 "in_domain": true | false,
 "is_source_question": true | false,
 "category": "identite" | "passeport" | "etat_civil" | "education" | "entrepreneuriat" | "fiscalite" | "justice" | "autres" | null,
 "action": "premiere_demande" | "renouvellement" | "perte" | "modification" | "general" | null,
 "standalone_question_fr": "string",
 "needs_clarification": true | false,
 "clarification_question": "string" | null
}

Règles :
- language : langue du DERNIER MESSAGE uniquement. Ne regarde JAMAIS l'historique pour la langue.
  Une question entièrement en français est "fr", même si la conversation était en wolof avant.
  Si la phrase est construite en wolof avec des mots français ("carte nationale bi, dama ko ñàkk"), c'est "wo".
- in_domain : true si la question concerne des papiers, démarches, services publics ou l'administration au Sénégal, ou si c'est une question de suivi / salutation dans cette conversation. false sinon (sport, météo, recettes...).
- is_source_question : true si l'utilisateur demande d'où viennent les informations ou quelles sont les sources.
- standalone_question_fr : la question complète et autonome, reformulée en FRANÇAIS, en résolvant les références à l'historique.
  Exemple : historique sur la carte d'identité + "Et si je l'ai perdue ?" -> "Que faire en cas de perte de la carte nationale d'identité ?"
  Exemple : "Carte nationale bi, dama ko ñàkk, lan la ma wara def ?" -> "J'ai perdu ma carte nationale d'identité, que dois-je faire ?"
- needs_clarification : true SEULEMENT si on ne peut pas savoir de quelle démarche il s'agit, même avec l'historique (ex : "je veux un papier"), ou pour une simple salutation. Si une réponse générale est possible, mets false.
- clarification_question : UNE seule question courte, dans la langue de l'utilisateur, sinon null.
"""

DEFAULT = {
    "language": "fr", "in_domain": True, "is_source_question": False,
    "category": None, "action": None, "needs_clarification": False,
    "clarification_question": None,
}


def _format_history(history, max_items):
    lines = []
    for m in history[-max_items:]:
        role = "Utilisateur" if m["role"] == "user" else "Assistant"
        lines.append(f"{role} : {m['content'][:400]}")
    return "\n".join(lines) or "(aucun)"


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return json.loads(match.group(0) if match else text)


LANG_NAMES = {"fr": "français", "wo": "wolof", "en": "anglais"}


def understand(llm, question: str, history, max_history: int = 6, answer_lang: str | None = None) -> dict:
    prompt = (f"HISTORIQUE :\n{_format_history(history, max_history)}\n\n"
              f"DERNIER MESSAGE : {question}")
    if answer_lang in LANG_NAMES:
        prompt += (f"\n\n(Si tu poses une clarification_question, écris-la en "
                   f"{LANG_NAMES[answer_lang]}.)")
    try:
        data = parse_json(llm.generate(prompt, system=SYSTEM, json_mode=True))
    except (ValueError, json.JSONDecodeError):
        data = {}
    result = {**DEFAULT, **{k: v for k, v in data.items() if v is not None or k in DEFAULT}}
    if result.get("language") not in ("fr", "wo", "en"):
        result["language"] = "fr"
    result["standalone_question_fr"] = data.get("standalone_question_fr") or question
    return result
