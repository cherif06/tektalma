"use strict";

const EXAMPLES = [
  "Carte nationale bi, nan la ma mën a def ngir jël ko ?",
  "Carte nationale bi, dama ko ñàkk, lan la ma wara def ?",
  "Comment obtenir ma carte nationale d'identité ?",
  "Combien coûte le passeport ?",
  "Comment obtenir un extrait de naissance ?",
  "D'où viennent ces informations ?",
];
// ⚠️ Libellés wolof à faire relire par un locuteur
const UI = {
  sources: { wo: "📚 Fan la xibaar yi jóge", fr: "📚 Sources officielles", en: "📚 Official sources" },
  fiche: { wo: "📋 Defar sama fiche", fr: "📋 Générer ma fiche", en: "📋 Create my checklist" },
  download: { wo: "⬇️ Wàcce fiche bi (PDF)", fr: "⬇️ Télécharger la fiche (PDF)", en: "⬇️ Download checklist (PDF)" },
  listen: { wo: "🔊 Déglu", fr: "🔊 Écouter", en: "🔊 Listen" },
  thinking: { wo: "Maa ngi seet ci sources officielles yi", fr: "Recherche dans les sources officielles", en: "Searching official sources" },
};
const LABELS = {
  fr: { documents: "Documents à préparer", etapes: "Étapes", lieux: "Où aller", cout: "Coût", delai: "Délai", conseils: "À savoir" },
  wo: { documents: "Kayit yi nga war a waajal", etapes: "Ni nga koy defe", lieux: "Fan nga war a dem", cout: "Njëg", delai: "Diir", conseils: "Lu war a xam" },
  en: { documents: "Documents to prepare", etapes: "Steps", lieux: "Where to go", cout: "Cost", delai: "Processing time", conseils: "Good to know" },
};
const t = (k, lang) => UI[k][lang] || UI[k].fr;

const $ = (s) => document.querySelector(s);
const chat = $("#chat"), form = $("#form"), input = $("#input"), micBtn = $("#mic"), statusEl = $("#status");
let history = [];          // {role, content, sources}
let forcedLang = "";
let busy = false;

// ------------------------------------------------------------------ utilitaires
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

/** Markdown minimal (gras, listes, citations [S1]) — tout est échappé d'abord. */
function md(text) {
  const out = [];
  let list = null;
  const inline = (s) => esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\[S(\d+)\]/g, '<span class="cite">[S$1]</span>');
  for (const raw of String(text).split("\n")) {
    const line = raw.trim();
    const m = line.match(/^([-*•]|\d+[.)])\s+(.*)$/);
    if (m) {
      const tag = /\d/.test(m[1]) ? "ol" : "ul";
      if (list !== tag) { if (list) out.push(`</${list}>`); out.push(`<${tag}>`); list = tag; }
      out.push(`<li>${inline(m[2])}</li>`);
      continue;
    }
    if (list) { out.push(`</${list}>`); list = null; }
    if (line) out.push(`<p>${inline(line.replace(/^#+\s*/, ""))}</p>`);
  }
  if (list) out.push(`</${list}>`);
  return out.join("");
}

function setStatus(text, err = false) {
  statusEl.textContent = text || "";
  statusEl.classList.toggle("err", err);
}

function setBusy(v) {
  busy = v;
  for (const b of [micBtn, $("#send")]) b.disabled = v && !recorder;
}

