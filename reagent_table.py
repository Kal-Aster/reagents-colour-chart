#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reagent_table.py - pipeline unica della matrice sostanza x reattivo.

Scarica i dati semantici da PsychonautWiki (CC BY 4.0), li normalizza e li salva;
con --html esporta anche la tabella visuale.

    python3 reagent_table.py            # scarica, normalizza, salva i dati
    python3 reagent_table.py --html     # ... ed esporta anche index.html
    python3 reagent_table.py --offline  # non riscarica: riusa il data.json locale
    python3 reagent_table.py --check    # verifica le uscite (exit 1 se non tornano)

Uscite:
    data.json                                dataset normalizzato (con provenienza e licenza dentro)
    psychonautwiki_reagenti_sostanze.csv    formato lungo: una riga per record
    index.html                               la tabella visuale (solo con --html)

Nessun effetto collaterale all'import: i file si scrivono solo quando main() gira.
"""
import argparse, csv, html, json, os, re, sys, time, urllib.request

# === SEZIONE 0 - CONFIG ==========================================================
API = "https://api.psychonautwiki.org/"
# I percorsi di default sono relativi allo script: funziona da qualunque cartella
# e su qualunque macchina (i percorsi si sovrascrivono con --data/--csv/--html/--schema).
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.join(HERE, "data.json")
DEFAULT_CSV = os.path.join(HERE, "psychonautwiki_reagenti_sostanze.csv")
DEFAULT_HTML = os.path.join(HERE, "index.html")
DEFAULT_SCHEMA = os.path.join(HERE, "psychonautwiki_schema.json")


def ensure_dir(path):
    """Crea la cartella di destinazione, se il percorso ne ha una."""
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]

# intestazione unica: la usa sia il writer Python sia l'export CSV del browser
CSV_COLUMNS = ["sostanza", "alias", "reattivo", "reattivo_full", "descrizione", "forma",
               "dinamica", "variante", "is_positive", "sequenza_temporale", "n_fasi",
               "n_percorsi", "struttura", "percorsi", "colore_testo_iniziale",
               "colore_testo_finale", "toni_registrati_grezzi", "sequenza_canonica",
               "url_psychonautwiki"]

# stato letto da load_state(): le funzioni lo usano, ma all'import non e' nulla
D = None
RG, COLORS, SUBS = [], [], []
COL_BY_ID, COL_BY_HEX, COL_BY_FAM_TONE = {}, {}, {}
COL_FULL, COLS, RG_ORDER, cov, BASE_FAM = {}, [], [], {}, {}


def page_date(data):
    """La data dei dati (dalla marca di scaricamento), in italiano, per il pie' di pagina."""
    ts = (data or {}).get("fetchedAt") or ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", ts)
    if not m:
        return ""
    return "%d %s %s" % (int(m.group(3)), MESI[int(m.group(2)) - 1], m.group(1))


def load_state(data):
    """Carica il dataset normalizzato nello stato del modulo (palette, sostanze, colonne)."""
    global D, RG, COLORS, SUBS, COL_BY_ID, COL_BY_HEX, COL_BY_FAM_TONE
    global COL_FULL, COLS, RG_ORDER, cov, BASE_FAM
    D = data
    RG = D["reagents"]
    COLORS = D["colors"]
    SUBS = D["substances"]
    COL_BY_ID = {c["id"]: c for c in COLORS}
    COL_BY_HEX = {c["hex"]: c for c in COLORS}
    COL_BY_FAM_TONE = {}
    for _c in COLORS:
        COL_BY_FAM_TONE[(_c["name"].rstrip("123"), _c["name"][-1])] = _c
    cov = {r["shortName"]: 0 for r in RG}
    for s in SUBS:
        for c in s["cells"]:
            cov[c["reagent"]] = cov.get(c["reagent"], 0) + 1
    RG_ORDER = sorted(RG, key=lambda r: (-cov.get(r["shortName"], 0), r["fullName"]))
    COLS = [r["shortName"] for r in RG_ORDER]
    COL_FULL = {r["shortName"]: r["fullName"] for r in RG}
    BASE_FAM = compute_base_families()


# === SEZIONE 1 - FETCH (la rete) ================================================


def gql(query, variables=None):
    """Una query GraphQL all'API semantica di PsychonautWiki, con retry."""
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "User-Agent": "research-dataset-builder/1.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))


SUB_Q = """
query S($limit: Int, $offset: Int) {
  substances(limit: $limit, offset: $offset) {
    name url
    commonNames
    class { chemical psychoactive }
    reagents {
      substanceName rawName
      results {
        reagent { id fullName shortName }
        description isPositive
        startColors { id name hex simple simpleColorId }
        endColors   { id name hex simple simpleColorId }
      }
    }
  }
}
"""

REAG_Q = "{ reagents { id fullName shortName whiteFirstColor } }"
COLOR_Q = "{ reagentColors { id name hex simple simpleColorId } }"


def fetch_data():
    """Scarica e normalizza: il payload dell'API diventa il dataset (sostanze x reattivi)."""
    reagents = gql(REAG_Q)["data"]["reagents"]
    colors = gql(COLOR_Q)["data"]["reagentColors"]
    print("reattivi:", len(reagents), "| colori:", len(colors))

    subs, offset, limit = [], 0, 100
    while True:
        d = gql(SUB_Q, {"limit": limit, "offset": offset})
        chunk = d.get("data", {}).get("substances") or []
        if not chunk:
            break
        subs.extend(chunk)
        offset += limit
        if len(chunk) < limit or offset > 2000:
            break
    print("sostanze enumerate:", len(subs))

    rows = []
    for s in subs:
        rg = s.get("reagents") or {}
        results = rg.get("results") or []
        if not results:
            continue
        cells = []
        for r in results:
            cells.append({
                "reagentId": r["reagent"]["id"],
                "reagent": r["reagent"]["shortName"] or r["reagent"]["fullName"],
                "desc": (r.get("description") or "").strip(),
                "positive": r.get("isPositive"),
                "start": [{"name": c["name"], "hex": c["hex"], "simple": c.get("simple")}
                          for c in (r.get("startColors") or [])],
                "end": [{"name": c["name"], "hex": c["hex"], "simple": c.get("simple")}
                        for c in (r.get("endColors") or [])],
            })
        rows.append({
            "name": s["name"],
            "url": s.get("url"),
            "rawName": rg.get("rawName"),
            "substanceName": rg.get("substanceName"),
            "commonNames": s.get("commonNames") or [],
            "class": s.get("class") or {},
            "cells": cells,
        })

    return {
        "source": "PsychonautWiki semantic data via GraphQL API (https://api.psychonautwiki.org/)",
        "license": "CC BY 4.0 (semantic data)",
        "fetchedAt": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "reagents": reagents,
        "colors": colors,
        "substances": rows,
    }


def save_data(data, path):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    pairs = sum(len(r["cells"]) for r in data["substances"])
    print("scritto:", path, "| sostanze con dati:", len(data["substances"]), "| coppie:", pairs)


# === SEZIONE 2 - PARSER DELLE DESCRIZIONI ======================================
# -*- coding: utf-8 -*-
"""Parser delle descrizioni: testo -> fasi, e dentro ogni fase -> gruppi di colori con operatore.

Il testo della fonte e' prosa libera: contiene sfumature ("faint blue"), composti
("reddish purple", "orange - green"), scorciatoie tra parentesi ("(orange) red"),
sostantivi di forma ("black spots") e refusi. Qui viene ridotto a una struttura:
fasi (separate da ">") -> gruppi di colori, con l'operatore che li lega
(and/with = simultanei, or// = alternative).
"""
import json, re
from collections import Counter

FAMS = ["black", "blue", "green", "yellow", "orange", "brown", "red", "pink", "purple", "violet"]
MODS = ["dark", "light", "pale", "faint", "slow", "instant", "deep", "bright", "reddish", "yellowish",
        "brownish", "blackish", "greenish", "bluish", "purpleish", "pinkish", "olive", "slight",
        "neon", "sea", "very", "partial", "short", "greenish", "purple", "orange", "yellow", "red",
        "brown", "black", "blue", "pink"]

FAM_LIST = ["reddish", "purplish", "orangeish", "orangish", "orangy", "orange", "black", "blue",
            "green", "yellow", "brown", "red", "pink", "purple", "violet", "grey", "gray",
            "wine", "tan", "olive"]
FAMWORD = r"(?:%s)" % "|".join(FAM_LIST)
FAMCAP = r"(%s)" % "|".join(FAM_LIST)

# parole che il testo usa ma che non sono colori: restano nel testo della menzione
# senza influire sulla scelta del campione
EXTRA_MODS = (r"(?:rusty|salmon|turquoise|fizzes|fizz(?:es)?|dissappear\w*|dissipating|"
              r"just|possible|brief|weak|turns?|instantly|turning)")
MODWORD = (r"(?:no|dark|light|pale|faint|slow|instant|deep|bright|reddish|yellowish|brownish|"
           r"blackish|greenish|bluish|purpleish|pinkish|olive|slight|neon|sea|very|partial|short|"
           r"deep|" + EXTRA_MODS + r")")

# refusi della fonte, normalizzati solo per il parsing (il testo resta quello originale)
TYPOS = [(r"\bfain\b", "faint"), (r"\bdakr\b", "dark"), (r"\bdissapear\w*", "dissappearing"),
         (r"\breddisch\b", "reddish"), (r"\bfizze?s\b", "fizzes")]

ISH_SUFFIX = {"orangeish": "orange", "orangy": "orange"}
# suffisso -ish: la parola aggiunge una famiglia alla menzione ("reddish purple" = rosso + viola)
ISH_ADD = {"reddish": "red", "yellowish": "yellow", "brownish": "brown", "blackish": "black",
           "greenish": "green", "bluish": "blue", "purpleish": "purple", "pinkish": "pink",
           "orangeish": "orange", "violetish": "purple"}
SHADE = {"light", "dark", "pale", "faint", "bright", "slight", "very", "deep", "neon",
         "partial", "instant", "slow", "no", "short", "olive", "weak"}

# parole di forma citate dalla fonte
FORMS = {"spots": "macchie", "spot": "macchie", "streaks": "strisce", "streak": "strisce",
         "ring": "anello", "particles": "particelle", "particle": "particelle",
         "clouds": "nubi", "cloud": "nubi", "precipitate": "precipitato",
         "precipitates": "precipitato", "dots": "punti", "dot": "punti"}

# la fonte abbrevia i composti anche con parentesi: "(orange) red", "Brown-Green (yellow)"
PAREN_COL = re.compile(r"\(\s*%s\s*\)" % FAMCAP, re.I)


def strip_index(desc):
    return re.sub(r"\s*\(\d+\)\s*$", "", desc or "").strip()


