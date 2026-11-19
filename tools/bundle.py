#!/usr/bin/env python3
"""Raccoglie la pagina in un unico file HTML.

La pagina è già senza dipendenze esterne (niente moduli, niente fetch): per
metterla in un file solo basta sciogliere il foglio di stile e i quattro
script dentro l'HTML. Il risultato si apre con un doppio clic, si può
mandare per email e funziona offline.

    python3 tools/bundle.py            -> dist/tabella-dei-colori-dei-reagenti.html
    python3 tools/bundle.py -o page.html
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "index.html"

# Il collegamento al file unico vale per la pagina in reparto, non per il
# file unico stesso (che non contiene la cartella dist/).
BUNDLE_LINK = re.compile(
    r'\s*<a id="bundle-link"[^>]*>.*?</a>', re.S)

LINK_TAG = re.compile(r'<link rel="stylesheet" href="([^"]+)"\s*>')
SCRIPT_TAG = re.compile(r'<script src="([^"]+)"\s*></script>')


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def inline_style(html: str, minify: bool = True) -> str:
    def repl(m: re.Match) -> str:
        css = read(ROOT / m.group(1).split("?")[0])
        if minify:
            css = minify_css(css)
        return "<style>\n" + css + "\n</style>"

    return LINK_TAG.sub(repl, html)


def minify_css(css: str) -> str:
    """Minifica il foglio di stile: toglie i commenti e gli spazi
    superflui, restando attento alle stringhe (i `content: "..."`)."""
    out = []
    i = 0
    n = len(css)
    quote = None
    while i < n:
        ch = css[i]
        if quote:
            out.append(ch)
            if ch == "\\":
                if i + 1 < n:
                    out.append(css[i + 1])
                    i += 2
                    continue
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and css[i + 1] == "*":
            end = css.find("*/", i + 2)
            i = n if end < 0 else end + 2
            continue
        out.append(ch)
        i += 1
    text = "".join(out)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*([{};:,>])\s*", r"\1", text)
    text = re.sub(r"\s*;\}", "}", text)
    return text.strip()


def minify_js(js: str) -> str:
    """Minifica il javascript con rjsmin, se c'e'. Senza, il codice
    resta com'era: la pagina funziona lo stesso."""
    try:
        import rjsmin  # noqa: PLC0415
    except ImportError:
        return js
    try:
        return rjsmin.jsmin(js)
    except Exception:
        return js


DATA_FILES = ("data/reagents.js", "data/descriptions.js")


def minify_data(js: str) -> str:
    """Il dataset occupa nove decimi del file: compatto diventa molto
    piu' piccolo e la pagina non cambia."""
    assignment = re.search(r"(window\.\w+)\s*=\s*(?=\{)", js)
    end = js.rfind("}")
    if not assignment or end < assignment.end():
        return js
    # il commento in cima (la licenza) resta com'e'
    head = js[:assignment.start()]
    data = json.loads(js[assignment.end():end + 1])
    return head + assignment.group(1) + "=" + json.dumps(
        data, separators=(",", ":"), ensure_ascii=False) + ";"


def inline_scripts(html: str, minify: bool = True) -> str:
    def repl(m: re.Match) -> str:
        name = m.group(1).split("?")[0]
        js = read(ROOT / name)
        if name in DATA_FILES:
            js = minify_data(js)
        elif minify:
            js = minify_js(js)
        # uno script inline non puo' contenere la sequenza che chiude il tag
        js = js.replace("</script", "<\\/script")
        return "<script>\n" + js + "\n</script>"

    return SCRIPT_TAG.sub(repl, html)


def build(out: Path, minify: bool = True) -> int:
    html = read(SOURCE)
    html = inline_style(html, minify)
    html = inline_scripts(html, minify)
    html = BUNDLE_LINK.sub("", html)
    # il parametro di versione non serve piu': non ci sono file esterni
    html = re.sub(r"\?v=\d+", "", html)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return len(html)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--output", default=None,
                    help="where to write the single file")
    ap.add_argument("--no-minify", action="store_true",
                    help="keep the css and the js readable")
    args = ap.parse_args()

    out = Path(args.output) if args.output else ROOT / "dist" / "tabella-dei-colori-dei-reagenti.html"
    if not out.is_absolute():
        out = ROOT / out

    size = build(out, minify=not args.no_minify)
    print(f"scritto {out} ({size/1024:.0f} kB)")
    print(f"la pagina in reparto era {(SOURCE.stat().st_size)/1024:.0f} kB, "
          f"il file solo {size/1024:.0f} kB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
