# 🇸🇳 TEKTALMA AI

Assistant vocal des démarches administratives au Sénégal (français · wolof · anglais),
basé sur un RAG qui répond **uniquement** à partir de sources officielles.

## Lancer en local
```
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt -r requirements-dev.txt
python -m scripts.build_index            # construit l'index
uvicorn api.main:app --reload --port 8000  # API + app PWA sur http://localhost:8000
pytest -q                                 # tests (sans appel Gemini)
python -m scripts.eval_rag                # évaluation + calibrage du seuil (appels Gemini)
```
Ancienne interface (plan B) : `streamlit run app/application.py`

## Structure
- `app/` : pipeline RAG (compréhension, recherche hybride, génération, garde-fous, voix, wolof)
- `api/main.py` : API FastAPI (`/api/ask`, `/api/transcribe`, `/api/speak`, `/api/checklist`, `/health`) qui sert aussi le front
- `web/` : PWA installable (HTML/CSS/JS sans build, service worker, micro WAV 16 kHz)

## Déploiement (GitHub Actions → GHCR → Dokploy)
Chaque push sur `main` : tests → build de l'image → publication sur `ghcr.io/<repo>` → redéploiement Dokploy → vérification de `/health`.
Les PR lancent uniquement tests + build.

Configuration (une seule fois) :
1. **Dokploy** : créer une application, source *Docker*, image `ghcr.io/<owner>/<repo>:latest`, port **8000**.
   Si le package GHCR est privé, ajouter le registre `ghcr.io` dans Dokploy (utilisateur GitHub + token `read:packages`).
   Variables d'environnement : celles de `.env.example` (`GEMINI_API_KEY`, `HF_TOKEN`...). Domaine + HTTPS (Let's Encrypt) :
   **HTTPS est obligatoire** pour le micro et l'installation de la PWA.
2. **GitHub → Settings → Secrets and variables → Actions** :
   secrets `DOKPLOY_URL` (ex. `https://dokploy.mondomaine.com`), `DOKPLOY_API_KEY` (Dokploy → Settings → API),
   `DOKPLOY_APPLICATION_ID` ; variable `APP_URL` (ex. `https://tektalma.mondomaine.com`).

## Architecture
Question (voix/texte) → transcription Gemini → compréhension (langue, intention,
reformulation en français) → recherche hybride ChromaDB + BM25 (fusion RRF) →
seuil de confiance → génération Gemini à partir des fiches → garde-fous
(citations valides, chiffres présents dans les sources) → réponse + sources → voix.

## Ajouter ou désactiver une démarche
- Ajouter : copier `data/raw/_modele/MODELE_fiche.md`, coller le texte exact d'une page officielle,
  puis `python -m scripts.validate_raw` et `python -m scripts.build_index`.
- Désactiver une fiche obsolète : `status: inactive` dans son en-tête, puis reconstruire l'index.
