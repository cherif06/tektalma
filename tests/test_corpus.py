from app.corpus import load_fiches

REQUIRED = ("title", "organisme", "url", "category", "collected_at")


def test_fiches_completes():
    fiches = load_fiches()
    assert fiches, "aucune fiche active"
    for f in fiches:
        for key in REQUIRED:
            assert f["meta"].get(key), f"{f['doc_id']} : champ '{key}' manquant"
        assert str(f["meta"]["url"]).startswith("https://")
