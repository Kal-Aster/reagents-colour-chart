"""Il vocabolario delle sostanze: a quale sostanza va un nome di una fonte.

data/substances.json e' l'anagrafica delle sostanze della pagina: per ognuna
l'id, il nome, il tipo, la voce di PsychonautWiki, la classe e gli alias, cioe'
tutti i nomi raccolti dalle fonti e i nomi di strada. Gli estrattori non
scrivono sostanze, solo reazioni legate a un id: build_data.py le compone.

Un nome di una fonte si cerca cosi':
1. data/name-conflicts.json, che lega a mano una coppia fonte-nome a un id;
2. il nome e gli alias del vocabolario, senza distinguere maiuscole e
   minuscole: se il nome e' di una sola sostanza, e' quella.

Gli alias possono essere ambigui ("speed" e' l'anfetamina e la
metanfetamina): servono alla ricerca nella pagina. "rejected" sono i nomi che
una fonte da' a una sostanza e che non sono suoi ("tea" per la caffeina): non
sono alias e non generano avvisi.

Un nome ambiguo o sconosciuto pero' ferma l'estrazione, che dice dove
aggiungerlo: una reazione non va mai a una sostanza indovinata.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBSTANCES = ROOT / "data" / "substances.json"
CONFLICTS = ROOT / "data" / "name-conflicts.json"


def load() -> list[dict]:
    return json.loads(SUBSTANCES.read_text(encoding="utf-8"))["substances"]


class Vocabulary:
    def __init__(self) -> None:
        self.substances = load()
        self.by_id = {substance["id"]: substance for substance in self.substances}
        self.conflicts = json.loads(CONFLICTS.read_text(encoding="utf-8"))
        self.by_name: dict[str, set[str]] = {}
        for substance in self.substances:
            for name in [substance["name"], *substance.get("aliases", [])]:
                self.by_name.setdefault(name.lower(), set()).add(substance["id"])
        self.errors: list[str] = []
        self.new_aliases: dict[str, set[str]] = {}

    def resolve(self, source: str, name: str, lookup: str | None = None) -> str | None:
        """L'id della sostanza a cui va il nome; None, con l'errore annotato,
        se il nome non c'e' o e' ambiguo. finish() li dice tutti insieme.

        "lookup" e' il nome da cercare fra nomi e alias, quando non e' quello
        della fonte: per PsychonautWiki "Cocaine" di "Cocaine (Crack)". Il file
        dei conflitti usa sempre il nome della fonte, intero."""
        resolved = self.conflicts.get(source, {}).get(name)
        if resolved:
            if resolved not in self.by_id:
                self.errors.append(f"{CONFLICTS.name}: {source} {name!r} -> {resolved!r}, "
                                   "che non e' nel vocabolario")
                return None
            return resolved
        found = self.by_name.get((lookup or name).lower(), set())
        if len(found) == 1:
            return next(iter(found))
        if found:
            self.errors.append(f"{source} {name!r} e' ambiguo ({', '.join(sorted(found))}): "
                               f"aggiungi la coppia a {CONFLICTS.name}")
        else:
            self.errors.append(f"{source} {name!r} non e' nel vocabolario: aggiungilo come "
                               f"alias in {SUBSTANCES.name}")
        return None

    def note_aliases(self, substance_id: str, names: list[str]) -> None:
        """Gli alias che una fonte da' a una sostanza e il vocabolario non ha."""
        substance = self.by_id[substance_id]
        known = {name.lower() for name in
                 [substance["name"], *substance.get("aliases", []), *substance.get("rejected", [])]}
        for name in names:
            if name and name.lower() not in known:
                self.new_aliases.setdefault(substance_id, set()).add(name)

    def finish(self) -> None:
        """Avvisa degli alias nuovi; si ferma se ci sono nomi da risolvere."""
        for substance_id, names in sorted(self.new_aliases.items()):
            print(f"avviso: alias nuovi per {substance_id}: {', '.join(sorted(names))}")
        if self.errors:
            raise SystemExit("nomi da risolvere:\n  " + "\n  ".join(dict.fromkeys(self.errors)))
