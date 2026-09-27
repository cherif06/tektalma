"""Configuration centrale de TEKTALMA AI."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Dossiers de données
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
VECTORSTORE_DIR = DATA_DIR / "vectorstore"
CHUNKS_FILE = PROCESSED_DIR / "chunks.json"
FICHES_FILE = PROCESSED_DIR / "fiches.json"

for _d in (RAW_DIR, PROCESSED_DIR, VECTORSTORE_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# LLM (Gemini) : modèle principal + modèle de secours
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
GEMINI_FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

# Voix : Gemini TTS (toutes langues), Oolel-Voices (wolof), secours gTTS (fr/en)
GEMINI_TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts")
GEMINI_TTS_VOICE = os.getenv("GEMINI_TTS_VOICE", "Kore")
WOLOF_TTS = os.getenv("WOLOF_TTS", "gemini")          # "oolel" ou "gemini"
# Oolel-Voices (Soynade Research) via sa démo en ligne sur Hugging Face
OOLEL_SPACE = "soynade-research/Oolel-Voices-Demo"
OOLEL_VOICE_URL = os.getenv(
    "OOLEL_VOICE_URL",
    "https://huggingface.co/spaces/soynade-research/Oolel-Voices-Demo/resolve/main/8_1_c.wav")
OOLEL_TIMEOUT = int(os.getenv("OOLEL_TIMEOUT", "40"))   # secondes avant de basculer
HF_TOKEN = os.getenv("HF_TOKEN") or None

# Embeddings et base vectorielle
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
COLLECTION_NAME = "tektalma_demarches"

# Retrieval
DENSE_K = 20          # candidats par recherche sémantique
BM25_K = 20           # candidats par recherche mots-clés
TOP_DOCS = 2          # nombre de fiches envoyées au LLM
# Similarité minimale (cosinus) de la meilleure fiche pour oser répondre.
# À ajuster avec : python -m scripts.eval_rag
MIN_SIMILARITY = float(os.getenv("MIN_SIMILARITY", "0.84"))

# Conversation
MAX_HISTORY = 6       # derniers messages transmis à la compréhension
