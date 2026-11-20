#!/usr/bin/env python3
"""Estrae i colori dei campioni puri del NIST/NIJ CADS.

Il dataset "NIST/NIJ Characterized Authentic Drug Sample (CADS) Project"
(doi:10.18434/mds2-3627) raccoglie i referti di analisi di campioni
sequestrati: ognuno ha in fondo i test colorimetrici con cobalto tiocianato,
Froehde, Marquis, Mecke e Simon's, ripetuti due volte.

Lo script prende solo i campioni con un composto solo: in una miscela il
colore non si puo' attribuire a un componente, e nemmeno la sua assenza (la
miscela CADS 030 col saccarosio non reagisce al Marquis, il saccarosio puro
si'). Il cobalto tiocianato resta fuori: non e' lo Scott ne' il Morris della
pagina, ma la loro base comune, e da' blu con quasi tutte le ammine.

I dati sono di dipendenti del NIST: negli Stati Uniti non hanno copyright
(17 U.S.C. 105) e il NIST ne concede ovunque l'uso, chiedendo di citarlo e di
dire che cosa e' stato cambiato. Qui i nomi dei colori diventano colori della
palette con le regole di tools/colour_names.py; i testi originali non sono
riportati.

    python3 tools/extract_cads.py            # scarica (se serve) ed estrae
    python3 tools/extract_cads.py --offline  # usa solo i file in sources/cache/
"""
from __future__ import annotations

import argparse
import re
import zipfile

from source_schema import (CACHE, add_observations, download, fetched_at, pdf_text,
                           readings, substance, write)
from vocabulary import Vocabulary

SOURCE_ID = "CADS"
SOURCE = {
    "label": "NIST/NIJ CADS",
    "year": 2026,
    "url": "https://doi.org/10.18434/mds2-3627",
    "license": "NIST (public domain in the US)",
    "script": "tools/extract_cads.py",
}
# i file del dataset, con lo sha256 che il NIST pubblica nella sua scheda
ARCHIVES = [
    ("https://data.nist.gov/od/ds/mds2-3627/CADS%20Panel%201%20Reports.zip",
     "cads-panel-1.zip", "0ebbe88fbd17a2e6603e6933616119b283cb891a1a026513579d0037f6fb5932"),
    ("https://data.nist.gov/od/ds/mds2-3627/Panel%202%20Reports.zip",
     "cads-panel-2.zip", "68a64f61c238c68472d86612e6dc0debe27fb2641a69c182e8f4643bd6ca1b3b"),
]
REAGENTS = {"Marquis": "Mq", "Mecke": "Me", "Froehde": "Fr", "Simon’s": "Si"}
NO_COLOUR_CHANGE = "NCC"
NOT_PERFORMED = "NP"

# I campioni puri: il campione -> il nome della sostanza come compare nel
# referto, che e' un alias nel vocabolario (data/substances.json). Un campione
# puro che manca da questo elenco ferma lo script: va nominato a mano.
PURE_SAMPLES = {
    "CADS 009": "2-Fluoro deschloroketamine",
    "CADS 014": "Methamphetamine",
    "CADS 015": "Methamphetamine",
    "CADS 016": "Tianeptine",
    "CADS 017": "Pyrrolidinoisohexanophenone",
    "CADS 020": "BMDP",
    "CADS 021": "FUB-AMB",
    "CADS 022": "N-Ethyl Pentedrone",
    "CADS 026": "4-cyano CUMYL-BUTINACA",
    "CADS 028": "Eutylone",
    "CADS 031": "Tadalafil",
    "CADS 035": "Valeryl fentanyl",
    "CADS 038": "Cocaine base",
    "CADS 039": "Aniracetam",
    "CADS 041": "Adrafinil",
    "CADS 045": "4-Fluoro ABUTINACA",
    "CADS 046": "Methylenedioxymethamphetamine",
}

# una formula chimica nel riepilogo; "Variable" e' la carbossimetilcellulosa
FORMULA = re.compile(r"(?<![A-Za-z0-9])\(?[A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+\)?n?(?![A-Za-z0-9])"
                     r"|\bVariable\b")
# dove sta il colore, che la pagina non registra
WHERE = re.compile(r"\s+(?:on|around)\s+edges(?:\s+of\s+powder)?$", re.I)


def compounds(text: str) -> set[str]:
    """Le formule dei composti nel riepilogo, senza le righe del sale (lo
    stesso composto della base)."""
    summary = text.split("Compound Name", 1)[1].split("Physical characteristics", 1)[0]
    found = set()
    for line in summary.splitlines():
        if "(salt)" in line:
            continue
        for match in FORMULA.finditer(line):
            formula = match.group(0)
            if re.search(r"\d", formula) or formula == "Variable":
                found.add(formula)
    return found


def colour_results(text: str) -> dict[str, list[str]]:
    """Reagente -> i risultati delle due ripetizioni, come li scrive il referto."""
    table = text.split("Color Test Name", 1)[1].split(f"{NO_COLOUR_CHANGE}-", 1)[0]
    results = {}
    for line in table.splitlines():
        for name in REAGENTS:
            match = re.match(rf"\s*{re.escape(name)}\s{{2,}}(.+)$", line)
            if match:
                values = re.split(r"\s{2,}", match.group(1).strip())
                if len(values) != 2:
                    raise SystemExit(f"{name}: attese due ripetizioni, trovate {values}")
                results[name] = values
    return results


def stages(value: str) -> list[list[str]]:
    """Il risultato di una ripetizione come tappe: nessuna se non cambia colore."""
    if value == NO_COLOUR_CHANGE:
        return []
    return [[WHERE.sub("", value)]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    reports = {}
    for url, name, sha256 in ARCHIVES:
        archive = download(url, name, sha256, args.offline)
        with zipfile.ZipFile(archive) as opened:
            for member in opened.namelist():
                if not member.lower().endswith(".pdf"):
                    continue
                # solo il nome del file, mai il percorso dentro l'archivio
                path = CACHE / "cads" / member.rsplit("/", 1)[-1]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(opened.read(member))
                text = pdf_text(path)
                sample = re.search(r"Sample:\s*(CADS \d+)", text).group(1)
                reports[sample] = text
    print(f"referti {len(reports)}")

    pure = {sample for sample, text in reports.items() if len(compounds(text)) == 1}
    if pure != set(PURE_SAMPLES):
        raise SystemExit(f"campioni puri da nominare: {sorted(pure - set(PURE_SAMPLES))}, "
                         f"non piu' puri: {sorted(set(PURE_SAMPLES) - pure)}")

    vocabulary = Vocabulary()
    records: dict[str, dict] = {}
    observations: dict[tuple[str, str], list[list[dict]]] = {}
    for sample in sorted(pure):
        label = PURE_SAMPLES[sample]
        text = reports[sample]
        if label.lower() not in text.lower():
            raise SystemExit(f"{sample}: il referto non nomina {label!r}")
        name = vocabulary.resolve(SOURCE_ID, label)
        if name is None:
            continue
        records.setdefault(name, substance(name))
        for reagent_name, values in colour_results(text).items():
            for value in values:
                if value == NOT_PERFORMED:
                    continue
                observation = readings(SOURCE_ID, REAGENTS[reagent_name], stages(value))
                observations.setdefault((name, REAGENTS[reagent_name]), []).append(observation)
    for (name, reagent), found in observations.items():
        add_observations(records[name]["reactions"], reagent, found)

    vocabulary.finish()
    write(SOURCE_ID, {**SOURCE, "fetchedAt": fetched_at()}, list(records.values()))


if __name__ == "__main__":
    main()
