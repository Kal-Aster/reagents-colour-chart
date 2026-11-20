"""Dai nomi dei colori delle fonti ai colori della palette.

Le fonti nominano i colori a parole: "Pink-orange" (NIST CADS), "Dark reddish
brown" (i nomi ISCC-NBS del NIJ), "Broom yellow" (i nomi RAL di Chang et al.).
La pagina invece ha una palette di famiglie, ognuna in tre tinte:
"red.light", "red.standard", "red.dark".

Un nome diventa una o piu' alternative, una per famiglia che nomina, con le
stesse regole del testo di PsychonautWiki in extract_psychonautwiki.py:

- un composto vale per tutte le sue famiglie: "Pink-orange" e' rosa oppure
  arancione, cosi' chi ha visto rosa lo trova e chi ha visto arancione pure;
- "-ish" aggiunge la sua famiglia: "reddish brown" e' rosso oppure marrone;
- "olive" e' verde;
- "light", "pale" danno la tinta chiara, "dark", "deep" quella scura, il
  resto quella standard.

I grigi sono una famiglia sola, "gray", che va dal grigio al nero: "grey" e'
gray.light, "dark grey" e "greyish black" gray.standard, "black" gray.dark.

Una parola che lo script non conosce ferma l'estrazione: un colore nuovo va
deciso a mano, non indovinato.
"""
from __future__ import annotations

import re

# parola -> famiglie della palette
HUE_WORDS = {
    "red": ["red"],
    "orange": ["orange"],
    "yellow": ["yellow"],
    "green": ["green"],
    "blue": ["blue"],
    "purple": ["purple"],
    "violet": ["purple"],
    "pink": ["pink"],
    "brown": ["brown"],
    "olive": ["green"],
    "wine": ["red", "purple"],
    # i nomi del catalogo RAL che non sono una famiglia
    "vermillion": ["red", "orange"],
    "vermilion": ["red", "orange"],
    "beige": ["yellow", "brown"],
}
# "-ish": aggiunge la sua famiglia a quella del nome
ISH_WORDS = {
    "reddish": "red",
    "orangish": "orange",
    "yellowish": "yellow",
    "greenish": "green",
    "bluish": "blue",
    "purplish": "purple",
    "pinkish": "pink",
    "brownish": "brown",
}
BLACK_WORDS = {"black", "blackish"}
GREY_WORDS = {"grey", "gray"}
# il grigio davanti a un'altra famiglia ne spegne il colore, non ne aggiunge una
GREYISH_WORDS = {"greyish", "grayish"}
GRAY = "gray"
SHADE_WORDS = {
    "light": "light",
    "pale": "light",
    "faint": "light",
    "dark": "dark",
    "deep": "dark",
    "blackish": "dark",
    # i nomi RAL che sono tinte scure della loro famiglia
    "claret": "dark",
    "curry": "dark",
    "sapphire": "dark",
}
# parole che non cambiano ne' la famiglia ne' la tinta: l'intensita' ISCC-NBS
# (strong, brilliant...) e i nomi RAL che sono solo nomi (broom yellow)
NEUTRAL_WORDS = {"strong", "moderate", "brilliant", "vivid", "very", "jet", "broom",
                 "lemon", "pearl"}


def palette_colours(name: str) -> list[str]:
    """Le alternative che un nome di colore indica, come colori della palette.

    >>> palette_colours("Pink-orange")
    ['pink.standard', 'orange.standard']
    >>> palette_colours("Dark reddish brown")
    ['red.dark', 'brown.dark']
    """
    words = [word for word in re.split(r"[\s\-‐‑]+", name.strip().lower()) if word]
    hyphenated = bool(re.search(r"[\-‐‑]", name))
    shade = "standard"
    families: list[str] = []
    black = grey = greyish = False
    for index, word in enumerate(words):
        if word in SHADE_WORDS:
            shade = SHADE_WORDS[word]
        if word in HUE_WORDS:
            families.extend(HUE_WORDS[word])
        elif word in ISH_WORDS:
            families.append(ISH_WORDS[word])
        elif word in BLACK_WORDS:
            black = True
        elif word in GREY_WORDS:
            # grigio come colore a se': da solo, in un composto o in fondo
            # ("Blue-grey"); davanti a un'altra famiglia ("Gray purplish blue")
            # e' solo una tinta spenta, davanti al nero lo schiarisce
            if hyphenated or index == len(words) - 1:
                grey = True
            else:
                greyish = True
        elif word in GREYISH_WORDS:
            greyish = True
        elif word not in SHADE_WORDS and word not in NEUTRAL_WORDS:
            raise ValueError(f"colore sconosciuto: {word!r} in {name!r}")
    alternatives = [f"{family}.{shade}" for family in dict.fromkeys(families)]
    if black:
        # il nero; ingrigito ("greyish black") o chiaro e' il grigio scuro
        lighter = greyish or grey or shade == "light"
        alternatives.append(f"{GRAY}.{'standard' if lighter else 'dark'}")
    elif grey:
        # il grigio; scuro e' il grigio scuro
        alternatives.append(f"{GRAY}.{'standard' if shade == 'dark' else 'light'}")
    if not alternatives:
        raise ValueError(f"nessun colore in {name!r}")
    return alternatives
