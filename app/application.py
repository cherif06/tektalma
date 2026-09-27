"""Interface TEKTALMA AI.  Lancer :  streamlit run app/application.py"""
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app import voice  # noqa: E402
from app.checklist import LABELS, checklist_html, checklist_pdf, generate_checklist  # noqa: E402
from app.pipeline import Tektalma  # noqa: E402

st.set_page_config(page_title="TEKTALMA AI", page_icon="🇸🇳", layout="centered",
                   initial_sidebar_state="collapsed")

# ---------------------------------------------------------------- textes (⚠️ wolof à faire relire)
LANG_OPTIONS = {"Auto": None, "Wolof": "wo", "Français": "fr", "English": "en"}
EXAMPLES = [
    "Carte nationale bi, nan la ma mën a def ngir jël ko ?",
    "Carte nationale bi, dama ko ñàkk, lan la ma wara def ?",
    "Comment obtenir ma carte nationale d'identité ?",
    "Et si je l'ai perdue ?",
    "Combien coûte le passeport ?",
    "D'où viennent ces informations ?",
]
UI = {
    "fiche": {"wo": "📋 Defar sama fiche", "fr": "📋 Générer ma fiche", "en": "📋 Create my checklist"},
    "download": {"wo": "⬇️ Wàcce fiche bi (PDF)", "fr": "⬇️ Télécharger la fiche (PDF)",
                 "en": "⬇️ Download checklist (PDF)"},
    "sources": {"wo": "📚 Fan la xibaar yi jóge", "fr": "📚 Sources officielles", "en": "📚 Official sources"},
    "thinking": {"wo": "Maa ngi seet ci sources officielles yi…", "fr": "Recherche dans les sources officielles…",
                 "en": "Searching official sources…"},
    "fiche_wait": {"wo": "Maa ngi defar fiche bi…", "fr": "Préparation de la fiche…", "en": "Preparing checklist…"},
}


def t(key, lang):
    return UI[key].get(lang or "fr", UI[key]["fr"])


# ---------------------------------------------------------------- design
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Manrope:wght@400;500;600&display=swap');
:root{
  --night:#0A1430; --deep:#12204A; --ivory:#EEF1F7; --muted:#8E9BBD;
  --line:rgba(160,180,230,.18); --gold:#F2B233; --teranga:#1FB36B; --clay:#E4572E;
}
.stApp{background:
  radial-gradient(900px 500px at 50% -120px, rgba(242,178,51,.14), transparent 70%),
  radial-gradient(700px 600px at 110% 110%, rgba(31,179,107,.10), transparent 70%),
  var(--night); color:var(--ivory);}
html, body, .stApp, p, li, label, input, textarea, button{font-family:Manrope, system-ui, sans-serif !important;}
header[data-testid="stHeader"]{background:transparent;}
#MainMenu, footer, [data-testid="stToolbar"]{visibility:hidden;}
.block-container{padding-top:1.6rem; max-width:760px;}

