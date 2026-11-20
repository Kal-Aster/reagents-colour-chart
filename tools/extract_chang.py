#!/usr/bin/env python3
"""Estrae i colori di Chang et al. 2025.

"Presumptive Tests for Xylazine - A Computer Vision Approach" (Chang et al.,
Analytical Science Advances, 2025, doi:10.1002/ansa.70008) prova 14 polveri
con Marquis, Mandelin e Mecke e confronta a occhio il colore finale con il
catalogo RAL: le tabelle 3, 4 e 5. L'articolo e' CC BY 4.0; lo script legge
il testo da Europe PMC e verifica la licenza prima di estrarre.

La tabella 2 dello stesso articolo non entra: riassume la letteratura, non
quello che gli autori hanno visto.

    python3 tools/extract_chang.py            # scarica (se serve) ed estrae
    python3 tools/extract_chang.py --offline  # usa solo il file in sources/cache/
"""
from __future__ import annotations

import argparse
import xml.etree.ElementTree as ElementTree

from source_schema import add_observations, download, fetched_at, readings, substance, write

SOURCE_ID = "Chang2025"
SOURCE = {
    "label": "Chang et al., Analytical Science Advances",
    "year": 2025,
    "url": "https://doi.org/10.1002/ansa.70008",
    "license": "CC BY 4.0",
    "script": "tools/extract_chang.py",
}
XML = ("https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11961553/fullTextXML",
       "chang-2025.xml")
LICENSE_URL = "creativecommons.org/licenses/by/4.0"

# la tabella -> il reagente
TABLES = {"TABLE 3": "Mq", "TABLE 4": "Md", "TABLE 5": "Me"}
NO_CHANGE = "None"
ARROW = "−→"

# Il nome nell'articolo -> (il nome della sostanza, il tipo, gli alias). Il
# nome e' quello di PsychonautWiki quando c'e', perche' build_data.py le unisca.
SUBSTANCES = {
    "Xylazine": ("Xylazine", "Adulterant", []),
    "Amph.H2SO4": ("Amphetamine", "Substance", []),
    "Amphetamine": ("Amphetamine", "Substance", []),
    "Methamph.HCl": ("Methamphetamine", "Substance", []),
    "Methamphetamine": ("Methamphetamine", "Substance", []),
    "MDMA": ("MDMA", "Substance", []),
    "Morphine.HCl": ("Morphine", "Substance", []),
    "Morphine": ("Morphine", "Substance", []),
    "Sucrose": ("Sucrose", "Adulterant", ["Sugar", "Table sugar"]),
    "Caffeine": ("Caffeine", "Adulterant", []),
    "Diazepam": ("Diazepam", "Substance", []),
    "Lorazepam": ("Lorazepam", "Substance", []),
    "Oxazepam": ("Oxazepam", "Substance", []),
    "Cocaine.HCl": ("Cocaine", "Substance", []),
    "Codeine": ("Codeine", "Substance", []),
    "Diamorphine.HCl": ("Heroin", "Substance", []),
    "Paracetamol": ("Paracetamol", "Adulterant", ["Acetaminophen", "APAP"]),
}


def text_of(element: ElementTree.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    root = ElementTree.parse(download(*XML, offline=args.offline)).getroot()
    licences = [link.get("{http://www.w3.org/1999/xlink}href", "")
                for licence in root.iter("license") for link in licence.iter("ext-link")]
    if not any(LICENSE_URL in href for href in licences):
        raise SystemExit(f"la licenza dell'articolo non e' piu' CC BY 4.0: {licences}")

    records: dict[str, dict] = {}
    found = set()
    for wrap in root.iter("table-wrap"):
        label = text_of(wrap.find("label")) if wrap.find("label") is not None else ""
        if label not in TABLES:
            continue
        found.add(label)
        reagent = TABLES[label]
        rows = [[text_of(cell) for cell in row] for row in wrap.iter("tr")]
        for sample, change, _, _ in rows[1:]:
            if sample not in SUBSTANCES:
                raise SystemExit(f"{label}: sostanza da nominare: {sample!r}")
            if change == NO_CHANGE:
                stages = []
            elif ARROW in change:
                # il colore di partenza e' il reagente: incolore, o il giallo
                # del Mandelin che readings() aggiunge da se'
                stages = [[change.split(ARROW, 1)[1].strip()]]
            else:
                raise SystemExit(f"{label}: cambio di colore illeggibile: {change!r}")
            name, kind, aliases = SUBSTANCES[sample]
            record = records.setdefault(name, substance(name, kind, aliases))
            add_observations(record["reactions"], reagent, [readings(SOURCE_ID, reagent, stages)])
    if found != set(TABLES):
        raise SystemExit(f"tabelle mancanti: {sorted(set(TABLES) - found)}")

    write(SOURCE_ID, {**SOURCE, "fetchedAt": fetched_at()}, list(records.values()))


if __name__ == "__main__":
    main()
