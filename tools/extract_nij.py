#!/usr/bin/env python3
"""Estrae i colori dello standard NIJ 0604.01.

"Color Test Reagents/Kits for Preliminary Identification of Drugs of Abuse",
NIJ Standard-0604.01 (luglio 2000, NCJ 183258), ha due tabelle di colori:

- la tabella 1, il colore finale di ogni reagente con farmaci, droghe e altre
  sostanze, con il nome ISCC-NBS e la notazione Munsell;
- la tabella 3, la specificita': per 27 sostanze, soprattutto non
  controllate, un + o un - per ogni reagente. Un - e' "nessuna reazione". La
  sua nota aggiunge sei sostanze che non danno colore con nessun reagente.

Dei dodici reagenti dello standard entrano quelli della pagina: Mandelin,
Marquis, Froehde, Mecke, Simon's, e il p-DMAB come Ehrlich, che e' lo stesso
reattivo. Cobalto tiocianato, Dille-Koppanyi, Duquenois-Levine, acido
nitrico, cloruro ferrico e Zwikker restano fuori.

E' una pubblicazione del governo degli Stati Uniti; la revisione del 2000 e'
stata fatta all'Universita' dello Utah. Lo script ne prende solo i fatti, la
coppia sostanza-reagente e il suo colore, e ne riscrive i nomi come colori
della palette con le regole di tools/colour_names.py.

    python3 tools/extract_nij.py            # scarica (se serve) ed estrae
    python3 tools/extract_nij.py --offline  # usa solo il file in sources/cache/
"""
from __future__ import annotations

import argparse
import re

from source_schema import (add_observations, download, fetched_at, pdf_text, readings,
                           substance, write)

SOURCE_ID = "NIJ"
SOURCE = {
    "label": "NIJ Standard-0604.01",
    "year": 2000,
    "url": "https://www.ojp.gov/pdffiles1/nij/183258.pdf",
    "license": "US government publication (facts only)",
    "script": "tools/extract_nij.py",
}
PDF = ("https://www.ojp.gov/pdffiles1/nij/183258.pdf", "nij-0604-01.pdf",
       "7a0faa664ddaf69f34c28ee2ce9c6103000ccefc5fca07acc7e62c992dc9dcd3")

# il numero del reagente nell'appendice A -> il reagente della pagina
REAGENTS = {4: "Md", 5: "Mq", 7: "Eh", 9: "Fr", 10: "Me", 12: "Si"}
REAGENT_COUNT = 12

