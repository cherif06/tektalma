# 🇸🇳 TEKTALMA AI

Assistant vocal des démarches administratives au Sénégal (français · wolof · anglais),
basé sur un RAG qui répond **uniquement** à partir de sources officielles.

## Lancer (Windows / PyCharm, depuis la racine du projet)
```
pip install -r requirements.txt
python -m scripts.validate_raw      # vérifie les fiches officielles
python -m scripts.build_index       # construit l'index (à faire avant la démo)
streamlit run app/streamlit_app.py  # lance l'interface
python -m scripts.eval_rag          # évaluation + calibrage du seuil
```

## Architecture
Question (voix/texte) → transcription Gemini → compréhension (langue, intention,
reformulation en français) → recherche hybride ChromaDB + BM25 (fusion RRF) →
seuil de confiance → génération Gemini à partir des fiches → garde-fous
(citations valides, chiffres présents dans les sources) → réponse + sources → voix.

## Ajouter ou désactiver une démarche
- Ajouter : copier `data/raw/_modele/MODELE_fiche.md`, coller le texte exact d'une page officielle,
  puis `python -m scripts.validate_raw` et `python -m scripts.build_index`.
- Désactiver une fiche obsolète : `status: inactive` dans son en-tête, puis reconstruire l'index.
