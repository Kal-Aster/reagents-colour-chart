#!/usr/bin/env python3
"""Porta il dataset nella pagina.

Il dataset e' quello estratto da PsychonautWiki (psychonautwiki_schema.json),
nello schema della fonte: la pagina lo legge cosi' com'e'. Lo script lo copia
in data/reagents.json e, siccome la pagina si apre anche dal disco, dove
fetch() non puo' leggere un file locale, anche in data/reagents.js come
script semplice.

    python3 tools/build_data.py
    python3 tools/build_data.py percorso/dello/schema.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "psychonautwiki_schema.json"
OUT = ROOT / "data" / "reagents.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema", nargs="?", type=Path, default=SOURCE)
    args = parser.parse_args()

    data = json.loads(args.schema.read_text(encoding="utf-8"))
    payload = json.dumps(data, indent=1, ensure_ascii=False)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(payload + "\n", encoding="utf-8")
    (OUT.parent / "reagents.js").write_text(
        "window.REAGENTS = " + payload + ";\n", encoding="utf-8")

    readings = sum(len(readings) for substance in data["substances"]
                   for readings in substance["reactions"].values())
    print(f"sostanze {len(data['substances'])} | reagenti {len(data['reagents'])} | "
          f"letture {readings} | fonti {', '.join(data['sources'])}")
    print(f"scritto {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
