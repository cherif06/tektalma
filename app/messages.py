"""Messages fixes. ⚠️ Faire relire les phrases en wolof par un locuteur de l'équipe."""

MESSAGES = {
    "out_of_domain": {
        "fr": "Je suis spécialisé dans les démarches administratives au Sénégal "
              "(carte d'identité, passeport, état civil…). Je ne peux pas vous aider sur ce sujet.",
        "wo": "Man, démarches administratives yi ci Senegaal rekk laa jëmu "
              "(carte d'identité, passeport, état civil…). Mënuma la dimbali ci loolu.",
        "en": "I specialise in administrative procedures in Senegal "
              "(ID card, passport, civil status…). I can't help with this topic.",
    },
    "no_info": {
        "fr": "Je n'ai pas trouvé suffisamment d'informations officielles pour répondre avec "
              "certitude. Je vous conseille de consulter le portail officiel e-senegal.sn "
              "ou l'administration concernée.",
        "wo": "Gisuma xibaar yu officiel yu doy ngir tontu la ak kóolute. "
              "Dafa gën nga seet ci e-senegal.sn walla nga laaj administration bi ko yor.",
        "en": "I couldn't find enough official information to answer with certainty. "
              "Please check the official portal e-senegal.sn or the relevant administration.",
    },
    "error": {
        "fr": "Le service est momentanément indisponible. Réessayez dans un instant.",
        "wo": "Service bi dafa jàpp ab diir. Jéemaatal ci kanam tuuti.",
        "en": "The service is temporarily unavailable. Please try again in a moment.",
    },
    "sources_intro": {
        "fr": "Ma réponse précédente s'appuie sur ces sources officielles :",
        "wo": "Sama tontu bi, ci sources officielles yii la jóge :",
        "en": "My previous answer is based on these official sources:",
    },
    "no_sources_yet": {
        "fr": "Je n'ai pas encore donné de réponse basée sur des sources dans cette conversation.",
        "wo": "Tontuguma dara ci sources yet ci waxtaan bii.",
        "en": "I haven't given a source-based answer in this conversation yet.",
    },
}


def msg(key: str, lang: str) -> str:
    return MESSAGES[key].get(lang, MESSAGES[key]["fr"])
