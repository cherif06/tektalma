"""Orchestration : comprendre -> chercher -> générer -> vérifier."""
from dataclasses import dataclass, field

from app.embeddings import Embedder
from app.generation import generate_answer
from app.guards import check_numbers, clean_citations, keep_language
from app.llm.client import LLMClient
from app.messages import msg
from app.retrieval import Retriever
from app.understanding import understand
from app.wolof import to_wolof
from config import settings


@dataclass
class Answer:
    text: str
    kind: str                     # answer | clarification | out_of_domain | no_info | sources | error
    language: str = "fr"
    sources: list = field(default_factory=list)
    debug: dict = field(default_factory=dict)
    docs: list = field(default_factory=list)      # fiches utilisées (pour la fiche récapitulative)
    question_fr: str = ""


def source_card(n, doc):
    m = doc["meta"]
    return {"n": n, "title": m["title"], "organisme": m["organisme"], "url": m["url"],
            "collected_at": str(m.get("collected_at", "")), "updated_at": str(m.get("updated_at", ""))}


class Tektalma:
    def __init__(self, retriever=None, llm=None):
        self.llm = llm or LLMClient()
        self.retriever = retriever or Retriever(Embedder())

    def ask(self, question: str, history=None, force_lang: str | None = None) -> Answer:
        history = history or []
        try:
            u = understand(self.llm, question, history, settings.MAX_HISTORY, force_lang)
        except RuntimeError:
            return Answer(msg("error", "fr"), "error")
        lang = force_lang or u["language"]
        debug = {"understanding": u}

        if u.get("is_source_question"):
            last = next((m.get("sources") for m in reversed(history)
                         if m["role"] == "assistant" and m.get("sources")), None)
            if not last:
                return Answer(msg("no_sources_yet", lang), "sources", lang, debug=debug)
            lines = [msg("sources_intro", lang)] + [
                f"- [S{s['n']}] {s['title']} — {s['organisme']}" for s in last]
            return Answer("\n".join(lines), "sources", lang, last, debug)

        if not u.get("in_domain", True):
            return Answer(msg("out_of_domain", lang), "out_of_domain", lang, debug=debug)

        if u.get("needs_clarification") and u.get("clarification_question"):
            return Answer(u["clarification_question"], "clarification", lang, debug=debug)

        # Domaine détecté mais absent du corpus (ex : entreprise) -> on ne force pas de réponse
        covered = {f["meta"]["category"] for f in self.retriever.fiches.values()}
        if u.get("category") and u["category"] not in covered and u["category"] != "autres":
            return Answer(msg("no_info", lang), "no_info", lang, debug=debug)

        query = u["standalone_question_fr"]
        docs = self.retriever.search(query, category=u.get("category"), action=u.get("action"))
        debug["retrieved"] = [(d["meta"]["fiche"], d["similarity"]) for d in docs]
        best_sim = max((d["similarity"] for d in docs), default=0.0)

        if best_sim < settings.MIN_SIMILARITY:
            return Answer(msg("no_info", lang), "no_info", lang, debug=debug)

        # Le wolof est rédigé d'abord en français (vérifiable), puis traduit.
        gen_lang = "fr" if lang == "wo" else lang
        try:
            raw, context = generate_answer(self.llm, docs, query, question, gen_lang)
        except RuntimeError:
            return Answer(msg("error", lang), "error", lang, debug=debug)

        text, used = clean_citations(raw, len(docs))
        text, removed = check_numbers(text, context)
        debug["removed_sentences"] = removed
        if not text:
            return Answer(msg("no_info", lang), "no_info", lang, debug=debug)

        text = keep_language(text, gen_lang)   # une seule langue dans la réponse
        if not text:
            return Answer(msg("no_info", lang), "no_info", lang, debug=debug)

        if lang == "wo":
            debug["answer_fr"] = text
            try:
                wolof = to_wolof(self.llm, text)
            except RuntimeError:
                wolof = None
            if wolof:
                text, _ = clean_citations(wolof, len(docs))
            else:
                lang = "fr"  # traduction non fiable : on garde la version française vérifiée

        cited = used or list(range(1, len(docs) + 1))
        sources = [source_card(n, docs[n - 1]) for n in cited]
        cards_docs = [{"meta": d["meta"], "full_text": d["full_text"]} for d in docs]
        return Answer(text, "answer", lang, sources, debug, cards_docs, query)
