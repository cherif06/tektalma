from app.guards import check_numbers, clean_citations, keep_language, looks_wolof


def test_citation_inexistante_retiree():
    text, used = clean_citations("Le coût est fixé [S1]. Autre point [S7].", n_sources=2)
    assert "[S7]" not in text and "[S1]" in text
    assert used == [1]


def test_chiffre_invente_supprime():
    context = "Le timbre coûte 500 FCFA. Valable 10 ans."
    text, removed = check_numbers("Le timbre coûte 500 FCFA [S1]. Le délai est de 48 heures [S1].", context)
    assert "500" in text
    assert "48" not in text and removed


def test_liste_numerotee_conservee():
    text, _ = check_numbers("1. Aller au commissariat.\n2. Payer 500 FCFA.", "500 FCFA")
    assert text.startswith("1.") and "2. Payer 500 FCFA." in text


def test_detection_wolof():
    assert looks_wolof("Dafay jël ñaari fan.")
    assert not looks_wolof("La carte est valable 10 ans.")
    assert keep_language("La carte est valable. Dafay jël ñaari fan.", "fr") == "La carte est valable."
