# Reagent colour chart

Una pagina che riorganizza in modo consultabile le tabelle di colori dei
reagenti per il drug checking, con ricerca per reagente e per colore, e con
l'evoluzione del colore nel tempo.

## Da dove vengono i dati

L'unica fonte è **PsychonautWiki**. La sua pagina "Copyrights" rilascia i
**dati semantici** del wiki in **CC BY 4.0** e il testo delle pagine in
CC BY-SA 4.0; la licenza dichiarata dal dataset è quella della fonte in
`sources`. Il dataset è in `psychonautwiki_schema.json`, generato a parte; la
pagina lo usa così com'è.

Ogni cella espone **tutte** le letture: quando una fonte dà più esiti per la
stessa coppia, la pagina li mostra tutti.

Le descrizioni dei reagenti nella sezione "Reagenti" sono un passaggio in
inglese, riportato com'è e tradotto a mano in italiano, tutti e due in
`data/descriptions.js`. Vengono dalle voci di Wikipedia (CC BY-SA 4.0) e,
per il 4-AP, che su Wikipedia non c'è, da un articolo open access (Houtzager
et al. 2024, CC BY 4.0). Il file è in CC BY-SA 4.0, scritto nel commento in
cima e in `license`; `sources` ha le fonti principali con la loro licenza e
`locales` i testi per lingua. Ogni descrizione ha il link al punto da cui
viene, la sua fonte principale e dice se è tradotta.

Le fonti usate in precedenza (Wikipedia, Grassroots Harm Reduction, EDM
Identity, reagent-tests.uk, ProTestKit, Tang et al. 2010) sono servite a
progettare il modello, ma i loro termini non ne permettono l'uso: estrattori e
dati estratti sono in `legacy/`, fuori dalla pagina.

## Portare i dati nella pagina

```bash
python3 tools/fetch_descriptions.py   # Wikipedia, Europe PMC -> data/descriptions.js
python3 tools/build_data.py           # psychonautwiki_schema.json -> data/reagents.json e .js
```

`fetch_descriptions.py` riscrive le fonti e l'inglese e non tocca le
traduzioni: dice quali reagenti sono da tradurre e quali vanno rivisti perché l'originale inglese è cambiato
dall'ultima volta.

## La pagina in un file solo

```bash
python3 tools/bundle.py     # -> dist/colori-dei-test-con-reagenti.html
```

La pagina non ha dipendenze esterne (niente moduli, niente `fetch`): il
bundler scioglie il foglio di stile e i quattro script dentro l'HTML e li
minimizza. Il risultato è **un file da circa 250 kB** che si apre con un doppio
clic, funziona offline e si può mandare per email. Il pulsante «Scarica»
nell'intestazione lo scarica.

```bash
.venv/bin/pip install rjsmin   # facoltativo: minifica anche il javascript
python3 tools/bundle.py                  # -> dist/colori-dei-test-con-reagenti.html
python3 tools/bundle.py --no-minify      # css e js leggibili (900 kB)
```

Senza `rjsmin` il javascript resta com'era e il file pesa circa 50 kB in
piu'.

## Il formato dei dati

`data/reagents.json` è lo schema di PsychonautWiki:

```
sources     { [fonte]: { label, year, url, license, fetchedAt } }
palette     { [tinta]: { shades: { light, standard, dark } } }   hex di ogni colore
reagents[]  { id, name, duration?, stir, baseColor? }
substances[]
  id, name, aliases?
  info        { wiki, type, class? }
  reactions
    [reagente][]           una lettura per esito
      source
      colors[] | null      la sequenza nel tempo, ogni colore "tinta.intensità";
                           [] nessuna reazione, null risultato incoerente
      proportion?          low | standard | high (assente: standard)
      observation?         1, 2… quando la fonte ha più osservazioni della coppia
      shape?               spots | ring | precipitate | particles
      fizz?                la reazione fa bolle
      fade?                il colore che svanisce
```

Un reagente senza letture non compare. `duration` è il tempo del test in
secondi (0 = istantaneo), `stir` dice se va mescolato, `baseColor` è il colore
del reagente stesso. Tutto il resto — lo stato della cella, il disaccordo fra
le letture, la copertura di un reagente — la pagina lo calcola al caricamento.

## Documenti

- `DESIGN.md` — modello dati, metodo di estrazione, conflitti tra fonti
- `FLOW.md` — flusso d'esperienza della pagina (v1 semplificata)
- `DECISIONS.md` — registro delle decisioni prese e di quelle ancora aperte

## La pagina

```
index.html                 la pagina
assets/styles.css          design system, temi, stampa
assets/colors.js           colori dalla palette dei dati, strisce, didascalie
assets/i18n.js             stringhe IT/EN
assets/app.js              stato, filtri, rendering
tools/serve.py             server di sviluppo (senza cache)
```

Si apre con un doppio clic su `index.html` (gli script sono classici, non
moduli ES, così funziona anche da `file://`). Per lo sviluppo:

```bash
python3 tools/serve.py 8000     # http://localhost:8000
```

La pagina contiene: il banner sull'avvertenza, la sezione **osservazioni**
che riordina la tabella e suggerisce il prossimo test, la **matrice** (riga =
sostanza, colonna = reagente) e in fondo i reagenti, le fonti e le licenze.

La tabella scorre in orizzontale da sola, con le prime due colonne agganciate a
sinistra. Le intestazioni di colonna stanno in una striscia separata agganciata
in alto alla pagina, che scorre in orizzontale in sincrono con la tabella.

## Struttura

```
data/reagents.json          il dataset (copiato da psychonautwiki_schema.json)
data/reagents.js            lo stesso dataset, come script (per file://)
tools/build_data.py         porta il dataset nella pagina
tools/bundle.py             la pagina in un file solo
tools/serve.py              server di sviluppo
assets/                     la pagina
legacy/                     estrattori e dati delle fonti non più usate
```

## Avvertenza

I test con reagenti sono **solo preliminari**. Un colore non è
un'identificazione, e un risultato negativo **non esclude** la presenza di una
sostanza. Per più reagenti servono più test. I dati coprono una parte
limitata delle sostanze: la copertura di ogni reagente è indicata nella
pagina, e le sostanze senza dati sono elencate esplicitamente.