# Il nome nello standard -> (il nome della sostanza, il tipo, gli alias). Il
# nome e' quello di PsychonautWiki quando c'e', perche' build_data.py le unisca.
# Lo standard scrive due nomi in due modi: "Acetominophen" ed "Exedrine".
SUBSTANCES = {
    "Acetaminophen": ("Paracetamol", "Adulterant", ["Acetaminophen", "APAP"]),
    "Acetominophen": ("Paracetamol", "Adulterant", ["Acetaminophen", "APAP"]),
    "Alprazolam": ("Alprazolam", "Substance", []),
    "Amobarbital": ("Amobarbital", "Substance", []),
    "Aspirin": ("Aspirin", "Adulterant", ["Acetylsalicylic acid"]),
    "Baking Soda": ("Sodium bicarbonate", "Adulterant", ["Baking soda"]),
    "Benzphetamine HCl": ("Benzphetamine", "Substance", []),
    "Brompheniramine Maleate": ("Brompheniramine", "Substance", []),
    "Chlordiazepoxide HCl": ("Chlordiazepoxide", "Substance", ["Librium"]),
    "Chlorpromazine HCl": ("Chlorpromazine", "Substance", []),
    "Cocaine HCl": ("Cocaine", "Substance", []),
    "Codeine": ("Codeine", "Substance", []),
    "Contac": ("Contac", "Substance", []),
    "d-Amphetamine HCl": ("Amphetamine", "Substance", []),
    "d-Methamphetamine HCl": ("Methamphetamine", "Substance", []),
    "Diacetylmorphine HCl": ("Heroin", "Substance", []),
    "Diazepam": ("Diazepam", "Substance", []),
    # 2,5-dimetossi-4-metilanfetamina: lo standard del 1981 la chiama STP
    "Dimethoxy-meth HCl": ("DOM", "Substance", []),
    "Doxepin HCl": ("Doxepin", "Substance", []),
    "Dristan": ("Dristan", "Substance", []),
    "Ephedrine HCl": ("Ephedrine", "Substance", []),
    "Exedrine": ("Excedrin", "Substance", []),
    "Hydrocodone tartrate": ("Hydrocodone", "Substance", []),
    "LSD": ("LSD", "Substance", []),
    # la nota 5 dello standard: e' il gas lacrimogeno, non la spezia
    "Mace": ("2-Chloroacetophenone", "Substance", ["Mace", "CN", "Phenacyl chloride"]),
    "MDA HCl": ("MDA", "Substance", []),
    "MDMA HCl": ("MDMA", "Substance", []),
    "Meperidine HCl": ("Pethidine", "Substance", []),
    "Mescaline HCl": ("Mescaline", "Substance", []),
    "Methadone HCl": ("Methadone", "Substance", []),
    "Methaqualone": ("Methaqualone", "Substance", []),
    "Methylphenidate HCl": ("Methylphenidate", "Substance", []),
    "Morphine monohydrate": ("Morphine", "Substance", []),
    "Nutmeg": ("Nutmeg", "Substance", []),
    "Opium": ("Opium", "Substance", []),
    "Oxycodone HCl": ("Oxycodone", "Substance", []),
    "Pentobarbital": ("Pentobarbital", "Substance", []),
    "Phenobarbital": ("Phenobarbital", "Substance", []),
    "Phencyclidine HCl": ("PCP", "Substance", []),
    "Procaine HCl": ("Procaine", "Adulterant", ["Novocaine"]),
    "Propoxyphene HCl": ("Dextropropoxyphene", "Substance", []),
    "Pseudoephedrine HCl": ("Pseudoephedrine", "Substance", []),
    "Quinine HCl": ("Quinine", "Adulterant", []),
    "Salt": ("Sodium chloride", "Adulterant", ["Salt"]),
    "Secobarbital": ("Secobarbital", "Substance", []),
    "Sugar": ("Sucrose", "Adulterant", ["Sugar", "Table sugar"]),
    "Tea": ("Tea", "Substance", []),
    "THC": ("Tetrahydrocannabinol", "Substance", []),
    "Tobacco": ("Tobacco", "Substance", []),
    # la nota della tabella 3
    "D-galactose": ("Galactose", "Adulterant", []),
    "glucose": ("Glucose", "Adulterant", ["Dextrose"]),
    "mannitol": ("Mannitol", "Adulterant", []),
    "oregano": ("Oregano", "Substance", []),
    "rosemary": ("Rosemary", "Substance", []),
    "thyme": ("Thyme", "Substance", []),
}

ROW = re.compile(r"^A\.(\d+)\s+(.+)$")
# la notazione Munsell in fondo al nome del colore, quando la riga non ha
# lasciato le due colonne separate: "Strong reddish orange 10R 6/12 to"
MUNSELL = re.compile(r"\s+(?:\d+(?:\.\d+)?[A-Z]+\s+\d+(?:\.\d+)?/\d+|Black)$")


def analyte(name: str) -> str:
    """Il nome senza l'asterisco del reagente d'uso e senza il numero della nota."""
    return re.sub(r"\d+$", "", name.replace("*", "").strip()).strip()


