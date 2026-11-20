"""Quello che gli estrattori delle fonti hanno in comune.

Ogni estrattore (tools/extract_*.py) scarica una fonte, ne legge i colori e
scrive sources/<fonte>.json nello schema di sources/PNW.json, ma solo con
"sources" e "substances", e ogni sostanza solo con l'id e le reazioni: la
palette e i reagenti sono quelli di PsychonautWiki, il resto della sostanza
viene dal vocabolario (tools/vocabulary.py). tools/build_data.py unisce poi
tutte le fonti.

I file scaricati restano in sources/cache/, fuori dal repository come i file
che ne escono: si rifanno da capo lanciando gli estrattori.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from colour_names import palette_colours

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "sources"
CACHE = SOURCES / "cache"
USER_AGENT = "reagent-color-chart/1.0 (tools/extract_*.py)"

# Il colore proprio del reagente, la goccia prima della reazione: le letture
# di PsychonautWiki lo registrano come prima tappa, e le altre fonti fanno lo
# stesso perche' la pagina lo riconosca. build_data.py verifica che sia lo
# stesso "baseColor" del dataset di PsychonautWiki.
BASE_COLOURS = {"Md": "yellow.standard", "Si": "orange.light"}


def download(url: str, name: str, sha256: str | None = None, offline: bool = False) -> Path:
    """Il file all'url, scaricato in sources/cache/<name> se non c'e' gia'.
    Con l'hash, un file diverso da quello pubblicato ferma l'estrazione."""
    path = CACHE / name
    if not path.exists():
        if offline:
            raise SystemExit(f"manca {path}: lancia lo script senza --offline")
        CACHE.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            path.write_bytes(response.read())
        print(f"scaricato {url}")
    if sha256:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != sha256:
            raise SystemExit(f"{path}: sha256 {digest}, la fonte dichiara {sha256}")
    return path


def pdf_text(path: Path) -> str:
    """Il testo di un PDF, con l'impaginazione (pdftotext, da poppler-utils)."""
    result = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                            capture_output=True, text=True, check=True)
    return result.stdout


def readings(source: str, reagent: str, stages: list[list[str]]) -> list[dict]:
    """Le letture di una osservazione: una per percorso di colori.

    stages e' la sequenza dei nomi delle alternative di ogni tappa; ogni nome
    vale per tutte le famiglie che nomina, quindi una tappa "Pink-orange"
    seguita da "Brown" da' due letture: rosa poi marrone, arancione poi
    marrone. Nessuna tappa e' "nessuna reazione".
    """
    paths: list[list[str]] = [[]]
    for stage in stages:
        alternatives = [colour for name in stage for colour in palette_colours(name)]
        # due tappe uguali di seguito sono una tappa sola: "rosso" poi "rosso"
        # non e' un cambio di colore
        paths = [path + [colour] if path[-1:] != [colour] else path
                 for path in paths for colour in dict.fromkeys(alternatives)]
    base = BASE_COLOURS.get(reagent)
    out = []
    for path in [list(unique) for unique in dict.fromkeys(map(tuple, paths))]:
        colours = [base] + path if base and path else path
        out.append({"source": source, "colors": colours})
    return out


def add_observations(reactions: dict, reagent: str, observations: list[list[dict]]) -> None:
    """Aggiunge le letture di piu' osservazioni della stessa coppia, ognuna
    una volta sola: "Green" alla prima prova e "Blue-Green" alla seconda sono
    verde e blu, non verde due volte. La pagina mostra le letture, non le
    osservazioni che le hanno date."""
    entries = reactions.setdefault(reagent, [])
    for observation in observations:
        for reading in observation:
            if reading not in entries:
                entries.append(dict(reading))


def substance(substance_id: str) -> dict:
    """Una sostanza della fonte: l'id del vocabolario e le sue reazioni."""
    return {"id": substance_id, "reactions": {}}


def fetched_at() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def write(source_id: str, source: dict, substances: list[dict]) -> Path:
    path = SOURCES / f"{source_id}.json"
    SOURCES.mkdir(parents=True, exist_ok=True)
    data = {"sources": {source_id: source}, "substances": substances}
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    count = sum(len(entries) for record in substances for entries in record["reactions"].values())
    print(f"scritto {path} | sostanze {len(substances)} | letture {count}")
    return path