/* --- orbe vocale : l'élément signature --- */
.tk-hero{display:flex; flex-direction:column; align-items:center; text-align:center; padding:12px 0 6px;}
.tk-orb{position:relative; width:150px; height:150px; margin-bottom:18px;}
.tk-orb span{position:absolute; inset:0; border-radius:50%; border:2px solid;}
.tk-orb span:nth-child(1){border-color:rgba(31,179,107,.55); animation:tk-breathe 4.8s ease-in-out infinite;}
.tk-orb span:nth-child(2){inset:16px; border-color:rgba(242,178,51,.7); animation:tk-breathe 4.8s ease-in-out .5s infinite;}
.tk-orb span:nth-child(3){inset:32px; border-color:rgba(228,87,46,.6); animation:tk-breathe 4.8s ease-in-out 1s infinite;}
.tk-orb .core{position:absolute; inset:46px; border-radius:50%;
  background:radial-gradient(circle at 35% 30%, #FFE7A8, var(--gold) 45%, #B9791A 100%);
  box-shadow:0 0 38px rgba(242,178,51,.55), 0 0 90px rgba(242,178,51,.25);}
@keyframes tk-breathe{0%,100%{transform:scale(1); opacity:.9} 50%{transform:scale(1.06); opacity:.45}}
@media (prefers-reduced-motion: reduce){.tk-orb span{animation:none}}
.tk-word{font-family:Sora, sans-serif; font-weight:700; font-size:2.4rem; letter-spacing:.14em; line-height:1;
  background:linear-gradient(90deg, var(--ivory), #C9D3EE); -webkit-background-clip:text; color:transparent;}
.tk-wo{font-family:Sora, sans-serif; font-size:1.2rem; margin:14px 0 4px; color:var(--gold);}
.tk-fr{color:var(--muted); max-width:520px; margin:0 auto; font-size:.95rem; line-height:1.55;}
.tk-bar{display:flex; align-items:center; gap:12px; padding:4px 0 10px;}
.tk-bar .tk-orb{width:38px; height:38px; margin:0;}
.tk-bar .tk-orb span:nth-child(2){inset:5px} .tk-bar .tk-orb span:nth-child(3){inset:10px}
.tk-bar .tk-orb .core{inset:13px; box-shadow:0 0 14px rgba(242,178,51,.6);}
.tk-bar .tk-word{font-size:1.25rem;}
.tk-bar small{color:var(--muted); display:block; font-size:.8rem;}

/* --- micro --- */
[data-testid="stAudioInput"]{border:1.5px solid rgba(242,178,51,.55); border-radius:18px;
  background:rgba(18,32,74,.75); box-shadow:0 0 28px rgba(242,178,51,.12); padding:6px 10px;}
[data-testid="stAudioInput"] label p{font-family:Sora, sans-serif !important; color:var(--gold); font-size:1rem;}

/* --- conversation --- */
[data-testid="stChatMessage"]{background:rgba(18,32,74,.55); border:1px solid var(--line);
  border-radius:4px 18px 18px 18px; padding:14px 16px; margin-bottom:10px;}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){
  background:rgba(242,178,51,.08); border-color:rgba(242,178,51,.3); border-radius:18px 4px 18px 18px;}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li{color:var(--ivory); line-height:1.6;}
[data-testid="stExpander"]{border:1px solid rgba(31,179,107,.35); border-radius:12px; background:rgba(31,179,107,.05);}
[data-testid="stExpander"] summary p{color:var(--teranga) !important; font-weight:600;}
[data-testid="stExpander"] a{color:#6FE0A4;}

/* --- boutons --- */
.stButton button, .stDownloadButton button{border-radius:999px; border:1px solid var(--line);
  background:rgba(238,241,247,.04); color:var(--ivory); font-weight:600;}
.stButton button:hover, .stDownloadButton button:hover{border-color:var(--gold); color:var(--gold);}
.stButton button:focus-visible, .stDownloadButton button:focus-visible{outline:2px solid var(--gold); outline-offset:2px;}
.stDownloadButton button{background:var(--gold); color:#1B2235; border:none;}
.stDownloadButton button:hover{background:#FFD36E; color:#1B2235;}
/* --- zone de saisie : fond sombre, texte clair --- */
[data-testid="stBottom"], [data-testid="stBottom"] > div{background:var(--night) !important;}
[data-testid="stChatInput"]{border-radius:18px; background:var(--deep) !important;
  border:1px solid rgba(242,178,51,.45) !important;}
[data-testid="stChatInput"] > div{background:transparent !important;}
[data-testid="stChatInput"] textarea{color:var(--ivory) !important; -webkit-text-fill-color:var(--ivory) !important;
  background:transparent !important; caret-color:var(--gold);}
[data-testid="stChatInput"] textarea::placeholder{color:var(--muted) !important;
  -webkit-text-fill-color:var(--muted) !important; opacity:1;}
[data-testid="stChatInput"] button{color:var(--gold) !important;}

/* --- fiche : aspect document officiel imprimé --- */
.tk-fiche{background:#FBF8F1; color:#1B2235; border-radius:3px; padding:0 22px 18px; margin:6px 0 10px;
  box-shadow:0 10px 30px rgba(0,0,0,.35);}
.tk-fiche .flag{height:6px; margin:0 -22px 16px;
  background:linear-gradient(90deg,#00853F 33.3%,#FDEF42 33.3% 66.6%,#E31B23 66.6%);}
.tk-fiche h3{font-family:Sora, sans-serif; font-size:1.15rem; margin:0 0 4px; color:#1B2235;}
.tk-fiche h4{font-family:Sora, sans-serif; font-size:.9rem; margin:14px 0 6px; color:#00853F;
  border-bottom:1px solid #D8D2C2; padding-bottom:4px;}
.tk-fiche p, .tk-fiche li{color:#1B2235 !important; font-size:.92rem; margin:3px 0;}
.tk-fiche ul{list-style:none; padding:0; margin:0;}
.tk-fiche li::before{content:""; display:inline-block; width:11px; height:11px; border:1.5px solid #1B2235;
  margin-right:9px; vertical-align:-1px;}
.tk-fiche .facts{display:flex; gap:10px; flex-wrap:wrap; margin-top:10px;}
.tk-fiche .fact{border:1.5px solid #1B2235; padding:6px 10px; font-size:.85rem;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

ORB = "<div class='tk-orb'><span></span><span></span><span></span><div class='core'></div></div>"


@st.cache_resource(show_spinner="TEKTALMA AI mi ngi tàmbali… · Démarrage…")
def get_engine():
    return Tektalma()


engine = get_engine()
state = st.session_state
for key, default in {"messages": [], "last_audio": None, "pending": None, "mic_key": 0}.items():
    state.setdefault(key, default)

# ---------------------------------------------------------------- en-tête
if not state.messages:
    st.markdown(f"""<div class="tk-hero">{ORB}<div class="tk-word">TEKTALMA</div>
      <p class="tk-wo">Na nga def ? Waxal sa laaj, ma tontu la.</p>
      <p class="tk-fr">Carte d'identité, passeport, état civil : posez votre question à voix haute
      ou par écrit, en wolof, en français ou en anglais. Les réponses viennent des sites officiels de l'État.</p>
      </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="tk-bar">{ORB}<div><div class="tk-word">TEKTALMA</div>
      <small>Démarches administratives du Sénégal</small></div></div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns([5, 2, 2], vertical_alignment="center")
with c1:
    choice = st.segmented_control("Làkk · Langue de réponse", list(LANG_OPTIONS), default="Auto",
                                  label_visibility="collapsed")
    forced_lang = LANG_OPTIONS.get(choice or "Auto")
with c2:
    voice_on = st.toggle("🔊 Voix", value=True)
with c3:
    if st.button("↺ Bu bees", help="Nouvelle conversation", use_container_width=True):
        state.messages, state.last_audio = [], None
        st.rerun()


# ---------------------------------------------------------------- rendu des messages
def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "demarche"


def render_fiche(f, lang):
    L = LABELS.get(lang, LABELS["fr"])

    def lst(key):
        items = f.get(key) or []
        return f"<h4>{L[key]}</h4><ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else ""

    facts = "".join(f"<div class='fact'><b>{L[k]}</b> : {f[k]}</div>" for k in ("cout", "delai") if f.get(k))
    st.markdown(f"""<div class="tk-fiche"><div class="flag"></div><h3>{f['titre']}</h3>
      <p>{f['resume']}</p><div class="facts">{facts}</div>
      {lst('documents')}{lst('etapes')}{lst('lieux')}{lst('conseils')}</div>""", unsafe_allow_html=True)


for i, m in enumerate(state.messages):
    with st.chat_message(m["role"], avatar="🧑🏾" if m["role"] == "user" else "🟡"):
        st.markdown(m["content"])
        if m["role"] != "assistant":
            continue
        lang = m.get("lang", "fr")
        if m.get("audio"):
            st.audio(m["audio"], format=m.get("mime", "audio/wav"), autoplay=not m.get("played"))
            m["played"] = True  # lecture automatique une seule fois
        if m.get("sources"):
            with st.expander(t("sources", lang)):
                for s in m["sources"]:
                    maj = s["updated_at"] or "non indiquée"
                    st.markdown(f"**[S{s['n']}] {s['title']}**  \n{s['organisme']}  \n"
                                f"[{s['url']}]({s['url']})  \n:grey[Collectée le {s['collected_at']} · "
                                f"mise à jour : {maj}]")
        if m.get("kind") == "answer" and m.get("docs"):
            if m.get("fiche"):
                render_fiche(m["fiche"], lang)
                if m.get("fiche_pdf"):
                    st.download_button(t("download", lang), data=m["fiche_pdf"],
                                       file_name=f"tektalma-{slug(m['fiche']['titre'])}.pdf",
                                       mime="application/pdf", key=f"dl_{i}")
                else:  # secours si le PDF n'a pas pu être créé
                    st.download_button(t("download", lang), data=m["fiche_html"],
                                       file_name=f"tektalma-{slug(m['fiche']['titre'])}.html",
                                       mime="text/html", key=f"dl_{i}")
            elif st.button(t("fiche", lang), key=f"fiche_{i}"):
                with st.spinner(t("fiche_wait", lang)):
                    try:
                        fiche = generate_checklist(engine.llm, m["docs"], m["question_fr"], lang)
                        m["fiche"] = fiche
                        m["fiche_html"] = checklist_html(fiche, m["sources"], lang)
                        try:
                            m["fiche_pdf"] = checklist_pdf(fiche, m["sources"], lang)
                        except Exception:  # noqa: BLE001
                            m["fiche_pdf"] = None
                    except Exception:  # noqa: BLE001
                        st.warning("Fiche indisponible pour le moment, réessayez dans un instant.")
                st.rerun()

# ---------------------------------------------------------------- entrées : voix + texte
audio = st.audio_input("🎙️ Bësal, wax, bësaat · Appuyez, parlez, appuyez à nouveau",
                       key=f"mic_{state.mic_key}")
with st.expander("💡 Misaal · Exemples de questions"):
    cols = st.columns(2)
    for k, ex in enumerate(EXAMPLES):
        if cols[k % 2].button(ex, key=f"ex_{k}", use_container_width=True):
            state.pending = ex
            st.rerun()
typed = st.chat_input("Bindal sa laaj… · Écrivez votre question…")

question, from_mic = None, False
if audio is not None:
    audio_bytes = audio.getvalue()
    digest = hashlib.md5(audio_bytes).hexdigest()
    if digest != state.last_audio:
        state.last_audio = digest
        with st.spinner("Maa ngi déglu… · Transcription…"):
            try:
                question = voice.transcribe(engine.llm, audio_bytes, audio.type or "audio/wav", forced_lang)
                from_mic = True
            except RuntimeError:
                st.error("Transcription indisponible pour le moment : écrivez votre question.")
if typed:
    question = typed
if state.pending:
    question, state.pending = state.pending, None

if question:
    history = [{"role": m["role"], "content": m["content"], "sources": m.get("sources")}
               for m in state.messages]
    state.messages.append({"role": "user", "content": question})
    with st.spinner(t("thinking", forced_lang)):
        ans = engine.ask(question, history, force_lang=forced_lang)
        audio_out, mime = (voice.speak(engine.llm, ans.text, ans.language)
                           if voice_on and ans.kind != "error" else (None, None))
    state.messages.append({
        "role": "assistant", "content": ans.text, "kind": ans.kind, "lang": ans.language,
        "sources": ans.sources, "docs": ans.docs, "question_fr": ans.question_fr,
        "audio": audio_out, "mime": mime, "played": False,
    })
    if from_mic:
        state.mic_key += 1  # remet le micro à zéro pour la question suivante
    st.rerun()