def table_one(text: str) -> dict[tuple[str, int], list[list[str]]]:
    """(sostanza, reagente) -> le tappe del colore finale.

    Due righe vanno lette con la successiva: "35 to ... 44" e' un colore che
    passa in un altro, "Dark grayish reddish" va a capo su "Brown".
    """
    start = text.index("Table 1. Final colors")
    end = text.index("* Usual kit reagent", start)
    rows: dict[tuple[str, int], list[list[str]]] = {}
    current: list[list[str]] | None = None
    continues = False
    for line in text[start:end].splitlines():
        match = ROW.match(line.strip())
        if match:
            reagent = int(match.group(1))
            fields = re.split(r"\s{2,}", match.group(2).strip())
            name, colour = analyte(fields[0]), fields[3] if len(fields) > 3 else ""
            # il "to" sta in fondo alla riga: dopo il colore o dopo il Munsell
            continues = line.rstrip().endswith(" to")
            colour = MUNSELL.sub("", re.sub(r"\s+to$", "", colour))
            key = (name, reagent)
            if key in rows:
                raise SystemExit(f"riga ripetuta: {key}")
            current = rows[key] = [[colour]]
            continue
        fields = re.split(r"\s{2,}", line.strip())
        if current is None or not line.strip():
            continue
        if continues and len(fields) >= 2 and fields[0].isdigit():
            # la seconda tappa: "44  Dark reddish brown  7.5R 2/4"
            current.append([fields[1]])
            continues = False
        elif re.fullmatch(r"[A-Z][a-z]+", line.strip()):
            # il nome del colore andato a capo: "Brown"
            current[-1][-1] += " " + line.strip()
    return rows


def table_three(text: str) -> dict[str, list[bool]]:
    """Sostanza -> per ogni reagente, se da' un colore."""
    start = text.index("Table 3. Specificity of color tests")
    end = text.index("APPENDIX A", start)
    out = {}
    for line in text[start:end].splitlines():
        match = re.match(r"^\s*(\S.*?)\s{2,}((?:[+-]\s+){%d}[+-])\s*$" % (REAGENT_COUNT - 1), line)
        if match:
            out[analyte(match.group(1))] = [sign == "+" for sign in match.group(2).split()]
    return out


def no_colours(text: str) -> list[str]:
    """Le sostanze della nota della tabella 3: nessun colore con nessun reagente."""
    match = re.search(r"Substances that gave no colors with these reagents are:\s*(.+?)\.",
                      text, re.S)
    names = re.split(r",\s*(?:and\s+)?", " ".join(match.group(1).split()))
    return [name.strip() for name in names]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    text = pdf_text(download(*PDF, offline=args.offline))
    colours = table_one(text)
    specificity = table_three(text)
    negatives = no_colours(text)
    print(f"tabella 1: {len(colours)} righe | tabella 3: {len(specificity)} sostanze | "
          f"nota: {', '.join(negatives)}")

    unknown = ({name for name, _ in colours} | set(specificity) | set(negatives)) - set(SUBSTANCES)
    if unknown:
        raise SystemExit(f"sostanze da nominare: {sorted(unknown)}")

    # la tabella 3 e la tabella 1 devono dire la stessa cosa: un + ha il suo
    # colore, un - non ce l'ha (per sostanza, perche' le tabelle scrivono i
    # nomi in modo diverso). Solo per i reagenti della pagina: per l'acido
    # nitrico la tabella 3 da' un + alla clorpromazina che la tabella 1 non ha.
    coloured = {(SUBSTANCES[name][0], reagent) for name, reagent in colours}
    for name, signs in specificity.items():
        for index, positive in enumerate(signs):
            if index + 1 in REAGENTS and positive != ((SUBSTANCES[name][0], index + 1) in coloured):
                raise SystemExit(f"tabelle 1 e 3 in disaccordo: {name}, A.{index + 1}")

    records: dict[str, dict] = {}

    def add(name: str, reagent: int, stages: list[list[str]]) -> None:
        if reagent not in REAGENTS:
            return
        canonical, kind, aliases = SUBSTANCES[name]
        record = records.setdefault(canonical, substance(canonical, kind, aliases))
        reagent_id = REAGENTS[reagent]
        add_observations(record["reactions"], reagent_id,
                         [readings(SOURCE_ID, reagent_id, stages)])

    for (name, reagent), stages in colours.items():
        add(name, reagent, stages)
    for name, signs in specificity.items():
        for index, positive in enumerate(signs):
            if not positive:
                add(name, index + 1, [])
    for name in negatives:
        for reagent in REAGENTS:
            add(name, reagent, [])

    write(SOURCE_ID, {**SOURCE, "fetchedAt": fetched_at()}, list(records.values()))


if __name__ == "__main__":
    main()