function scrollDown() {
  requestAnimationFrame(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
}

async function api(path, body) {
  const res = await fetch(path, body instanceof FormData
    ? { method: "POST", body }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${path} ${res.status}`);
  return res;
}

function bubble(role, html, cls = "") {
  $("#hero")?.remove();
  const el = document.createElement("div");
  el.className = `msg ${role} ${cls}`.trim();
  el.innerHTML = html;
  chat.appendChild(el);
  scrollDown();
  return el;
}

// ------------------------------------------------------------------ question -> réponse
async function ask(question) {
  question = question.trim();
  if (!question || busy) return;
  setBusy(true);
  setStatus("");
  bubble("user", md(question));
  const pending = bubble("assistant", `<span class="dots">${esc(t("thinking", forcedLang))}</span>`, "pending");
  try {
    const res = await api("/api/ask", { question, history: history.slice(-6), lang: forcedLang || null });
    const ans = await res.json();
    history.push({ role: "user", content: question });
    history.push({ role: "assistant", content: ans.text, sources: ans.sources });
    pending.classList.remove("pending");
    renderAnswer(pending, ans);
  } catch (e) {
    pending.classList.remove("pending");
    pending.innerHTML = md("Le service est momentanément indisponible. Réessayez dans un instant.");
  } finally {
    setBusy(false);
  }
}

function renderAnswer(el, ans) {
  const lang = ans.language || "fr";
  el.innerHTML = md(ans.text);
  const actions = document.createElement("div");
  actions.className = "actions";
  el.appendChild(actions);

  if (ans.sources?.length) {
    const d = document.createElement("details");
    d.className = "sources";
    d.innerHTML = `<summary>${esc(t("sources", lang))}</summary>` + ans.sources.map((s) =>
      `<div><strong>[S${esc(s.n)}] ${esc(s.title)}</strong><br>${esc(s.organisme)}<br>
       <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a><br>
       <small>Collectée le ${esc(s.collected_at)} · mise à jour : ${esc(s.updated_at || "non indiquée")}</small></div>`).join("");
    el.appendChild(d);
  }

  if (ans.kind !== "error") {
    const listen = document.createElement("button");
    listen.textContent = t("listen", lang);
    listen.onclick = () => playVoice(el, ans.text, lang, listen);
    actions.appendChild(listen);
    if ($("#voice").checked) playVoice(el, ans.text, lang, listen);
  }
  if (ans.can_checklist) {
    const b = document.createElement("button");
    b.textContent = t("fiche", lang);
    b.onclick = () => makeChecklist(el, ans.question_fr, lang, b);
    actions.appendChild(b);
  }
  scrollDown();
}

// ------------------------------------------------------------------ voix (le texte s'affiche d'abord)
async function playVoice(el, text, lang, btn) {
  let audio = el.querySelector("audio");
  if (!audio) {
    btn.disabled = true;
    try {
      const res = await api("/api/speak", { text, lang });
      audio = document.createElement("audio");
      audio.controls = true;
      audio.src = URL.createObjectURL(await res.blob());
      el.insertBefore(audio, el.querySelector(".actions"));
      btn.remove();
    } catch {
      btn.disabled = false;
      return;
    }
  }
  audio.play().catch(() => {});   // lecture auto parfois bloquée sur mobile : le lecteur reste visible
}

// ------------------------------------------------------------------ fiche récapitulative
async function makeChecklist(el, questionFr, lang, btn) {
  btn.disabled = true;
  btn.textContent = "…";
  try {
    const res = await api("/api/checklist", { question_fr: questionFr, lang });
    const { fiche, pdf } = await res.json();
    const L = LABELS[lang] || LABELS.fr;
    const lst = (k) => fiche[k]?.length ? `<h4>${esc(L[k])}</h4><ul>${fiche[k].map((i) => `<li>${esc(i)}</li>`).join("")}</ul>` : "";
    const facts = ["cout", "delai"].filter((k) => fiche[k]).map((k) => `<div class="fact"><b>${esc(L[k])}</b> : ${esc(fiche[k])}</div>`).join("");
    const card = document.createElement("div");
    card.className = "fiche";
    card.innerHTML = `<div class="flag"></div><h3>${esc(fiche.titre)}</h3><p>${esc(fiche.resume)}</p>
      <div class="facts">${facts}</div>${lst("documents")}${lst("etapes")}${lst("lieux")}${lst("conseils")}`;
    el.appendChild(card);
    if (pdf) {
      const blob = new Blob([Uint8Array.from(atob(pdf), (c) => c.charCodeAt(0))], { type: "application/pdf" });
      const a = document.createElement("a");
      a.className = "primary";
      a.href = URL.createObjectURL(blob);
      a.download = `tektalma-${(fiche.titre || "demarche").toLowerCase().normalize("NFD").replace(/[^a-z0-9]+/g, "-").slice(0, 40)}.pdf`;
      a.textContent = t("download", lang);
      btn.replaceWith(a);
    } else {
      btn.remove();
    }
    scrollDown();
  } catch {
    btn.disabled = false;
    btn.textContent = t("fiche", lang);
    setStatus("Fiche indisponible pour le moment, réessayez.", true);
  }
}

// ------------------------------------------------------------------ micro : enregistrement WAV 16 kHz
// (WAV plutôt que webm/mp4 : accepté partout par Gemini, identique sur Android et iPhone)
let recorder = null;

async function startRecording() {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
  } catch {
    setStatus("Micro indisponible : autorisez l'accès au micro (HTTPS requis).", true);
    return;
  }
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const src = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(4096, 1, 1);
  const chunks = [];
  node.onaudioprocess = (e) => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
  src.connect(node);
  node.connect(ctx.destination);
  recorder = { stream, ctx, node, src, chunks, started: Date.now() };
  micBtn.classList.add("rec");
  micBtn.setAttribute("aria-label", "Arrêter l'enregistrement");
  setStatus("🎙️ Maa ngi déglu… · Parlez, puis appuyez à nouveau");
  recorder.timeout = setTimeout(stopRecording, 60000);
}

async function stopRecording() {
  const r = recorder;
  if (!r) return;
  recorder = null;
  clearTimeout(r.timeout);
  r.node.disconnect(); r.src.disconnect();
  r.stream.getTracks().forEach((tr) => tr.stop());
  const rate = r.ctx.sampleRate;
  await r.ctx.close();
  micBtn.classList.remove("rec");
  micBtn.setAttribute("aria-label", "Parler");
  if (Date.now() - r.started < 700) { setStatus("Appuyez, parlez, puis appuyez à nouveau."); return; }

  setBusy(true);
  setStatus("Maa ngi déglu… · Transcription…");
  try {
    const fd = new FormData();
    fd.append("audio", encodeWav(r.chunks, rate, 16000), "question.wav");
    if (forcedLang) fd.append("lang", forcedLang);
    const { text } = await (await api("/api/transcribe", fd)).json();
    setBusy(false);
    setStatus("");
    if (text) await ask(text);
  } catch {
    setBusy(false);
    setStatus("Transcription indisponible : écrivez votre question.", true);
  }
}

function encodeWav(chunks, inRate, outRate) {
  const len = chunks.reduce((n, c) => n + c.length, 0);
  const data = new Float32Array(len);
  let o = 0;
  for (const c of chunks) { data.set(c, o); o += c.length; }
  const ratio = inRate / outRate;
  const n = Math.floor(len / ratio);
  const buf = new DataView(new ArrayBuffer(44 + n * 2));
  const str = (off, s) => [...s].forEach((ch, i) => buf.setUint8(off + i, ch.charCodeAt(0)));
  str(0, "RIFF"); buf.setUint32(4, 36 + n * 2, true); str(8, "WAVE"); str(12, "fmt ");
  buf.setUint32(16, 16, true); buf.setUint16(20, 1, true); buf.setUint16(22, 1, true);
  buf.setUint32(24, outRate, true); buf.setUint32(28, outRate * 2, true);
  buf.setUint16(32, 2, true); buf.setUint16(34, 16, true); str(36, "data"); buf.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) {
    const s = Math.max(-1, Math.min(1, data[Math.floor(i * ratio)]));
    buf.setInt16(44 + i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return new Blob([buf], { type: "audio/wav" });
}

// ------------------------------------------------------------------ événements
micBtn.addEventListener("click", () => (recorder ? stopRecording() : busy ? null : startRecording()));
form.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = input.value;
  input.value = "";
  ask(q);
});
$("#langs").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-lang]");
  if (!b) return;
  forcedLang = b.dataset.lang;
  document.querySelectorAll("#langs button").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
});
$("#reset").addEventListener("click", () => location.reload());

const ex = $("#examples");
EXAMPLES.forEach((q) => {
  const b = document.createElement("button");
  b.textContent = q;
  b.onclick = () => ask(q);
  ex.appendChild(b);
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/sw.js").catch(() => {}));
}