def normalize(text):
    t = text.strip()
    t = t.replace("->", ">").replace("→", ">").replace("–", "-").replace("—", "-")
    for pat, rep in TYPOS:
        t = re.sub(pat, rep, t, flags=re.I)
    # "deepgreen" -> "deep green" (modificatore attaccato al colore)
    t = re.sub(r"\b(deep|light|dark|pale|faint)(?=(?:black|blue|green|yellow|orange|brown|red|pink|purple|violet|grey|gray)\b)",
               r"\1 ", t, flags=re.I)
    t = re.sub(r"\s*>\s*", " > ", t)
    t = re.sub(r"\s*/\s*", " / ", t)
    t = re.sub(r"\band\b", " and ", t, flags=re.I)
    t = re.sub(r"\bwith\b", " with ", t, flags=re.I)
    t = re.sub(r"\bor\b", " or ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()


MENTION = re.compile(
    r"(?P<mods>(?:%s)\s+)*(?P<fam>%s)(?:ish)?\b(?P<noun>\s+(?:spots?|streaks?|ring|particles|clouds?|precipitate|dots?))?" % (MODWORD, FAMWORD),
    re.I)


def fam_to_families(fam, mods=()):
    """Famiglie di palette che una parola del testo puo' indicare."""
    fam = fam.lower()
    if fam in ("violet", "purplish"):
        fam = "purple"
    elif fam in ("reddish",):
        fam = "red"
    elif fam in ("orangeish", "orangish", "orangy"):
        fam = "orange"
    elif fam in ("grey", "gray"):
        fam = "black"
    elif fam == "wine":
        return ["red", "purple"]
    elif fam == "tan":
        return ["orange", "yellow"]
    elif fam == "olive":
        return ["green"]
    out = [fam]
    if "olive" in mods and "green" not in out:
        out.insert(0, "green")
    return out


def find_mentions(phase, allow_all=True):
    """Elenco di menzioni di colore: famiglia, modificatori, famiglie composite, posizione."""
    out = []
    for m in MENTION.finditer(phase):
        fam = m.group("fam").lower()
        mods = [x.lower() for x in (m.group("mods") or "").split()]
        raw = m.group(0)
        ish = raw.lower().rstrip(".").split()
        fams = fam_to_families(fam, mods)
        # "reddish purple" -> compound {red, purple}; "olive black" -> {green, black}
        for tok in ish:
            if tok in ISH_ADD and ISH_ADD[tok] not in fams:
                fams.insert(0, ISH_ADD[tok])
            elif tok in ISH_SUFFIX and ISH_SUFFIX[tok] not in fams:
                fams.insert(0, ISH_SUFFIX[tok])
        noun = (m.group("noun") or "").strip().lower()
        out.append({"fam": fam, "fams": list(dict.fromkeys(fams)), "mods": mods, "noun": noun,
                    "start": m.start(), "end": m.end(), "text": raw.strip()})
    # unifica i composti con trattino ("red-orange", "orange - green" -> una sola menzione)
    merged = []
    for m in out:
        if merged:
            prev = merged[-1]
            between = phase[prev["end"]:m["start"]]
            if between.strip() == "-":
                prev["fams"] = list(dict.fromkeys(prev["fams"] + m["fams"]))
                prev["text"] = (prev["text"] + "-" + m["text"]).strip()
                prev["end"] = m["end"]
                prev["compound"] = True
                continue
        merged.append(m)
    return merged


def parse(desc):
    """-> {'phases': [ {'groups': [ {'op': 'sim'|'alt', 'colors':[...] } ] } ]}"""
    txt = normalize(strip_index(desc))
    if not txt:
        return {"phases": [], "raw": txt}
    phases = []
    for ph in txt.split(" > "):
        # i colori tra parentesi sono alternative della fase: "(orange) red"
        paren = []

        def _take(m):
            paren.append((m.group(1).lower(), m.start()))
            return " "

        ph = PAREN_COL.sub(_take, ph)
        negative = bool(re.match(r"^\s*(?:no|none|clear)\b", ph, re.I))
        if negative and paren:
            negative = False              # il colore tra parentesi e' il risultato
        if negative and " / " in ph:
            ph = ph.split(" / ", 1)[1]      # "no change / faint yellow" -> resta la parte con colore
        elif negative and " or " in ph:
            ph = ph.split(" or ", 1)[1]      # "clear or grey" -> resta la parte con colore
        elif negative:
            ph = ""                        # "no blue color change" -> nessun colore risultante
        mentions = find_mentions(ph)
        groups, i = [], 0
        while i < len(mentions):
            grp = [mentions[i]]
            op = "single"
            while i + 1 < len(mentions):
                between = ph[grp[-1]["end"]:mentions[i + 1]["start"]].lower()
                if " and " in between or " with " in between:
                    # "and"/"with" dentro UNA fase = colori che coesistono ("sim"):
                    # "yellow with black spots", "reddish with grey dots".
                    # Da non confondere con l'"AND" fra DUE osservazioni della stessa
                    # cella ("red AND green > brown", 25B/25C/25D-NBOMe Mandelin):
                    # li' nessun record registra entrambi i colori, quindi non sono
                    # simultanei e il rendering apre due percorsi paralleli.
                    # Vedi build_html.py, cell_html() (commento con la citazione
                    # Clancy 2021 / tesi Clancy 2022: per gli NBOMe i reattivi
                    # standard danno "a range of different colours").
                    nxt = "sim"
                elif " / " in between or " or " in between:
                    nxt = "alt"
                else:
                    break
                op = nxt
                grp.append(mentions[i + 1])
                i += 1
            groups.append({"op": op, "colors": grp})
            i += 1
        # i colori tra parentesi entrano come alternative nello stesso gruppo
        for word, pos in paren:
            fams = fam_to_families(word)
            m = {"fam": fams[0], "fams": fams, "mods": [], "noun": "", "start": pos, "end": pos,
                 "text": word}
            if groups:
                groups[0]["op"] = "alt"
                groups[0]["colors"].append(m)
                groups[0]["colors"].sort(key=lambda x: x["start"])
            else:
                groups.append({"op": "single", "colors": [m]})
        phases.append({"groups": groups, "text": ph})
    return {"phases": phases, "raw": txt}


def cell_forms(desc):
    """Forme citate nella descrizione: 'macchie', 'precipitato', 'anello'."""
    out = []
    for m in re.finditer(r"\b(spots?|streaks?|ring|particles|clouds?|precipitates?|dots?)\b",
                         (desc or "").lower()):
        lab = FORMS.get(m.group(1))
        if lab and lab not in out:
            out.append(lab)
    return ";".join(out)



# === SEZIONE 3 - MODELLO (la semantica dei dati) ===============================

def canon_hex(h):
    col = COL_BY_HEX.get(h)
    if not col:
        return h
    tgt = COL_BY_ID.get(col.get("simpleColorId"))
    return tgt["hex"] if tgt else h


def esc(s):
    return html.escape(s or "", quote=True)


def fmt_desc(t):
    """Formatta la descrizione: '>' evidenziato, frasi negative in corsivo, indice in grigio."""
    t = esc(t)
    t = t.replace(" &gt; ", " <span class='gt'>&gt;</span> ")
    low = t.lower()
    for n in NEG:
        if n in low:
            i = low.find(n)
            t = t[:i] + "<em class='neg'>" + t[i:i + len(n)] + "</em>" + t[i + len(n):]
            low = t.lower()
    # indice finale (nn)
    if t.rstrip().endswith(")"):
        j = t.rstrip().rfind("(")
        if j > 0:
            t = t[:j] + "<span class='idx' title='Indice di provenienza della riga di riferimento, non un tempo'>" + t[j:] + "</span>"
    return t


FAMWORDS = [("black", "black"), ("blue", "blue"), ("green", "green"), ("yellow", "yellow"),
            ("orange", "orange"), ("brown", "brown"), ("red", "red"), ("pink", "pink"),
            ("violet", "purple"), ("purple", "purple")]


def final_families(desc):
    """Famiglie di colore citate dal testo DOPO l'ultimo '>' (il 'finale' dichiarato dalla fonte)."""
    if ">" not in desc:
        return set()
    tail = re.sub(r"\s*\(\d+\)\s*$", "", desc).split(">")[-1].lower()
    out = set()
    for word, fam in FAMWORDS:
        if word in tail:
            out.add(fam)
    return out


ARROW = ("<svg class='farrow' viewBox='0 0 24 24' width='10' height='10' fill='none' stroke='currentColor' "
         "stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'><path d='M9 5l7 7-7 7'/></svg>")


def fam_of(h):
    c = COL_BY_HEX.get(h)
    return c["name"].rstrip("123") if c else ""


NEG = ("no color change", "no instant reaction", "no change", "no reaction",
       "no pink color change", "no blue color change", "no green", "none")


def compute_base_families():
    """REGOLA #1 - il colore proprio del reattivo.

    Nei reattivi che hanno un colore proprio (whiteFirstColor None) il primo campione
    registrato e' quello del reattivo, non un risultato della reazione: e' la "prima
    osservazione" della cella, sia che il testo lo nomini sia che non lo nomini.
    La famiglia del colore proprio e' quella del primo campione nella maggioranza
    delle celle del reattivo (verificato sul corpus):
      Mandelin giallo 134/134 | Morris rosa 59/59 | Scott rosa 7/7
      Simon's arancio 40/46 (nelle altre 6 il primo campione e' gia' un risultato:
      la fonte non ha registrato il colore del reattivo -> non se lo invento)
    """
    out = {}
    for r in RG:
        if r.get("whiteFirstColor") is not None:
            continue
        cnt = {}
        for s in SUBS:
            for c in s["cells"]:
                if c["reagent"] == r["shortName"] and c["start"]:
                    f = fam_of(canon_hex(c["start"][0]["hex"]))
                    cnt[f] = cnt.get(f, 0) + 1
        if not cnt:
            continue
        f, n = max(cnt.items(), key=lambda kv: kv[1])
        if n / sum(cnt.values()) >= 0.6:
            out[r["shortName"]] = f
    return out


def std_color(fam):
    for c in COLORS:
        if c["name"].rstrip("123") == fam and c.get("simple"):
            return c
    for c in COLORS:
        if c["name"].rstrip("123") == fam:
            return c
    return None


# La sfumatura nel testo ("faint blue", "dark brown") dice quale tonalita' della
# famiglia intendeva la fonte. Ordini di preferenza verificati sul corpus:
# light/pale/faint/slight/weak -> 1, dark/deep -> 3, nessuna sfumatura -> 2 (tono standard).
TONE_PREF_LIGHT = ["1", "2", "3"]
TONE_PREF_DARK = ["3", "2", "1"]
TONE_PREF_NONE = ["2", "1", "3"]
TONE_PREF_WORDS = {"light": TONE_PREF_LIGHT, "pale": TONE_PREF_LIGHT, "faint": TONE_PREF_LIGHT,
                   "slight": TONE_PREF_LIGHT, "weak": TONE_PREF_LIGHT,
                   "dark": TONE_PREF_DARK, "deep": TONE_PREF_DARK}


# Marcatori di una reazione che cambia nel tempo senza passaggi espliciti.
# "dissappearing yellow" / "dissipating reddish": il colore citato svanisce.
DYN_FADE = {"dissappearing", "disappearing", "dissipating", "fading", "fades", "vanishing"}
DYN_OTHER = {"fizzes"}


def missing_color(fam, mods=(), mode="full"):
    """Colore con cui disegnare un campione che il testo nomina ma che non e' stato
    osservato: la famiglia alla tonalita' che la sfumatura implica (o quella standard)."""
    if mode == "std":
        return std_color(fam)
    for t in tone_pref(list(mods) or []):
        c = COL_BY_FAM_TONE.get((fam, t))
        if c:
            return c
    return std_color(fam)


def tone_pref(mods):
    for mod in mods or []:
        p = TONE_PREF_WORDS.get(str(mod).lower())
        if p:
            return p
    return TONE_PREF_NONE

def alias_of(s):
    """Il nome grezzo della sostanza, quando diverso da quello canonico."""
    raw = (s.get("rawName") or "").strip()
    if raw and raw.lower() != s["name"].lower():
        base = raw.split(" (")[0]
        if base.lower() != s["name"].lower():
            return raw
    return ""


def cell_model(cell):
    """Struttura della cella: fasi (dal testo), operatori, abbinamento dei campioni registrati.

    Tre regole, verificate sul corpus:

    1) REGOLA #1 - il colore proprio del reattivo (Mandelin giallo, Morris e Scott
       rosa, Simon's arancio) e' SEMPRE la prima osservazione della cella, anche
       quando il testo lo cita: resta il campino iniziale, e se il testo lo cita
       in una fase successiva quella fase si aggancia al campione successivo
       (il ritorno al colore di prima).
    2) Una ripetizione CONSECUTIVA dello stesso campione e' un duplicato (una sola
       osservazione); una ripetizione NON consecutiva e' un ritorno al colore di
       prima e viene conservata.
    3) REGOLA #2 - il registro fa la spina dorsale: i campioni sono la sequenza
       osservata. I percorsi paralleli si aprono SOLO dove il testo scrive
       un'alternativa esplicita ("/" o "or"): un composto ("reddish purple") o
       un campione che il testo non nomina non aprono un percorso a se'.
    """
    p = parse(cell["desc"])
    sib = cell.get("_sib") or set()
    raw = cell["start"]
    base = BASE_FAM.get(cell["reagent"])
    # --- i campioni registrati: una ripetizione consecutiva e' un duplicato ---
    tones = []
    for t in raw:
        if tones and tones[-1]["hex"] == t["hex"]:
            continue
        tones.append(t)
    # --- regola #1: il colore proprio del reattivo e' riservato come prima osservazione
    init_idx = None
    if base and tones and fam_of(canon_hex(tones[0]["hex"])) == base:
        init_idx = 0
    used = [False] * len(tones)
    phases = []
    mention_phase = []          # fase in cui cade ogni menzione, nell'ordine
    mention_list = []           # le menzioni, nell'ordine in cui sono abbinate
    sample_men = {}             # indice del campione -> ordinal della menzione
    ordinal = 0
    for pi, ph in enumerate(p["phases"]):
        groups = []
        for g in ph["groups"]:
            mentions = []
            for m in g["colors"]:
                mt = []
                pref = tone_pref(m.get("mods", []))
                for f in m["fams"]:
                    cand = [i for i, t in enumerate(tones)
                            if not used[i] and i != init_idx and fam_of(canon_hex(t["hex"])) == f]
                    if not cand:
                        continue
                    # la sfumatura del testo decide quale tonalita' e' quella citata
                    cand.sort(key=lambda i: pref.index(tones[i]["name"][-1])
                              if tones[i]["name"][-1] in pref else 9)
                    i = cand[0]
                    mt.append(tones[i]); used[i] = True; sample_men[i] = ordinal
                mentions.append({"text": m["text"], "fams": m["fams"], "tones": mt,
                                 "mods": m.get("mods", []), "noun": m.get("noun", "")})
                mention_phase.append(pi)
                mention_list.append(mentions[-1])
                ordinal += 1
            keep = []
            for m in mentions:
                got = {fam_of(canon_hex(t["hex"])) for t in m["tones"]}
                m["missing"] = [f for f in m["fams"] if f not in got]
                # la menzione nomina il colore proprio del reattivo: quello e' il
                # campino iniziale, non un colore mancante (regola #1)
                if init_idx == 0 and m["missing"]:
                    init_fam = fam_of(canon_hex(tones[0]["hex"]))
                    rest = []
                    for f in m["missing"]:
                        if f == init_fam and pi == 0:
                            m["init_label"] = True
                        else:
                            rest.append(f)
                    m["missing"] = rest
                # se lo stesso colore e' registrato da un altro record della stessa
                # fonte, qui non e' "mancante": lo registra quell'altro record
                if sib and m["missing"]:
                    sup = [f for f in m["missing"] if f in sib]
                    rest = [f for f in m["missing"] if f not in sib]
                    if sup:
                        m["suppressed"] = sup
                        m["missing"] = rest
                        if not rest and not m["tones"]:
                            continue
                keep.append(m)
            if keep:
                groups.append({"op": g["op"], "mentions": keep})
        phases.append({"groups": groups})
    free = [(i, t) for i, t in enumerate(tones) if not used[i]]
    # i reattivi senza colore proprio: la prima osservazione e' il campino
    # iniziale solo se il testo non la nomina
    if init_idx is None and tones and not used[0]:
        init_idx = 0
    initial = tones[init_idx] if init_idx is not None else None
    if initial is not None:
        free = [(i, t) for i, t in free if i != init_idx]
    # la menzione che nomina il colore proprio del reattivo nella prima fase
    # etichetta il campino iniziale
    init_label = ""
    for ph in phases:
        for g in ph["groups"]:
            for m in g["mentions"]:
                if m.get("init_label"):
                    init_label = m["text"]
    # i campioni registrati che il testo non descrive appartengono alla fase in cui il
    # registro li colloca: quella del campione abbinato che li precede
    undoc = {}
    for i, t in free:
        prev = [j for j in sample_men if j < i]
        ph_i = mention_phase[sample_men[max(prev)]] if prev else 0
        undoc.setdefault(ph_i, []).append(t)
    final_fam = None
    if len(phases) > 1:
        last = [m for g in phases[-1]["groups"] for m in g["mentions"]]
        if last:
            final_fam = last[-1]["fams"][0]
    # marcatore dinamico: il colore che svanisce, con la traiettoria dei campioni
    dyn = None
    for ph in p["phases"]:
        for g in ph["groups"]:
            for m in g["colors"]:
                mods = [x.lower() for x in m.get("mods", [])]
                if any(x in DYN_FADE for x in mods):
                    dyn = {"fade_fam": m["fams"][0], "text": m["text"], "mods": mods}
    # "fizzes" non e' uno svanimento: resta solo un'osservazione dinamica
    # "foaming" e "bubbling" sono la stessa reazione che sbuffa: la parola cambia,
    # il marcatore no (il dato ne conta 20 record, non 10)
    fizz = bool(re.search(r"\b(fizz\w*|foam\w*|bubbl\w*)", cell.get("desc", ""), re.I))
    dynamic = None
    if dyn is not None:
        traj = list(raw)                      # il registro completo, nell'ordine
        fade_idx = None
        if dyn["fade_fam"]:
            for i, t in enumerate(traj):
                if fam_of(canon_hex(t["hex"])) == dyn["fade_fam"]:
                    fade_idx = i
                    break
        last_fam = fam_of(canon_hex(traj[-1]["hex"])) if traj else None
        # il colore finale e' noto solo se l'ultimo campione non e' lo stesso
        # colore che svanisce: altrimenti resta sconosciuto
        final_unknown = bool(dyn["fade_fam"] and last_fam == dyn["fade_fam"])
        dynamic = {"traj": traj, "fade_idx": fade_idx, "fade_fam": dyn["fade_fam"],
                   "final_unknown": final_unknown, "text": dyn["text"], "mods": dyn["mods"],
                   "marker": "svanisce"}
    # --- regola #2: alternative esplicite -> percorsi paralleli; altrimenti
    # il registro fa la spina dorsale della cella
    has_alt = any(g["op"] == "alt" and len(g["mentions"]) > 1
                  for ph in phases for g in ph["groups"])
    chain = None
    if not has_alt and not dynamic:
        chain = []
        prev_phase = 0
        for i, t in enumerate(tones):
            if i == init_idx:
                continue
            om = sample_men.get(i)
            m = mention_list[om] if om is not None else None
            ph_i = mention_phase[om] if om is not None else prev_phase
            if om is not None:
                prev_phase = ph_i
            chain.append({"kind": "tone", "tone": t, "mention": m,
                          "undoc": m is None, "phase": ph_i})
        # i colori citati dal testo ma non registrati entrano nella posizione
        # della fase che li nomina
        for ph_i, ph in enumerate(phases):
            for g in ph["groups"]:
                for m in g["mentions"]:
                    for f in (m.get("missing") or []):
                        pos = len(chain)
                        for k, st in enumerate(chain):
                            if st["phase"] > ph_i:
                                pos = k
                                break
                        chain.insert(pos, {"kind": "missing", "fam": f,
                                           "mods": m.get("mods", []), "phase": ph_i,
                                           "text": m.get("text", "")})
    return {"phases": phases, "initial": initial, "extras": [] if chain is not None else [t for _, t in free],
            "undoc": undoc, "final_fam": final_fam, "n_raw": len(raw), "n_uniq": len(tones),
            "dynamic": dynamic, "fizz": fizz, "chain": chain, "has_alt": has_alt,
            "init_label": init_label}


ARROW_INIT = ("<svg class='farrow init' viewBox='0 0 24 24' width='10' height='10' fill='none' stroke='currentColor' "
              "stroke-width='2.6' stroke-linecap='round' stroke-linejoin='round'><path d='M9 5l7 7-7 7'/></svg>")


FAM_IT = {"black": "nero", "blue": "blu", "green": "verde", "yellow": "giallo",
          "orange": "arancio", "brown": "marrone", "red": "rosso", "pink": "rosa",
          "purple": "viola"}


def branches_for(g, m):
    """Un composto ("reddish purple") apre un ramo per ciascuna famiglia citata.
    Le famiglie registrate da un record fratello non aprono ramo qui: quel colore
    lo mostra l'altra osservazione."""
    if len(m["fams"]) > 1:
        sup = set(m.get("suppressed") or [])
        out = [fork_branch(g, m, fam=f) for f in m["fams"] if f not in sup]
        return out
    return [fork_branch(g, m)]


def fork_branch(g, m, fam=None):
    """Un ramo: la menzione intera, oppure il suo ramo di famiglia (composti)."""
    if fam is None:
        return {"op": "single", "mentions": [m], "forked": True}
    tones = [t for t in m.get("tones", []) if fam_of(canon_hex(t["hex"])) == fam]
    mm = {"text": m["text"], "fams": [fam], "tones": tones, "mods": m.get("mods", []),
          "noun": m.get("noun", ""), "missing": [] if tones else [fam], "compound": True}
    return {"op": "single", "mentions": [mm], "forked": True}


def build_tracks(mo):
    """Le alternative ('/' o 'or') aprono un ramo: la reazione si legge come percorsi paralleli."""
    tracks = [[]]
    for pi, ph in enumerate(mo["phases"]):
        shared = []
        choices = []
        undoc_here = mo["undoc"].get(pi, [])
        plain = []
        for g in ph["groups"]:
            if g["op"] == "sim":
                shared.append(g)                      # simultanei: stanno in ogni percorso
            elif g["op"] == "alt" and len(g["mentions"]) > 1:
                for m in g["mentions"]:
                    choices.extend(branches_for(g, m))
            elif len(g["mentions"]) == 1 and len(g["mentions"][0]["fams"]) > 1:
                # composto ("reddish purple"): un percorso per ciascuna famiglia citata
                m = g["mentions"][0]
                choices.extend(branches_for(g, m))
            else:
                plain.append(g)
        for t in undoc_here:
            choices.append({"op": "single", "undocumented": True,
                            "mentions": [{"text": t["name"],
                                          "fams": [fam_of(canon_hex(t["hex"]))],
                                          "tones": [t], "missing": [], "mods": []}]})
        if choices:
            # con alternative (o campioni non descritti) anche i gruppi semplici
            # diventano percorsi separati
            branches = [[g] for g in plain] + [[ch] for ch in choices]
        else:
            branches = [list(plain)] if plain else []
        # i colori simultanei stanno in ogni percorso
        branches = [list(shared) + br for br in branches]
        if not branches:
            branches = [list(shared)]
        new_tracks = []
        for tr in tracks:
            for br in branches:
                nt = list(tr)
                nt.append(br)
                new_tracks.append(nt)
        tracks = new_tracks
    return tracks


def render_group(g, mode):
    cls = "grp"
    if g.get("undocumented"):
        cls += " undoc"
    if g["op"] == "sim":
        cls += " sim"
    if g.get("forked"):
        cls += " forked"
    inner = []
    tail = []          # i marcatori stanno FUORI dal riquadro del gruppo
    mentions = [m for m in g["mentions"] if m.get("tones") or m.get("missing")]
    for mi, m in enumerate(mentions):
        if mi > 0:
            inner.append("<span class='fsym'>%s</span>" % ("+" if g["op"] == "sim" else " "))
        if mode == "full":
            for t in m["tones"]:
                sw_cls = "sw" + (" undoc" if g.get("undocumented") else "")
                inner.append("<i class='%s' style='background:%s' title='%s'></i>" % (
                    sw_cls, t["hex"], esc("%s %s" % (t["name"], t["hex"]))))
                if g.get("undocumented"):
                    tail.append("<span class='q' title='%s'>?</span>" % esc(
                        "campione registrato (%s %s) che il testo non descrive: esito alternativo "
                        "non documentato nella prosa" % (t["name"], t["hex"])))
            miss = m.get("missing") or ([] if m["tones"] else list(m["fams"]))
            for f in miss:
                # il campino e' colorato come il colore citato dal testo: si vede
                # quale manca senza scriverne il nome, che occuperebbe spazio
                col = missing_color(f, m.get("mods", []), mode)
                tip_miss = esc("%s: citato nel testo ma non presente nei campioni registrati"
                               % FAM_IT.get(f, f))
                inner.append("<i class='sw missing' style='background:%s' title='%s'></i>" % (
                    col["hex"] if col else "#e9ecf1", tip_miss))
                tail.append("<span class='miss' title='%s'><em>!</em></span>" % tip_miss)
        else:
            for f in [x for x in m["fams"] if x not in (m.get("suppressed") or [])]:
                c = std_color(f)
                if c:
                    inner.append("<i class='sw' style='background:%s' title='%s'></i>" % (
                        c["hex"], esc("%s %s" % (c["name"], c["hex"]))))
    tip = " · ".join(m["text"] for m in g["mentions"])
    return "<span class='%s' title='%s'>%s</span>%s" % (cls, esc(tip), "".join(inner), "".join(tail))


def render_dynamic(mo, mode):
    """Traiettoria di una reazione che svanisce: i campioni registrati in ordine,
    con la freccia fra le fasi e il riquadro tratteggiato se il finale non c'e'."""
    d = mo["dynamic"]
    traj = d["traj"]
    if not traj:
        return ""
    out = []
    for i, t in enumerate(traj):
        if i > 0:
            out.append(ARROW)
        name, hexv = t["name"], t["hex"]
        if mode == "std":
            c = std_color(fam_of(canon_hex(t["hex"])))
            if c:
                name, hexv = c["name"], c["hex"]
        tip = "%s %s" % (name, hexv)
        if i == 0:
            tip += " — primo campione registrato della cella"
        out.append("<i class='sw%s' style='background:%s' title='%s'></i>" % (
            " init" if i == 0 else "", hexv, esc(tip)))
        if i == d["fade_idx"]:
            out.append("<span class='fade' title='%s'>\u21e3</span>" % esc(
                "svanisce: il testo dice che questo colore (%s %s) scompare — e' un colore "
                "intermedio, non quello finale" % (name, hexv)))
    if d["final_unknown"]:
        out.append(ARROW)
        out.append("<span class='miss' title='%s'><i class='sw missing'></i><em>!</em></span>" % esc(
            "dopo lo svanimento non e' registrato alcun campione: il colore finale non e' "
            "fra le osservazioni"))
    return "<span class='flow dyn'>%s</span>" % "".join(out)


def render_chain(mo, mode):
    """REGOLA #2 - il registro fa la spina dorsale: i campioni registrati, nell'ordine
    in cui sono stati osservati, collegati dalla freccia. I percorsi paralleli si
    aprono solo dove il testo scrive un'alternativa esplicita ("/" o "or")."""
    out = []
    if mo["initial"]:
        lab = mo.get("init_label") or ""
        out.append("<i class='sw init' style='background:%s' title='%s'></i>" % (
            mo["initial"]["hex"],
            esc("prima osservazione: il colore proprio del reattivo (%s %s)%s"
                % (mo["initial"]["name"], mo["initial"]["hex"],
                   (". Il testo lo nomina gia' nella prima fase: '%s'" % lab) if lab else ""))))
    first = True
    for st in mo["chain"]:
        if mo["initial"]:
            out.append(ARROW_INIT if first else ARROW)
        elif not first:
            out.append(ARROW)
        first = False
        if st.get("kind") == "missing":
            col = missing_color(st["fam"], st.get("mods", []), mode)
            tip = esc("%s: citato nel testo ma non presente nei campioni registrati"
                      % FAM_IT.get(st["fam"], st["fam"]))
            out.append("<i class='sw missing' style='background:%s' title='%s'></i>" % (
                col["hex"] if col else "#e9ecf1", tip))
            out.append("<span class='miss' title='%s'><em>!</em></span>" % tip)
            continue
        t = st["tone"]
        nm, hexv = t["name"], t["hex"]
        if mode == "std":
            c = std_color(fam_of(canon_hex(t["hex"])))
            if c:
                nm, hexv = c["name"], c["hex"]
        tip = "%s %s" % (nm, hexv)
        m = st.get("mention")
        if m:
            tip += " — il testo lo descrive come '%s'" % m["text"]
            if len(m["fams"]) > 1:
                tip += " [composto: %s]" % m["text"]
        else:
            tip += " — campione registrato che il testo non descrive"
        out.append("<i class='sw' style='background:%s' title='%s'></i>" % (hexv, esc(tip)))
        if not m:
            out.append("<span class='q' title='%s'>?</span>" % esc(
                "campione registrato (%s %s) che il testo non descrive: e' un passo della "
                "sequenza osservata, senza un nome corrispondente nel testo" % (nm, hexv)))
    return "<span class='flow chain'>%s</span>" % "".join(out)


def render_flow(cell, mode):
    """mode 'full': tutti i toni registrati + colore iniziale + extra.
       mode 'std' : un campione standard per famiglia, citati dal testo.
       Un'alternativa esplicita ('/' o 'or') apre un ramo: la cella mostra percorsi
       paralleli. Senza alternative, il registro fa la spina dorsale."""
    mo = cell_model(cell)
    if mo.get("dynamic"):
        return render_dynamic(mo, mode)
    if mo.get("chain") is not None:
        return render_chain(mo, mode)
    tracks = build_tracks(mo)
    has_init = (mode == "full" and mo["initial"])
    if not any(tracks) and not has_init and not mo["extras"]:
        return ""
    last_phase = len(mo["phases"]) - 1

    def track_html(tr):
        out = []
        if has_init:
            out.append("<i class='sw init' style='background:%s' title='%s'></i>" % (
                mo["initial"]["hex"],
                esc("prima osservazione: il colore proprio del reattivo (%s %s)%s"
                    % (mo["initial"]["name"], mo["initial"]["hex"],
                       (". Il testo lo nomina gia' nella prima fase: '%s'" % mo.get("init_label"))
                       if mo.get("init_label") else ""))))
        # una fase che non ha campioni e non ha colori mancanti non si disegna:
        # e' il caso in cui il testo nomina il colore proprio del reattivo, e quel
        # nome e' gia' il campino iniziale (evita il riquadro vuoto in mezzo)
        nodes = [nd for nd in tr if nd and any(
            m.get("tones") or m.get("missing") for g in nd for m in g["mentions"])]
        for pi, node in enumerate(nodes):
            if pi > 0:
                out.append(ARROW)
            elif has_init:
                out.append(ARROW_INIT)
            for g in node:
                out.append(render_group(g, mode))
        return "".join(out)

    # i campioni registrati che il testo non descrive sono gia' percorsi a se' (tracce separate)
    if len(tracks) == 1:
        return "<span class='flow'>%s</span>" % track_html(tracks[0])
    rows = ["<span class='track'>%s</span>" % track_html(tr) for tr in tracks]
    return "<span class='flow tracks'>%s</span>" % "".join(rows)


SHADE_IT = {"dark": "scuro", "light": "chiaro", "pale": "pallido", "faint": "tenue",
            "bright": "brillante", "olive": "oliva", "neon": "neon", "sea": "mare",
            "slight": "lieve", "deep": "intenso", "very": "intenso"}


def mention_text(m):
    base = "+".join(FAM_IT.get(f, f) for f in m["fams"])
    for mod in m.get("mods", []):
        if mod in SHADE_IT:
            base = base + " " + SHADE_IT[mod]
            break
    if m.get("compound"):
        # il legame di composto non e' visibile nel disegno: lo si conserva qui
        base = "%s [composto: %s]" % (base, m.get("text", ""))
    return base


def paths_text(cell):
    """Percorsi con i nomi dei campioni registrati: 'yellow1 -> green3 ;; yellow1 -> brown2'."""
    mo = cell_model(cell)
    if mo.get("dynamic"):
        d = mo["dynamic"]
        parts = [t["name"] for t in d["traj"]]
        if d["final_unknown"]:
            parts.append("?")
        return " → ".join(parts)
    if mo.get("chain") is not None:
        parts = []
        if mo["initial"]:
            parts.append(mo["initial"]["name"])
        for st in mo["chain"]:
            if st.get("kind") == "missing":
                parts.append("?" + st["fam"])
            else:
                parts.append(st["tone"]["name"])
        return " → ".join(parts)
    out = []
    for tr in build_tracks(mo):
        parts = []
        if mo["initial"]:
            parts.append(mo["initial"]["name"])
        for node in tr:
            for g in node:
                for m in g["mentions"]:
                    if m["tones"]:
                        parts.append("+".join(t["name"] for t in m["tones"]))
                    elif m.get("missing"):
                        parts.append("?" + "/".join(m["missing"]))
                    # una menzione che non ha campioni e non ha colori mancanti
                    # nomina il campino iniziale: non aggiunge un passo
        if parts:
            out.append(" \u2192 ".join(parts))
    return " ;; ".join(out)


def structure_text(cell):
    """Percorsi in testo: 'giallo → verde scuro > nero ;; giallo → marrone > nero'."""
    mo = cell_model(cell)
    if mo.get("dynamic"):
        d = mo["dynamic"]
        parts = []
        for i, t in enumerate(d["traj"]):
            f = FAM_IT.get(fam_of(canon_hex(t["hex"])), "")
            if i == d["fade_idx"]:
                f += " (svanisce)"
            parts.append(f)
        if d["final_unknown"]:
            parts.append("? (finale non campionato)")
        return " → ".join(parts)
    if mo.get("chain") is not None:
        parts = []
        if mo["initial"]:
            parts.append(FAM_IT.get(fam_of(canon_hex(mo["initial"]["hex"])), "") + " (prima osservazione)")
        for st in mo["chain"]:
            if st.get("kind") == "missing":
                parts.append("? " + FAM_IT.get(st["fam"], st["fam"]))
                continue
            f = FAM_IT.get(fam_of(canon_hex(st["tone"]["hex"])), "")
            m = st.get("mention")
            if m:
                if len(m["fams"]) > 1:
                    f += " [composto: %s]" % m["text"]
                else:
                    f += " (%s)" % m["text"]
            parts.append(f)
        return " → ".join(parts)
    tracks = build_tracks(mo)
    init_txt = ""
    if mo["initial"]:
        init_txt = FAM_IT.get(fam_of(canon_hex(mo["initial"]["hex"])), "") + " →"
    out = []
    for tr in tracks:
        phases_txt = []
        for node in tr:
            t = " ".join("+".join(mention_text(m) for m in g["mentions"]
                                  if m.get("tones") or m.get("missing"))
                         for g in node).strip()
            if t:
                phases_txt.append(t)
        if not phases_txt:
            continue
        body = " > ".join(phases_txt)
        if init_txt:
            body = init_txt + " " + body
        out.append(body)
    return " ;; ".join(out)


def n_paths(mo):
    """Quanti percorsi mostra la cella: con il registro come spina dorsale e' uno,
    con alternative esplicite e' uno per alternativa. Una cella dinamica (un colore
    che svanisce) mostra UNA traiettoria: il registro dei campioni, non i rami del
    testo."""
    if mo.get("dynamic"):
        return 1
    if mo.get("chain") is not None:
        return 1
    return len(build_tracks(mo))


def n_fasi_of(mo):
    """Fasi del testo; per le celle dinamiche, le fasi della traiettoria;
    per le celle con il registro come spina dorsale, i passi della sequenza."""
    if mo.get("dynamic"):
        return len(mo["dynamic"]["traj"]) + (1 if mo["dynamic"]["final_unknown"] else 0)
    if mo.get("chain") is not None:
        return len(mo["chain"]) + (1 if mo["initial"] else 0)
    return len(mo["phases"])


def dynamic_label(mo):
    """Colonna 'dinamica': che cosa svanisce, o che cosa sbuffa."""
    d = mo.get("dynamic")
    if d:
        if d["fade_fam"]:
            return "svanisce: %s" % FAM_IT.get(d["fade_fam"], d["fade_fam"])
        return "svanisce"
    if mo.get("fizz"):
        return "sbuffa"
    return ""


def fams_of_cell(cell):
    """Famiglie di colore registrate da un record (dal suo elenco campioni)."""
    out = []
    for t in cell.get("start") or []:
        f = fam_of(canon_hex(t["hex"]))
        if f not in out:
            out.append(f)
    return out


def merge_same_desc(cells):
    """Record con la stessa descrizione (stesso testo, stessa provenienza) descrivono
    la stessa reazione: i campioni sono uniti in un'unica osservazione.
    Restano separati i record che hanno testi o fonti diverse."""
    groups = []
    for c in cells:
        for g in groups:
            if g[0]["desc"] == c["desc"]:
                g.append(c)
                break
        else:
            groups.append([c])
    out = []
    for g in groups:
        if len(g) == 1:
            out.append((g[0], 1))
            continue
        start, end = [], []
        for c in g:
            for t in c["start"]:
                if not any(x["hex"] == t["hex"] for x in start):
                    start.append(t)
            for t in c["end"]:
                if not any(x["hex"] == t["hex"] for x in end):
                    end.append(t)
        m = dict(g[0])
        m["start"], m["end"] = start, end
        out.append((m, len(g)))
    return out


def cell_html(rk, cells):
    """Una cella può contenere più record (stessa coppia, righe di provenienza diverse)."""
    if not cells:
        return "<td class='c c-empty' data-rg='%s'><span class='dash'>&mdash;</span></td>" % rk
    rk = cells[0]["reagent"]
    positives = {c["positive"] for c in cells}
    same_mark = len(positives) == 1
    # record con la stessa descrizione (stessa fonte): restano record separati.
    # se nessun record registra da solo tutti i colori che il testo nomina insieme
    # ("red AND green"), non possono essere simultanei: sono osservazioni diverse,
    # e ognuna mostra i propri campioni.
    #
    # ---------------------------------------------------------------------------
    # "red AND green > brown (234)" (25B/25C/25D-NBOMe, Mandelin) reso come DUE
    # PERCORSI PARALLELI: l'"AND" della fonte viene letto come un "OR" (rosso |
    # verde), non come due colori simultanei. Ogni record mostra solo i propri
    # campioni e i colori citati dal testo ma non registrati da quel record non
    # vengono marcati come mancanti ("!") ma come "campioni del record fratello".
    #
    # Motivo: nessun record registra da solo entrambi i colori che il testo nomina
    # insieme -> non possono essere simultanei nella stessa osservazione.
    #
    # Riferimento (perché non esiste un "colore univoco" degli NBOMe nei reattivi
    # standard, e quindi due osservazioni diverse sono la norma e non un errore):
    #   Clancy L., Philp M., Shimmon R., Fu S., "Development and validation of a
    #   color spot test method for the presumptive detection of 25-NBOMe compounds",
    #   Drug Test. Anal. 2021, 13(5), 929-943. DOI 10.1002/dta.2905
    #   copia accettata (peer reviewed), lettura libera in UTS Opus:
    #   https://opus.lib.uts.edu.au/bitstream/10453/153341/3/9C8F4B03-EDEE-4C73-8E3E-0AD0A3FA3AE7%20%20%20%20AM.pdf
    #   Clancy L., "The development and validation of screening test methods for the
    #   presumptive detection of New Psychoactive Substances", tesi di dottorato,
    #   University of Technology Sydney, 2022, capp. 1-2 (liberamente scaricabile):
    #   https://opus.lib.uts.edu.au/bitstream/10453/168836/2/02whole.pdf
    #   citazioni dalla tesi:
    #     - "Currently, no presumptive test data exists for 25-NBOMe compounds."
    #     - "The analogues of the 25-NBOMe series produce a range of different
    #       colours, and 2) these observed colour changes cannot be distinguished
    #       from the colours seen when testing traditional illicit drugs and
    #       other NPS."
    #     - "Ehrlich's test, used to identify indoles such as LSD, and Marquis
    #       reagent have been utilised to detect 25-NBOMe compounds ... The results,
    #       however, indicate they are not reliable enough to accurately identify
    #       25-NBOMe compounds."
    #     - "The Mandelin reagent was shown to distinguish some NBOMe compounds and
    #       other phenethylamine-type substances ... A trending issue appears to be
    #       the different colours seen between analogues." (cap. 1, p. 18)
    #   Licenza delle due copie UTS Opus: self-archiving Wiley ("may be used for
    #   non-commercial purposes ... may not be enhanced, enriched or otherwise
    #   transformed into a derivative work"): lettura e citazione libere, uso non
    #   commerciale, nessuna derivazione -> CITABILE, non riusabile come dataset.
    #   Per i dati del dataset la fonte resta il semantic data PNW (CC BY 4.0).
    #
    # Nota: l'"AND" di una singola fase ("yellow with black spots") ha un altro
    # significato (colori che coesistono) ed e' gestito in parse_desc.py.
    # ---------------------------------------------------------------------------
    groups = []
    for c in cells:
        for g in groups:
            if g[0]["desc"] == c["desc"]:
                g.append(c)
                break
        else:
            groups.append([c])
    seen_txt = set()
    blocks, titles = [], []
    flat = []
    for g in groups:
        for j, c in enumerate(g):
            flat.append((c, g, j))
    for i, (cell, g, j) in enumerate(flat):
        nrec = len(g)
        pos = cell["positive"]
        # il flag isPositive della fonte non viene mostrato come segno: in 1520
        # record su 1521 coincide con "la riga registra almeno un campione", quindi
        # il segno non aggiunge informazione e si fa leggere come un giudizio
        # ("identificazione positiva") che non e'. Resta nel tooltip della cella
        # e nella colonna is_positive del CSV.
        if same_mark and i > 0:
            mark = ""
        txt = cell["desc"]
        if txt in seen_txt:
            body = ("<span class='dup' title='%s'>%s osservazione</span>"
                    % (esc("stessa descrizione e stessa fonte (%s): sono osservazioni diverse, "
                           "una per record, e i campioni mostrati sono quelli di ciascuna"
                           % (txt.split("(")[-1].rstrip(")") if "(" in txt else "")),
                       ["", "2ª", "3ª", "4ª"][j] if j < 4 else "%dª" % (j + 1)))
        else:
            seen_txt.add(txt)
            body = fmt_desc(txt)
        block = "<span class='tx'>%s</span>" % body
        if nrec > 1:
            # i colori che il testo nomina ma che questo record non registra non
            # sono "mancanti": li registra un altro record della stessa fonte
            sib = set()
            for k, c2 in enumerate(g):
                if k != j:
                    sib |= set(fams_of_cell(c2))
            if sib:
                cell = dict(cell)
                cell["_sib"] = sib
        mo_c = cell_model(cell)
        if mo_c.get("fizz"):
            block += ("<span class='fizz' title='%s'><svg viewBox='0 0 24 24' width='15' height='15' "
                      "fill='none' stroke='currentColor' stroke-width='2.1' stroke-linecap='round'>"
                      "<circle cx='7.2' cy='15.4' r='4.3'/><circle cx='15.4' cy='8.2' r='3.2'/>"
                      "<circle cx='18' cy='15.6' r='2.3'/></svg></span>" % esc(
                          "la reazione sbuffa: il testo lo dice ('fizzes', 'fizzing', 'foaming', 'bubbling'). "
                          "Non e' uno svanimento: il colore resta quello osservato."))
        # la cella si disegna se ha qualcosa da mostrare: un campione, un colore iniziale
        # o un colore citato dal testo ma non osservato (il riquadro tratteggiato)
        if (cell["start"] or cell["end"] or mo_c["initial"] or mo_c["extras"]
                or mo_c.get("dynamic") or any(ph["groups"] for ph in mo_c["phases"])):
            block += ("<span class='sws sws-full'>%s</span><span class='sws sws-std'>%s</span>"
                      % (render_flow(cell, "full"), render_flow(cell, "std")))
        blocks.append("<span class='mblock'>%s</span>" % block)
        seqs = [" > ".join("%s %s" % (x["name"], x["hex"]) for x in cell["start"]) or "—"]
        ends = [" > ".join("%s %s" % (x["name"], x["hex"]) for x in cell["end"]) or "—"]
        if nrec > 1:
            seqs = [" > ".join("%s %s" % (x["name"], x["hex"]) for x in c["start"]) or "—" for c in g]
            ends = [" > ".join("%s %s" % (x["name"], x["hex"]) for x in c["end"]) or "—" for c in g]
        titles.append("%s | isPositive: %s | sequenza registrata: %s | toni canonici: %s%s" % (
            esc(txt), str(pos).lower(), " | ".join(seqs), " | ".join(ends),
            (" | %d record con stessa descrizione e stessa fonte: osservazioni diverse, "
             "una per record" % nrec) if nrec > 1 else ""))
    if len(cells) > 1:
        n_same = sum(1 for g in groups if len(g) > 1)
        bt = ("%d record per la stessa coppia sostanza-reattivo" % len(cells))
        if n_same:
            bt += (": %d con la stessa descrizione e la stessa fonte sono osservazioni diverse "
                   "(una riga per record), %d con provenienza diversa restano separati"
                   % (n_same, len(cells) - n_same))
        else:
            bt += ": provenienza diversa, restano separati"
        badge = "<span class='badge' title='%s'>×%d</span>" % (esc(bt), len(cells))
    else:
        badge = ""
    return ("<td class='c%s' data-rg='%s' title='%s'>%s%s</td>" % (
        " multi" if len(cells) > 1 else "", rk,
        esc("%s: %s" % (COL_FULL.get(rk, rk), "  ///  ".join(titles))),
        badge, "".join(blocks)))



# === SEZIONE 4 - RENDER (la tabella visuale) ====================================

CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#fafafa;color:#14171e;font-family:'Outfit','Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1400px;margin:0 auto;padding:32px 24px 72px}
h1,h2,h3{margin:0;font-weight:600;letter-spacing:-.018em}
h1{font-size:clamp(22px,3.2vw,31px);line-height:1.18}
h2{font-size:15px;letter-spacing:.01em}
p{margin:0}
a{color:#b45309;text-decoration:none}
a:hover{text-decoration:underline}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace}

.hero{padding:4px 0 22px;border-bottom:1px solid #e9e9ef;margin-bottom:22px}
.hero .kicker{font-size:11.5px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:#b45309;margin-bottom:10px}
.hero .sub{margin-top:10px;color:#5c6270;max-width:74ch;font-size:14.5px}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.meta span{font-size:12px;color:#5c6270;background:#fff;border:1px solid #e6e6ec;border-radius:999px;padding:4px 11px}
.meta span b{color:#14171e;font-weight:600}

.panel{background:#fff;border:1px solid #e6e6ec;border-radius:16px;box-shadow:0 2px 10px rgba(20,23,30,.04);margin-bottom:20px}
.panel .ph{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid #efeff3}
.panel .ph svg{color:#b45309;flex:none}
.panel .pb{padding:16px 18px}

.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.stat{background:#fff;border:1px solid #e6e6ec;border-radius:14px;padding:14px 16px;box-shadow:0 2px 8px rgba(20,23,30,.035)}
.sv{display:block;font-size:24px;font-weight:700;letter-spacing:-.02em;line-height:1.1}
.sl{display:block;font-size:11.5px;color:#767c89;margin-top:3px}

.toolbar{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.field{position:relative;flex:1 1 240px;min-width:210px}
.field input{width:100%;padding:9px 12px 9px 34px;border:1px solid #dcdce4;border-radius:10px;font:inherit;font-size:13.5px;background:#fff;color:#14171e}
.field input:focus{outline:2px solid #f59e0b;outline-offset:1px;border-color:#f59e0b}
.field svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#9aa0ad}
select,.btn{font:inherit;font-size:13px;padding:9px 12px;border:1px solid #dcdce4;border-radius:10px;background:#fff;color:#14171e;cursor:pointer}
.btn{display:inline-flex;align-items:center;gap:7px;font-weight:500}
.btn:hover{background:#f6f6f9;border-color:#c9c9d3}
.btn.primary{background:#b45309;border-color:#b45309;color:#fff}
.btn.primary:hover{background:#96450a}
label.sl2{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:#5c6270;white-space:nowrap}
input[type=range]{accent-color:#b45309;width:120px}

.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}
.chip{display:inline-flex;align-items:center;gap:7px;font:inherit;font-size:12.5px;padding:5px 11px;border:1px solid #dcdce4;border-radius:999px;background:#fff;color:#5c6270;cursor:pointer}
.chip:hover{border-color:#c9c9d3;background:#fafafa}
.chip.off{opacity:.42;text-decoration:line-through}
.chip .cdot{width:8px;height:8px;border-radius:50%;display:inline-block}
.chip .cn{color:#9aa0ad;font-size:11.5px;font-family:'JetBrains Mono',monospace}

.bench-row{display:grid;grid-template-columns:132px 1fr 44px;gap:12px;align-items:center;padding:4px 0;width:100%;background:none;border:0;cursor:pointer;text-align:left;font:inherit}
.bench-row .label{font-size:12.5px;color:#5c6270}
.bench-row .val{font-size:12px;color:#767c89;text-align:right;font-family:'JetBrains Mono',monospace}
.bar-bg{height:16px;background:#f1f1f5;border-radius:6px;overflow:hidden}
.bar-fill{display:block;height:100%;background:linear-gradient(90deg,#d97706,#f0b429);border-radius:6px;transition:width .25s ease}
.bench-row:hover .label{color:#14171e}
.two{display:grid;grid-template-columns:1.15fr 1fr;gap:20px}
@media(max-width:900px){.two{grid-template-columns:1fr}.stats{grid-template-columns:repeat(2,1fr)}}

.tblwrap{overflow:auto;max-height:76vh;border-radius:0 0 16px 16px}
table{border-collapse:separate;border-spacing:0;table-layout:fixed;width:100%}
thead th{position:sticky;top:0;z-index:3;background:#fff;border-bottom:1px solid #e0e0e8;padding:9px 10px;text-align:left;font-size:12.5px;font-weight:600;color:#14171e;vertical-align:bottom}
thead th:first-child{left:0;z-index:4;border-right:1px solid #e6e6ec}
.rh{display:block;line-height:1.25}
.rc{display:block;font-size:11px;color:#9aa0ad;font-weight:500;font-family:'JetBrains Mono',monospace;margin-top:1px}
tbody td,tbody th{border-bottom:1px solid #f0f0f4}
th.rowhead{position:sticky;left:0;z-index:2;background:#fff;border-right:1px solid #e6e6ec;padding:9px 12px;font-weight:500;font-size:13.5px;text-align:left;white-space:nowrap}
th.rowhead a{color:#14171e}
th.rowhead a:hover{color:#b45309;text-decoration:underline}
.alias{display:block;font-size:11px;color:#9aa0ad;font-weight:400;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
td.c{padding:7px 10px;vertical-align:top;font-size:12.5px;color:#3a4256}
td.c-empty{background:#fbfbfc}
td.c.multi{background:#fffdf8;box-shadow:inset 2px 0 0 #f0b429}
.dash{color:#d4d4dc}
.mblock{display:block}
.mblock+.mblock{border-top:1px dashed #ececf2;margin-top:5px;padding-top:5px}
.dup{color:#b0b4bd;font-size:11px;font-style:italic}
.badge{float:right;font-size:9.5px;font-weight:700;color:#b45309;background:#fdf1dc;border:1px solid #f6e0b5;border-radius:999px;padding:0 5px;line-height:15px;margin-left:4px;font-family:'JetBrains Mono',monospace}
.tx{display:block;line-height:1.35}

.gt{color:#b45309;font-weight:700;padding:0 1px}
.neg{color:#8b909b;font-style:italic}
.idx{color:#b0b4bd;font-size:11px}
.pm{vertical-align:-1px;margin-right:4px}
.pm-y{color:#059669}
.pm-n{color:#c2c5cc;font-weight:700}
.sws{display:block;margin-top:4px}
.flow{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.flow .grp{display:inline-flex;gap:1px;padding:1px;border-radius:4px;box-shadow:inset 0 0 0 1px rgba(20,23,30,.14)}
.flow .grp.alt{flex-direction:column;gap:1px;align-items:center}
.flow .grp.sim{flex-direction:row}
.flow .grp.extra{opacity:.55;box-shadow:inset 0 0 0 1px rgba(20,23,30,.3)}
.flow .sw{border-radius:2px;width:10px;height:11px;box-shadow:none;flex:none}
.flow .sw.init{opacity:.45}
.flow .sw.missing{background:repeating-linear-gradient(45deg,#f3f4f7 0 3px,#dfe2e8 3px 6px);box-shadow:none;width:10px}
.flow .miss{display:inline-flex;align-items:center;gap:2px}
.flow .miss em{font-style:normal;font-size:9px;color:#5f6672;line-height:1;letter-spacing:.01em;font-weight:700}
.flow .q{font-size:9px;font-weight:700;color:#9aa0ac;line-height:1;cursor:help}
.flow .fade{font-size:10px;color:#8a6d3b;line-height:1;margin-left:1px;cursor:help;font-weight:700}
.flow.dyn{gap:3px}
.flow.chain{gap:3px;align-items:center}
.flow.chain .sw{width:11px;height:11px;border-radius:3px;box-shadow:inset 0 0 0 1px rgba(20,23,30,.16)}
.fizz{display:inline-flex;align-items:center;color:#5b6473;margin-left:4px;vertical-align:-2px;cursor:help}
.flow .farrow{color:#b8bcc4;flex:none}
.flow .farrow.init{color:#c9cdd5;stroke-width:2}
.flow.tracks{flex-direction:column;align-items:flex-start;gap:3px}
.flow .track{display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.flow .fsym{color:#9aa0ad;font-size:9px;font-weight:700;line-height:1;align-self:center;padding:0 1px}
.mode-std .sws-full{display:none}
.mode-full .sws-std{display:none}
.seg{display:inline-flex;border:1px solid #dcdce4;border-radius:10px;overflow:hidden;background:#fff}
.segbtn{font:inherit;font-size:13px;padding:8px 13px;border:0;background:#fff;color:#5c6270;cursor:pointer}
.segbtn:hover{background:#f6f6f9}
.segbtn.on{background:#b45309;color:#fff;font-weight:500}
.swgrp{display:inline-flex;gap:2px}
.sw{width:11px;height:11px;border-radius:3px;display:inline-block;box-shadow:inset 0 0 0 1px rgba(20,23,30,.16)}
.sw.big{width:30px;height:30px;border-radius:8px}
.swmore{font-size:9.5px;color:#9aa0ad;font-family:'JetBrains Mono',monospace;align-self:center}
tbody tr:hover td,tbody tr:hover th.rowhead{background:#fdfaf4}
tbody tr.hidden{display:none}

.fam{display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #f2f2f6}
.fam:last-child{border-bottom:0}
.famname{width:62px;font-size:12px;color:#5c6270;text-transform:capitalize}
.famsw{display:flex;gap:6px}
.notes{font-size:13px;color:#5c6270}
.notes li{margin-bottom:7px}
.notes b{color:#14171e;font-weight:600}
footer{margin-top:26px;padding-top:18px;border-top:1px solid #e9e9ef;font-size:12.5px;color:#767c89;display:flex;flex-wrap:wrap;gap:8px 22px;align-items:center}
footer a{color:#b45309}
"""

JS = """
const P = JSON.parse(document.getElementById('payload').textContent);
const rows = Array.from(document.querySelectorAll('#matrix tbody tr'));
const table = document.getElementById('matrix');
const q = document.getElementById('q');
const minCov = document.getElementById('mincov');
const sortSel = document.getElementById('sort');
const countEl = document.getElementById('count');
const cellCountEl = document.getElementById('cellcount');
const hidden = new Set();

// mappa colonna -> elementi (intestazione + celle)
const colEls = {};
document.querySelectorAll('#matrix [data-rg]').forEach(el=>{
  (colEls[el.dataset.rg] = colEls[el.dataset.rg] || []).push(el);
});

function applyCols(){
  P.reagents.forEach(r=>{
    const hide = hidden.has(r.short);
    (colEls[r.short]||[]).forEach(el=>{ el.style.display = hide ? 'none' : ''; });
  });
}

function apply(){
  const term = q.value.trim().toLowerCase();
  const min = +minCov.value;
  let shown = 0;
  rows.forEach(tr=>{
    const name = tr.dataset.name, alias = tr.dataset.alias || '';
    const okTerm = !term || name.includes(term) || alias.includes(term);
    const okCov = (+tr.dataset.cov) >= min;
    const on = okTerm && okCov;
    tr.classList.toggle('hidden', !on);
    if(on) shown++;
  });
  applyCols();
  countEl.textContent = shown + ' / ' + rows.length + ' sostanze';
  let cells = 0;
  document.querySelectorAll('#matrix tbody tr:not(.hidden)').forEach(tr=>{
    tr.querySelectorAll('td.c:not(.c-empty) .mblock').forEach(()=>{ cells++; });
  });
  cellCountEl.textContent = cells + ' coppie in vista';
}

q.addEventListener('input', apply);
minCov.addEventListener('input', apply);
sortSel.addEventListener('change', ()=>{
  const tb = table.tBodies[0];
  const arr = Array.from(tb.rows);
  const mode = sortSel.value;
  arr.sort((a,b)=>{
    if(mode==='za') return b.dataset.name.localeCompare(a.dataset.name);
    if(mode==='cov') return (+b.dataset.cov)-(+a.dataset.cov) || a.dataset.name.localeCompare(b.dataset.name);
    if(mode==='covasc') return (+a.dataset.cov)-(+b.dataset.cov) || a.dataset.name.localeCompare(b.dataset.name);
    return a.dataset.name.localeCompare(b.dataset.name);
  });
  arr.forEach(r=>tb.appendChild(r));
  apply();
});

document.querySelectorAll('.chip').forEach(ch=>{
  ch.addEventListener('click', ()=>{
    const rg = ch.dataset.rg;
    if(hidden.has(rg)) hidden.delete(rg); else hidden.add(rg);
    ch.classList.toggle('off', hidden.has(rg));
    apply();
  });
});

document.querySelectorAll('.bench-row').forEach(b=>{
  b.addEventListener('click', ()=>{
    const rg = b.dataset.rg;
    const only = (hidden.size === P.reagents.length-1 && !hidden.has(rg));
    hidden.clear();
    document.querySelectorAll('.chip').forEach(c=>c.classList.remove('off'));
    if(!only){ P.reagents.forEach(r=>{ if(r.short!==rg){hidden.add(r.short);} });
      document.querySelectorAll('.chip').forEach(c=>{ if(c.dataset.rg!==rg) c.classList.add('off'); });
    }
    apply();
    table.scrollIntoView({behavior:'smooth', block:'start'});
  });
});

document.getElementById('csv').addEventListener('click', ()=>{
  const out = ['__CSVHEADER__'];
  document.querySelectorAll('#matrix tbody tr:not(.hidden)').forEach(tr=>{
    const name = tr.querySelector('a').textContent;
    const aliasEl = tr.querySelector('.alias');
    const alias = aliasEl ? aliasEl.textContent : '';
    const url = tr.querySelector('a').getAttribute('href');
    const sub = P.subs.find(s=>s.name===name);
    if(!sub) return;
    Object.keys(sub.cells).forEach(rg=>{
      if(hidden.has(rg)) return;
      const full = (P.reagents.find(r=>r.short===rg)||{}).full || rg;
      sub.cells[rg].forEach((c,i)=>{
        const desc=c.d.replace(/\\s*\\(\\d+\\)\\s*$/,'').trim();
        const parts=desc.split('>').map(x=>x.trim());
        const seq = parts.length>1;
        const fmt = a => a.map(x=>x[0]+' '+x[1]).join(' > ');
        out.push([name,alias,rg,full,c.d,c.fm||'',c.dy||'',i+1,String(c.p).toLowerCase(),seq,
                  c.nf||parts.length,c.np,c.st||'',c.pt||'',seq?parts[0]:'',seq?parts[parts.length-1]:'',
                  fmt(c.s||[]),fmt(c.e||[]),url]
                 .map(v=>'"'+String(v==null?'':v).replace(/"/g,'""')+'"').join(';'));
      });
    });
  });
  const blob = new Blob(['\\ufeff'+out.join('\\n')], {type:'text/csv;charset=utf-8'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'psychonautwiki_reagenti_sostanze.csv';
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById('json').addEventListener('click', ()=>{
  const blob = new Blob([JSON.stringify(P,null,1)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'psychonautwiki_reagenti_sostanze.json';
  a.click();
  URL.revokeObjectURL(a.href);
});

document.getElementById('reset').addEventListener('click', ()=>{
  q.value=''; minCov.value='1'; sortSel.value='az'; hidden.clear();
  document.querySelectorAll('.chip').forEach(c=>c.classList.remove('off'));
  apply();
});

document.querySelectorAll('.segbtn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.segbtn').forEach(b=>b.classList.remove('on'));
    btn.classList.add('on');
    document.querySelector('.tblwrap').classList.toggle('mode-full', btn.dataset.mode==='full');
    document.querySelector('.tblwrap').classList.toggle('mode-std', btn.dataset.mode==='std');
  });
});

apply();
"""

today = "18 novembre 2026"
HTML = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Matrice sostanza × reattivo — PsychonautWiki</title>
<meta name="description" content="Tabella completa delle reazioni tra sostanze e reattivi di test, con descrizione del colore, sequenza temporale e campioni di colore, dai dati semantici di PsychonautWiki (CC BY 4.0).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head>
<body>
<div class="wrap">

<header class="hero">
  <div class="kicker">PsychonautWiki · dati semantici · CC BY 4.0</div>
  <h1>Matrice reazioni: sostanza × reattivo</h1>
  <p class="sub">Ogni riga è una sostanza, ogni colonna un reattivo, ogni cella la reazione documentata: descrizione testuale, eventuale sequenza nel tempo e campioni di colore iniziali e finali. Dati integrali del livello semantico dell'API GraphQL di PsychonautWiki, non la sola vista ridotta della "Color chart".</p>
  <div class="meta">
    <span><b>__NSUB__</b> sostanze</span>
    <span><b>__NPAIR__</b> coppie</span>
    <span><b>15</b> reattivi</span>
    <span><b>__NTRANS__</b> transizioni</span>
    <span>Estratto il __TODAY__</span>
    <span>Fonte: <a href="https://psychonautwiki.org/" target="_blank" rel="noopener">psychonautwiki.org</a></span>
  </div>
</header>

<div class="stats">__STATS__</div>

<section class="panel">
  <div class="ph">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
    <h2>Filtri e strumenti</h2>
  </div>
  <div class="pb">
    <div class="toolbar">
      <div class="field">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
        <input id="q" type="search" placeholder="Cerca una sostanza (es. MDMA, LSD, 2C-E, cocaina…)" autocomplete="off">
      </div>
      <label class="sl2">Ordina
        <select id="sort">
          <option value="az">Nome A–Z</option>
          <option value="za">Nome Z–A</option>
          <option value="cov">Più reattivi</option>
          <option value="covasc">Meno reattivi</option>
        </select>
      </label>
      <label class="sl2">Min. reattivi
        <input id="mincov" type="range" min="1" max="15" value="1">
        <span class="mono" id="mincovval">1</span>
      </label>
      <button class="btn" id="reset">Azzera</button>
      <div class="seg" role="group" aria-label="Rappresentazione dei colori">
        <button class="segbtn on" data-mode="full">Toni registrati</button>
        <button class="segbtn" data-mode="std">Toni standard</button>
      </div>
      <button class="btn" id="csv">Scarica CSV</button>
      <button class="btn primary" id="json">Scarica JSON</button>
    </div>
    <div class="chips">__CHIPS__</div>
  </div>
</section>

<section class="panel">
  <div class="ph">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/></svg>
    <h2>Copertura per reattivo</h2>
  </div>
  <div class="pb two">
    <div>__BARS__</div>
    <div class="notes">
      <p>Il reattivo con la copertura più ampia è il <b>Marquis</b> con __MARCQ__ sostanze, seguito da Mecke (__MECKQ__) e Mandelin (__MANDQ__). In fondo alla colonna trovate solo i reattivi più rari: Cannabis 4-AP copre __CAQ__ sostanze e Folin __FOQ__.</p>
      <p>Le combinazioni non documentate sono lasciate vuote: una cella vuota significa <b>dato assente</b>, non reazione assente. La distribuzione fortemente sbilanciata è il motivo per cui la "Color chart" visibile sul sito copre solo una fetta del dato reale.</p>
      <p style="color:#8b909b;font-size:12.5px">Clicca una barra per isolare quella colonna nella tabella, clicca di nuovo per ripristinarla.</p>
    </div>
  </div>
</section>

<section class="panel">
  <div class="ph">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/></svg>
    <h2>Matrice</h2>
    <span style="font-size:12px;color:#9aa0ad" id="count"></span>
    <span style="font-size:12px;color:#9aa0ad" id="cellcount"></span>
  </div>
  <div class="tblwrap mode-full">
    <table id="matrix">
      <colgroup>
        <col style="width:190px">
        __COLS__
      </colgroup>
      <thead>
        <tr>
          <th scope="col"><span class="rh">Sostanza</span><span class="rc">reattivi</span></th>
          __HEAD__
        </tr>
      </thead>
      <tbody>
        __ROWS__
      </tbody>
    </table>
  </div>
</section>

<section class="panel">
  <div class="ph">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="17" cy="15" r="2.5"/><path d="M8.5 11l3-2.5M9 13.5l6 1"/></svg>
    <h2>Legenda e avvertenze</h2>
  </div>
  <div class="pb two">
    <div>
      <div style="font-size:12.5px;color:#5c6270;margin-bottom:8px">Campioni di colore della fonte (27 tonalità, 9 famiglie):</div>
      __PAL__
    </div>
    <div>
      <ul class="notes">
        <li><b>Descrizione</b>: il testo della fonte, l'unica parte che descrive il reale. Il <span class="gt">&gt;</span> è l'indicatore temporale: "red-orange &gt; brown" vuol dire che la reazione parte rosso-arancio e finisce marrone; con più gradini ("A &gt; B &gt; C") sono le fasi in ordine.</li>
        <li><b>Percorsi e frecce</b>: il <b>registro fa la spina dorsale</b>. I campioni registrati dalla fonte, nell'ordine in cui sono stati osservati, sono la sequenza della cella, e la freccia scura li collega uno a uno. I <b>percorsi paralleli</b> si aprono <i>solo</i> dove il testo della fonte scrive un'alternativa esplicita ("dark green or brown", "green / dark green"): sono 118 record su 1521 (l'8%); in tutti gli altri casi la cella ha un solo percorso. La freccia <b>chiara</b> all'inizio collega la <b>prima osservazione</b> al primo passo: quel passaggio è dedotto dall'ordine del registro, non dal "&gt;" del testo. Un <b>composto</b> ("reddish purple", "purple-blue") non apre un percorso a sé: la fonte usa la palette di 9 famiglie, quindi un campione di quel colore può stare in una sola famiglia — la famiglia che non ha campione mostra il riquadro tratteggiato con il "!", e il legame di composto resta nel tooltip del campione e nella colonna "struttura" del CSV. Un campione registrato che il testo non nomina è un passo della sequenza: lo "?" affiancato lo distingue (188 campioni in 139 celle). Dentro una fase, <b>+</b> significa colori che compaiono <i>insieme</i> ("yellow with black spots").<li><b>Campini</b>: il campino in grigio sbiadito è la <b>prima osservazione</b> della cella. Per i reattivi che hanno un proprio colore (Mandelin, Morris, Scott, Simon's) quella prima osservazione è <b>sempre</b> il colore del reattivo, sia che il testo lo nomini sia che non lo nomini: il giallo del Mandelin è la prima osservazione in 134 celle su 134; le uniche 6 eccezioni sono celle di Simon's in cui la fonte non ha registrato il colore del reattivo (e non lo si inventa). Se il testo nomina quel colore nella prima fase, il campino sbiadito ne è l'etichetta (lo dice il tooltip e la colonna "struttura"); se lo nomina più avanti, quella fase si aggancia al campione successivo — il <b>ritorno</b> al colore di prima. Per gli altri 11 reattivi, che non hanno colore proprio, il campino iniziale è il primo campione registrato quando il testo non lo nomina. La riga &laquo;Reagent only&raquo; delle tavole pubblicate (PsychonautWiki, CC BY-SA 4.0) conferma Mandelin = giallo e Scott = rosso pallido (nel dato: pink 7/7); per Simon's dà &laquo;Colorless &gt; Pale red&raquo;, mentre il dato registra la swatch più chiara (orange1 #fde9d9). Un <b>campino con il "!"</b> è il contrario di un'osservazione: un colore che il <i>testo</i> nomina ma di cui non esiste un campione registrato (206 riquadri in 156 celle, 10,3%): nel record della fonte il testo e l'elenco dei campioni sono due campi tenuti separatamente e non coincidono sempre. Il campino è <b>colorato come quel colore</b> (alla tonalità che la sfumatura implica), con il bordo tratteggiato e il <b>"!"</b> che dicono "non è stato osservato"; il nome per esteso non c'è, sta nel tooltip, nella colonna <span class="mono">struttura</span> e in <span class="mono">percorsi</span> del CSV.<br>I due simboli non si confondono: <b>!</b> = il testo promette un colore che non è stato osservato, <b>?</b> = è stato osservato un colore che il testo non nomina.<br>La <b>sfumatura</b> nel testo dice quale tonalità della famiglia intendeva la fonte: "light/pale/faint/slight/weak" → tono 1, "dark/deep" → tono 3, nessuna sfumatura → tono 2 (la tonalità standard). Verificato sul corpus: "deep" coincide con "dark" (6 casi su 8 su tono 3; i 2 restanti sono celle dove il tono 3 non era registrato), "light/pale/faint" cadono sul tono 1 (131 menzioni contro 12 e 2). La regola sposta 17 scelte di campione, tutte verso la tonalità giusta, nessuna peggiurata.</li><li><b>Colori che svaniscono</b>: 3 celle descrivono una reazione senza passaggi espliciti ma con un colore che scompare ("dissappearing yellow", "dissipating reddish", "dissapearing blueish"). In quei casi la <b>traiettoria è l'ordine dei campioni registrati</b> e ogni campione è una fase collegata dalla freccia: 4-BMC/Mandelin diventa giallo → arancio → rosso (svanisce) → marrone → giallo (l'ultimo campione è lo stesso del primo: il registro torna al colore da cui partiva), HXE/Froehde blu → blu chiaro, Allylescaline/Hofmann giallo → grigio. È un'interpretazione — l'ordine di registrazione come timeline — e non un ">" del testo. Il campione che svanisce è marcato con il simbolo <b>⇣</b> (passa il mouse: il tooltip spiega che quel colore è intermedio, non finale). Quando l'ultimo campione è dello stesso colore che svanisce, il <b>colore finale non è determinabile</b>: la cella termina con il riquadro tratteggiato, così si vede che dopo c'è un colore successivo. L'<b>icona con le bolle</b> accanto al testo marca le 20 celle in cui la fonte scrive "fizzes", "fizzing", "foaming" o "bubbling": la reazione sbuffa, e non è uno svanimento — il colore osservato resta quello. La colonna "dinamica" del CSV riporta il marcatore ("svanisce: rosso", "sbuffa").<li><b>Forme</b>: il testo a volte dice che il colore non è uniforme — "black spots" (macchie, 21 celle), "greenish precipitate" (precipitato, 3), "purple ring" (anello, 3), "blue particles" (particelle, 2). La forma è nella colonna <span class="mono">forma</span> del CSV (29 celle) e resta nel testo della descrizione; non cambia il colore, quindi non apre un percorso diverso.</li><li><b>Campioni ripetuti</b>: quando il registro ripete lo stesso campione <i>di fila</i>, è un duplicato e viene mostrato una sola volta (56 celle, 85 occorrenze in più). Una ripetizione <i>non</i> di fila è invece un <b>ritorno</b> al colore di prima — il registro torna al colore da cui partiva — e viene conservata: è così che il rientro al colore del reattivo resta visibile (19 celle, tutte Mandelin).

        <li><b>Nel dato greco</b> l'API espone due liste, <span class='mono'>startColors</span> e <span class='mono'>endColors</span>, che <b>non</b> sono "prima" e "dopo": <span class='mono'>endColors</span> è la sequenza di <span class='mono'>startColors</span> deduplicata e normalizzata alla tonalità standard (verificato: coincide in 1.521 record su 1.521). Per questo la freccia compare solo se c'è il <span class='gt'>&gt;</span> nel testo.</li>
        <li><b>Indice tra parentesi</b>: numero di provenienza della riga di riferimento da cui la cella è stata ricavata, non un tempo. "no color change" non ha colori associati e l'indice serve a distinguere la fonte.</li>
        <li><b>Flag <span class="mono">isPositive</span></b>: è il campo della fonte che dice che <b>il reattivo ha reagito</b> — non che la sostanza sia stata identificata: i test colorimetrici sono presuntivi. Per questo <b>non è disegnato</b> nella cella: nel corpus coincide con la presenza di un campione in 1520 record su 1521 (l'unica eccezione è Buprenorphine/Liebermann, "black or no color change"), quindi il segno non aggiungerebbe informazione e si farebbe leggere come un giudizio. Resta nel <i>tooltip</i> della cella e nella colonna <span class="mono">is_positive</span> del CSV.</li>
        <li><b>Cella vuota</b>: nessun dato per quella coppia. I test colorimetrici sono presuntivi: un colore non è un'identificazione e un colore assente non è una prova di innocenza.</li>
        <li><b>Badge ×2</b>: la stessa coppia sostanza-reattivo ha più righe nella fonte. 21 celle su 211 (il 10%) hanno un doppio record: in 15 i due record hanno <b>provenienza diversa</b> (indice tra parentesi diverso: due fonti diverse) e restano <b>separati</b>, perché la discordanza fa parte del dato. In 6 i due record hanno <b>testo e provenienza identici</b> (25B/25C/25D-NBOMe Mandelin, 2C-E e Mexedrone Simon's, 4-MeO-PCP Mandelin): sono <b>due osservazioni della stessa fonte</b>, e ciascuna mostra i propri campioni. Poiché nessun record registra da solo entrambi i colori che il testo nomina insieme ("red AND green"), i due colori non possono essere simultanei: ogni riga mostra il proprio. Il testo della fonte resta in testa alla cella, con la sua parola "AND". Il criterio: due righe con lo stesso indice di provenienza non sono due fonti, sono la stessa riga annotata due volte.</li>
      </ul>
    </div>
  </div>
</section>

<footer>
  <span>Dati: <b>PsychonautWiki</b> (semantic data), licenza <a href="https://en.psychonautwiki.org/wiki/Copyrights" target="_blank" rel="noopener">CC BY 4.0</a> — recuperati via GraphQL API il __TODAY__.</span>
  <span>Le interpretazioni "più rosa", "verde oliva" o simili restano quelle degli autori della wiki.</span>

  <span>Strumento: tabella generata il __TODAY__, __NSUB__ sostanze × 15 reattivi.</span>
</footer>

</div>
<script type="application/json" id="payload">__PAYLOAD__</script>
<script>
__JS__
document.getElementById('mincov').addEventListener('input',e=>{document.getElementById('mincovval').textContent=e.target.value;});
</script>
</body>
</html>
"""




def build_page_parts():
    """Le parti variabili della pagina: righe, intestazioni, barre, palette, payload."""
    rows_html = []
    for s in SUBS:
        by_rg = {}
        for c in s["cells"]:
            by_rg.setdefault(c["reagent"], []).append(c)
        tds = []
        for rk in COLS:
            tds.append(cell_html(rk, by_rg.get(rk)))
        al = alias_of(s)
        link = s.get("url") or ""
        head = ("<th scope='row' class='rowhead'><a href='%s' target='_blank' rel='noopener'>%s</a>%s</th>"
                % (esc(link), esc(s["name"]),
                   ("<span class='alias' title='%s'>%s</span>" % (esc(al), esc(al))) if al else ""))
        rows_html.append("<tr data-name='%s' data-alias='%s' data-cov='%d'>%s%s</tr>" % (
            esc(s["name"].lower()), esc(alias_of(s).lower()), len(s["cells"]), head, "".join(tds)))

    head_cells = "".join("<th data-rg='%s' scope='col'><span class='rh'>%s</span><span class='rc'>%s</span></th>" % (
        r["shortName"], esc(r["fullName"]), cov.get(r["shortName"], 0)) for r in RG_ORDER)

    # ---------------- coverage bars ------------------------------------------------
    bars = "".join(
        "<button class='bench-row' data-rg='%s' title='Isola la colonna %s'><span class='label'>%s</span>"
        "<span class='bar-bg'><span class='bar-fill' style='width:%.1f%%'></span></span><span class='val'>%d</span></button>" % (
            r["shortName"], esc(r["fullName"]), esc(r["fullName"]),
            100.0 * cov.get(r["shortName"], 0) / max(cov.values()), cov.get(r["shortName"], 0))
        for r in RG_ORDER)

    # ---------------- color legend -------------------------------------------------
    fam_order = []
    for c in COLORS:
        fam = c["name"].rstrip("123")
        if fam not in fam_order:
            fam_order.append(fam)
    pal = ""
    for fam in fam_order:
        items = [c for c in COLORS if c["name"].rstrip("123") == fam]
        sw = "".join("<i class='sw big' style='background:%s' title='%s · %s'></i>" % (c["hex"], esc(c["name"]), c["hex"]) for c in items)
        pal += "<div class='fam'><span class='famname'>%s</span><span class='famsw'>%s</span></div>" % (esc(fam), sw)

    stats = [
        ("Sostanze", len(SUBS)),
        ("Coppie", sum(len(s["cells"]) for s in SUBS)),
        ("Reattivi", len(RG)),
        ("Transizioni", sum(1 for s in SUBS for c in s["cells"] if ">" in c["desc"])),
        ("Celle con colore", sum(1 for s in SUBS for c in s["cells"] if c["start"] or c["end"])),
    ]
    stat_html = "".join("<div class='stat'><span class='sv'>%d</span><span class='sl'>%s</span></div>" % (v, esc(k)) for k, v in stats)

    chips = "".join(
        "<button class='chip on' data-rg='%s'>%s <span class='cn'>%d</span></button>" % (
            r["shortName"], esc(r["fullName"]), cov.get(r["shortName"], 0)) for r in RG_ORDER)

    # ---------------- payload for JS ----------------------------------------------
    def payload_cells(s):
        out = {}
        for c in s["cells"]:
            mo = cell_model(c)
            out.setdefault(c["reagent"], []).append({
                "d": c["desc"], "p": c["positive"], "fm": cell_forms(c["desc"]),
                "st": structure_text(c), "np": n_paths(mo),
                "pt": paths_text(c), "dy": dynamic_label(mo),
                "nf": n_fasi_of(mo),
                "s": [[x["name"], x["hex"]] for x in c["start"]],
                "e": [[x["name"], x["hex"]] for x in c["end"]]})
        return out

    payload = {
        "reagents": [{"short": r["shortName"], "full": r["fullName"], "n": cov.get(r["shortName"], 0)} for r in RG_ORDER],
        "subs": [{"name": s["name"], "url": s.get("url"), "alias": alias_of(s),
                  "cells": payload_cells(s)} for s in SUBS],
    }
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return {"rows": rows_html, "head": head_cells, "bars": bars,
            "pal": pal, "stats": stat_html, "chips": chips,
            "payload": payload_json}


def render_html():
    """La pagina completa, pronta da scrivere."""
    p = build_page_parts()
    cols = "".join("<col style='width:%dpx'>" % 152 for _ in RG_ORDER)
    return (HTML
        .replace("__CSS__", CSS).replace("__JS__", JS).replace("__PAYLOAD__", p["payload"])
        .replace("__NSUB__", str(len(SUBS)))
        .replace("__NPAIR__", str(sum(len(s["cells"]) for s in SUBS)))
        .replace("__NTRANS__", str(sum(1 for s in SUBS for c in s["cells"] if ">" in c["desc"])))
        .replace("__TODAY__", page_date(D))
        .replace("__STATS__", p["stats"]).replace("__CHIPS__", p["chips"]).replace("__BARS__", p["bars"])
        .replace("__COLS__", cols).replace("__HEAD__", p["head"]).replace("__ROWS__", "\n".join(p["rows"]))
        .replace("__PAL__", p["pal"])
        .replace("__CSVHEADER__", ";".join(CSV_COLUMNS))
        .replace("__MARCQ__", str(cov.get("Mq", 0))).replace("__MECKQ__", str(cov.get("Me", 0)))
        .replace("__MANDQ__", str(cov.get("Md", 0))).replace("__CAQ__", str(cov.get("Ca", 0)))
        .replace("__FOQ__", str(cov.get("Fo", 0))))


def write_html(path):
    out = render_html()
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("scritto:", path, "%.2f MB" % (os.path.getsize(path) / 1e6))
    return out


# === SEZIONE 5 - USCITE (i dati) ===============================================


def write_csv(path):
    """Formato lungo: una riga per record (sostanza, reattivo, descrizione, lettura)."""
    ensure_dir(path)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(CSV_COLUMNS)
        for s in SUBS:
            seen_rg = {}
            for c in s["cells"]:
                seen_rg[c["reagent"]] = seen_rg.get(c["reagent"], 0) + 1
                n = seen_rg[c["reagent"]]
                desc = re.sub(r"\s*\(\d+\)\s*$", "", c["desc"]).strip()
                parts = [p.strip() for p in desc.split(">")]
                seq = len(parts) > 1
                mo = cell_model(c)
                w.writerow([s["name"], alias_of(s), c["reagent"], COL_FULL.get(c["reagent"], ""), c["desc"],
                            cell_forms(c["desc"]), dynamic_label(mo), n,
                            str(c["positive"]).lower(), str(seq).lower(),
                            n_fasi_of(mo), n_paths(mo), structure_text(c), paths_text(c),
                            parts[0] if seq else "", parts[-1] if seq else "",
                            " > ".join("%s %s" % (x["name"], x["hex"]) for x in c["start"]),
                            " > ".join("%s %s" % (x["name"], x["hex"]) for x in c["end"]),
                            s.get("url") or ""])
    print("scritto:", path)


# === SEZIONE 6 - EXPORT SCHEMA (il formato pubblico) ===========================
#
# Formato deciso con l'utente (18 nov 2026):
#
#   sources    l'entita' di proprieta' del dato, con la sua licenza e la data in cui
#              e' stata recuperata (una fonte = un recupero: due fonti aggregate
#              possono avere due date diverse)
#   palette    i 27 colori della fonte, riorganizzati per famiglia: nessuna sfumatura
#              puo' mancare e nessuna puo' essere duplicata, perche' ogni famiglia
#              ha esattamente light / standard / dark
#   reagents   id, nome, pagina wiki e il colore PROPRIO del reattivo (la sua prima
#              osservazione, che non e' un risultato della reazione)
#   substances  nome, alias, info (pagina wiki + tipo) e le reazioni per reattivo
#   reactions  una voce per percorso osservato: la sequenza dei colori osservati,
#              [] = nessun cambio di colore, null = osservazione incoerente
#
# I testi della fonte NON vengono esportati: servono solo come criterio al momento
# dell'export (per capire se un'osservazione e' incoerente) e poi spariscono.

SHADE_BY_TONE = {"1": "light", "2": "standard", "3": "dark"}
SOURCE_ID = "PNW"
SOURCE_LABEL = "PsychonautWiki"
SOURCE_URL = "https://psychonautwiki.org"
SOURCE_LICENSE = "CC BY 4.0"


# La procedura del test: quanto tempo il campione resta nel reattivo prima della
# lettura, e se va mescolato. Durata in secondi. Per i reattivi di cui il tempo
# non e' noto il campo non viene scritto (non si inventa un valore).
REAGENT_PROCEDURE = {
    "Marquis": {"duration": 30},
    "Froehde": {"duration": 30},
    "Robadope": {"duration": 30},
    "Liebermann": {"duration": 30},
    "Mandelin": {"duration": 30},
    "Mecke": {"duration": 30},
    "Morris": {"duration": 30, "stir": True},
    "Folin": {"duration": 30},
    "Simon's": {"duration": 0},
    "Ehrlich": {"duration": 300},
    "Hofmann": {"duration": 300},
}


def color_id(name):
    """'red2' -> 'red.standard' (il nome della fonte tradotto nel riferimento)."""
    hue = name.rstrip("123")
    return "%s.%s" % (hue, SHADE_BY_TONE[name[-1]])


def build_palette():
    """La palette per famiglia: ogni famiglia ha light, standard e dark."""
    fams = {}
    for c in COLORS:
        hue = c["name"].rstrip("123")
        fams.setdefault(hue, {})[SHADE_BY_TONE[c["name"][-1]]] = c["hex"]
    return {h: {"shades": fams[h]} for h in fams}


def reagent_base_colors():
    """Il colore proprio di ciascun reattivo: la tonalita' del suo colore base piu'
    spesso osservata come prima osservazione nelle sue celle."""
    out = {}
    for r in RG:
        base = BASE_FAM.get(r["shortName"])
        if not base:
            continue
        cnt = {}
        for s in SUBS:
            for c in s["cells"]:
                if c["reagent"] != r["shortName"] or not c["start"]:
                    continue
                t = c["start"][0]
                if fam_of(canon_hex(t["hex"])) == base:
                    cnt[t["name"]] = cnt.get(t["name"], 0) + 1
        if cnt:
            out[r["shortName"]] = color_id(max(cnt.items(), key=lambda kv: kv[1])[0])
    return out


def split_top_level(text, sep=", "):
    """Splitta una lista di nomi, ma solo al livello esterno delle parentesi e solo
    su una virgola seguita da spazio: cosi' 'N,N-DMT' resta un nome solo (la
    virgola chimica non e' un separatore) mentre 'STP (Serenity, Tranquility, and
    Peace)' non si rompe."""
    out, buf, depth = [], [], 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        if depth == 0 and text.startswith(sep, i):
            out.append("".join(buf).strip())
            buf = []
            i += len(sep)
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf).strip())
    return [x for x in out if x]


def first_paren(text):
    """Il contenuto della prima parentesi di primo livello ('DOM (STP (a, b))' -> 'STP (a, b)')."""
    i = text.find("(")
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return text[i + 1:j].strip()
    return ""


def schema_aliases(s):
    """Gli alias: prima i nomi comuni della fonte (commonNames), poi quello che il
    nome grezzo porta fra parentesi. Il nome canonico non e' un alias."""
    out, seen = [], set()
    name = (s["name"] or "").lower()
    for cn in (s.get("commonNames") or []):
        cn = (cn or "").strip()
        if not cn or cn.lower() == name or cn.lower() in seen:
            continue
        seen.add(cn.lower())
        out.append(cn)
    raw = (s.get("rawName") or "").strip()
    if raw and raw.lower() != name:
        inner = first_paren(raw)
        if inner:
            # 'Nome (alias1, alias2, ...)': il nome in testa puo' essere un altro
            # alias, la parentesi puo' elencarne piu' di uno
            head = raw[:raw.find("(")].strip()
            aliases = ([head] if head.lower() != name else []) + split_top_level(inner)
        else:
            aliases = [raw]
        for alias in aliases:
            if (alias and alias.lower() != name and alias.lower() not in seen):
                seen.add(alias.lower())
                out.append(alias)
    return out


def slugify(name):
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "x"


def text_families(desc):
    """Le famiglie di colore citate dal testo della fonte (criterio, non dato esportato)."""
    out = set()
    for ph in parse(desc).get("phases", []):
        for g in ph.get("groups", []):
            for m in (g.get("colors") or []):
                if isinstance(m, dict):
                    out.update(m.get("fams") or [])
    return out


def observed_families(cell):
    out = set()
    for t in cell["start"]:
        out.add(fam_of(canon_hex(t["hex"])))
    return out


def is_incoherent(cell):
    """REGOLA B (scelta dell'utente): l'osservazione e' incoerente quando il testo
    della fonte parla di colori e i campioni registrati sono di altre famiglie
    (i due insiemi sono disgiunti). Se il testo tace un colore che il campione
    mostra, non e' un'incoerenza: e' il colore proprio del reattivo o un passaggio
    che la fonte non ha descritto."""
    ft = text_families(cell["desc"])
    fo = observed_families(cell)
    return bool(ft) and bool(fo) and not (ft & fo)


def schema_paths(mo):
    """I percorsi della cella con la sequenza dei colori OSSERVATI, nello stesso
    ordine con cui la tabella li disegna (il registro fa la spina dorsale)."""
    if mo.get("dynamic"):
        return [[color_id(t["name"]) for t in mo["dynamic"]["traj"]]]
    if mo.get("chain") is not None:
        seq = [color_id(mo["initial"]["name"])] if mo["initial"] else []
        for st in mo["chain"]:
            if st.get("kind") == "tone":
                seq.append(color_id(st["tone"]["name"]))
        return [seq]
    tracks = build_tracks(mo)
    out = []
    for tr in tracks:
        seq = [color_id(mo["initial"]["name"])] if mo["initial"] else []
        for node in tr:
            for g in node:
                for m in g.get("mentions", []):
                    for t in (m.get("tones") or []):
                        seq.append(color_id(t["name"]))
        out.append(seq)
    return out


SHAPE_BY_FORM = {"macchie": "spots", "precipitato": "precipitate",
                 "anello": "ring", "particelle": "particles"}
FIZZ_RE = re.compile(r"\b(fizz\w*|foam\w*|bubbl\w*)", re.I)


# "black or no color change": la fonte offre due esiti, uno dei quali e' l'assenza
# di reazione. Sono 3 record nel corpus (A-PHP/Zimmermann, Buprenorphine/Marquis,
# Buprenorphine/Liebermann): valgono come due osservazioni distinte, una con il
# colore e una con la sequenza vuota.
ALT_NEG_RE = re.compile(r"\bor\b[^()]{0,24}?\bno (?:colou?r change|reaction|change)\b", re.I)


def schema_reactions(cells):
    """Le voci di una coppia (sostanza, reattivo): una per percorso osservato.

    Le 21 coppie con due osservazioni della stessa fonte (testo identico, campioni
    diversi) restano distinte dal campo 'observation': senza, le loro voci
    sarebbero indistinguibili una volta appiattite nell'array."""
    out = []
    for oi, cell in enumerate(cells):
        mo = cell_model(cell)
        incoh = is_incoherent(cell)
        form = cell_forms(cell["desc"])
        shape = SHAPE_BY_FORM.get(form)
        fizz = bool(FIZZ_RE.search(cell["desc"]))
        fade = None
        dyn = mo.get("dynamic")
        if dyn and dyn.get("fade_fam"):
            fade = color_id(std_color(dyn["fade_fam"])["name"])
        seqs = schema_paths(mo)
        for seq in seqs:
            r = {"source": SOURCE_ID,
                 "colors": None if incoh else seq}
            if len(cells) > 1:
                r["observation"] = oi + 1
            if fizz:
                r["fizz"] = True
            if shape:
                r["shape"] = shape
            if fade:
                r["fade"] = fade
            out.append(r)
        # l'alternativa esplicita "colore or nessuna reazione" e' una seconda
        # osservazione, con la sequenza vuota
        if ALT_NEG_RE.search(cell["desc"]) and seqs and any(seqs) and not incoh:
            r = {"source": SOURCE_ID, "colors": []}
            if len(cells) > 1:
                r["observation"] = oi + 1
            out.append(r)
    return out


def build_schema():
    """Il dataset nel formato pubblico."""
    base = reagent_base_colors()
    reagents = []
    for r in RG_ORDER:
        rec = {"id": r["shortName"], "name": r["fullName"],
               "wiki": "%s/wiki/%s" % (SOURCE_URL, r["fullName"].replace(" ", "_"))}
        if r["shortName"] in base:
            rec["baseColor"] = base[r["shortName"]]
        proc = REAGENT_PROCEDURE.get(r["fullName"], {})
        if "duration" in proc:
            rec["duration"] = proc["duration"]
        rec["stir"] = bool(proc.get("stir"))
        reagents.append(rec)

    substances = []
    for s in SUBS:
        rec = {"id": slugify(s["name"]), "name": s["name"]}
        al = schema_aliases(s)
        if al:
            rec["aliases"] = al
        info = {"wiki": s.get("url"), "type": "Substance"}
        cls = s.get("class") or {}
        if cls.get("chemical") or cls.get("psychoactive"):
            info["class"] = {"chemical": cls.get("chemical") or [],
                             "psychoactive": cls.get("psychoactive") or []}
        rec["info"] = info
        by_rg = {}
        for c in s["cells"]:
            by_rg.setdefault(c["reagent"], []).append(c)
        rec["reactions"] = {rk: schema_reactions(cells) for rk, cells in by_rg.items()}
        substances.append(rec)

    year = 2026
    m = re.match(r"(\d{4})", (D or {}).get("fetchedAt") or "")
    if m:
        year = int(m.group(1))
    return {
        "sources": {SOURCE_ID: {"label": SOURCE_LABEL, "year": year, "url": SOURCE_URL,
                                "license": SOURCE_LICENSE,
                                "fetchedAt": (D or {}).get("fetchedAt", "")}},
        "palette": build_palette(),
        "reagents": reagents,
        "substances": substances,
    }


def write_schema(path):
    """Esporta il dataset nel formato pubblico e ne verifica l'integrita'."""
    data = build_schema()
    # ogni campione registrato deve comparire in almeno un percorso della sua coppia
    lost = 0
    entries = 0
    for s, sub in zip(SUBS, data["substances"]):
        for c in s["cells"]:
            mo = cell_model(c)
            seqs = schema_paths(mo)
            entries += len(schema_reactions([c]))
            seen = set()
            for sq in seqs:
                seen.update(sq)
            for t in c["start"]:
                if color_id(t["name"]) not in seen:
                    lost += 1
    ids = [x["id"] for x in data["substances"]]
    if len(set(ids)) != len(ids):
        raise SystemExit("slug non univoci fra le sostanze")
    if lost:
        raise SystemExit("campioni persi nell'export: %d" % lost)
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    n_null = sum(1 for s in data["substances"] for rs in s["reactions"].values()
                 for r in rs if r["colors"] is None)
    n_fizz = sum(1 for s in data["substances"] for rs in s["reactions"].values()
                 for r in rs if r.get("fizz"))
    n_shape = sum(1 for s in data["substances"] for rs in s["reactions"].values()
                  for r in rs if r.get("shape"))
    print("scritto:", path, "| sostanze: %d | reattivi: %d | voci: %d | null: %d | fizz: %d | shape: %d"
          % (len(data["substances"]), len(data["reagents"]), entries, n_null, n_fizz, n_shape))
    return data


# === SEZIONE 7 - VERIFICA =======================================================


def check(csv_path=None, html_path=None, schema_path=None):
    """Controlla le uscite: nessun campione perso, CSV allineato, HTML coerente.
    Ritorna True se tutto torna (il main() ne fa l'exit code)."""
    ok = True
    csv_path = csv_path or DEFAULT_CSV
    # --- i campioni registrati devono comparire tutti nel rendering --------------
    total = lost = cells_with_flow = 0
    for s in SUBS:
        for c in s["cells"]:
            h = render_flow(c, "full")
            mo = cell_model(c)
            if (c["start"] or c["end"] or mo["initial"] or mo["extras"]
                    or mo.get("dynamic") or any(ph["groups"] for ph in mo["phases"])):
                cells_with_flow += 1
            seen = []
            for t in c["start"]:
                if t["hex"] not in seen:
                    seen.append(t["hex"])
            for hx in seen:
                total += 1
                if ("background:%s" % hx) not in h:
                    lost += 1
                    print("   PERSO", s["name"], c["reagent"], c["desc"], hx)
    print("campioni unici attesi: %d   persi: %d   celle con flusso: %d" % (total, lost, cells_with_flow))
    ok &= (lost == 0)

    # --- i composti devono mostrare tutte le famiglie citate ---------------------
    comp = comp_ok = 0
    for s in SUBS:
        for c in s["cells"]:
            p = parse(c["desc"])
            if not any(len(m["fams"]) > 1 for ph in p["phases"] for g in ph["groups"] for m in g["colors"]):
                continue
            comp += 1
            fams = [f for ph in p["phases"] for g in ph["groups"] for m in g["colors"] for f in m["fams"]]
            if all(FAM_IT.get(f, f) in structure_text(c) for f in set(fams)):
                comp_ok += 1
    print("celle con composto: %d   con tutti i rami presenti: %d" % (comp, comp_ok))
    ok &= (comp == comp_ok)

    # --- il CSV ------------------------------------------------------------------
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8-sig") as f:
            rows = list(csv.reader(f, delimiter=";"))
        print("CSV: %d righe (1+%d)   %d colonne" % (len(rows), len(rows) - 1, len(rows[0])))
        n_rec = sum(len(s["cells"]) for s in SUBS)
        ok &= (len(rows) == n_rec + 1 and len(rows[0]) == len(CSV_COLUMNS))
        ok &= (rows[0] == CSV_COLUMNS)
        # la colonna 'forma' deve coincidere col testo
        bad = 0
        for r in rows[1:]:
            desc = re.sub(r"\s*\(\d+\)\s*$", "", r[4]).strip()
            if cell_forms(desc) != r[5]:
                bad += 1
        print("disallineamenti forma:", bad)
        ok &= (bad == 0)
    else:
        print("CSV non trovato:", csv_path)
        ok = False

    # --- l'export schema (solo se e' stato scritto) ------------------------------
    if schema_path and os.path.exists(schema_path):
        sc = json.load(open(schema_path, encoding="utf-8"))
        hex_by_id = {}
        for hue, h in sc["palette"].items():
            for shade, hexv in h["shades"].items():
                hex_by_id["%s.%s" % (hue, shade)] = hexv
        n_e = n_bad = n_null = 0
        for s in SUBS:
            sub = next((x for x in sc["substances"] if x["name"] == s["name"]), None)
            if sub is None:
                n_bad += 1
                continue
            by_rg = {}
            for c in s["cells"]:
                by_rg.setdefault(c["reagent"], []).append(c)
            for rk, cells in by_rg.items():
                exp = schema_reactions(cells)
                got = sub["reactions"].get(rk, [])
                n_e += len(got)
                n_null += sum(1 for r in got if r["colors"] is None)
                if len(exp) != len(got):
                    n_bad += 1
                    print("   NUMERO DI VOCI DIVERSO", s["name"], rk, len(exp), len(got))
                    continue
                for e, g in zip(exp, got):
                    if e["colors"] != g["colors"] or e.get("observation") != g.get("observation"):
                        n_bad += 1
                        print("   SCORRETTO", s["name"], rk, e, g)
                        continue
                    # i colori della voce devono essere campioni registrati
                    for cid in (g["colors"] or []):
                        if hex_by_id.get(cid) not in [x["hex"] for c in cells for x in c["start"]]:
                            n_bad += 1
                            print("   COLORE NON REGISTRATO", s["name"], rk, cid)
        print("schema: %d voci | null: %d | colori non presenti fra i campioni: %d" % (n_e, n_null, n_bad))
        ok &= (n_bad == 0)

    # --- l'HTML (solo se e' stato scritto) ---------------------------------------
    if html_path and os.path.exists(html_path):
        h = open(html_path, encoding="utf-8").read()
        body = re.search(r"<tbody[^>]*>(.*?)</tbody>", h, re.S)
        trs = re.findall(r"<tr[^>]*>.*?</tr>", body.group(1), re.S) if body else []
        tds = re.findall(r"<td[^>]*class='c[^']*'[^>]*>", h)
        print("HTML: %d righe   %d celle" % (len(trs), len(tds)))
        ok &= (len(trs) == len(SUBS) and len(tds) == len(SUBS) * len(COLS))
    print("OK" if ok else "FALLITO")
    return bool(ok)


# === MAIN =======================================================================


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Scarica, normalizza e salva i dati semantici di PsychonautWiki "
                    "(CC BY 4.0); con --html esporta anche la tabella visuale.")
    ap.add_argument("--data", default=DEFAULT_DATA, help="percorso del dataset normalizzato")
    ap.add_argument("--csv", default=DEFAULT_CSV, help="percorso del CSV (formato lungo)")
    ap.add_argument("--html", nargs="?", const=DEFAULT_HTML, default=None,
                    help="esporta anche la tabella HTML (con --html PATH si sceglie dove)")
    ap.add_argument("--schema", nargs="?", const=DEFAULT_SCHEMA, default=None,
                    help="esporta anche il dataset nel formato pubblico (JSON)")
    ap.add_argument("--offline", action="store_true", help="non riscarica: riusa il data.json locale")
    ap.add_argument("--no-csv", action="store_true", help="non scrivere il CSV")
    ap.add_argument("--check", action="store_true", help="verifica le uscite (exit 1 se non tornano)")
    args = ap.parse_args(argv)

    if args.offline:
        if not os.path.exists(args.data):
            print("non trovo il dataset locale:", args.data, "\n"
                  "togli --offline per scaricarlo dalla rete.", file=sys.stderr)
            return 2
        with open(args.data, encoding="utf-8") as f:
            data = json.load(f)
        print("dato locale:", args.data, "|", data.get("fetchedAt", ""))
    else:
        data = fetch_data()
        save_data(data, args.data)
    load_state(data)

    if not args.no_csv:
        write_csv(args.csv)
    if args.html:
        write_html(args.html)
    if args.schema:
        write_schema(args.schema)
    if args.check:
        return 0 if check(args.csv, args.html, args.schema) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
