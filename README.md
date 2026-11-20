# Reagent colour chart

Una pagina che riorganizza in modo consultabile le tabelle di colori dei
reagenti per il drug checking, con ricerca per reagente e per colore, e con
l'evoluzione del colore nel tempo.

## Da dove vengono i dati

Le fonti sono quattro, ognuna con uno script che la legge e ne riconduce i
nomi dei colori alla palette della pagina:

| Fonte | Licenza | Script | Cosa porta |
|---|---|---|---|
| [PsychonautWiki](https://psychonautwiki.org) | dati semantici CC BY 4.0 | `tools/extract_psychonautwiki.py` | 210 sostanze, 15 reagenti |
| [NIJ Standard-0604.01](https://www.ojp.gov/pdffiles1/nij/183258.pdf) (2000) | pubblicazione del governo USA, se ne usano solo i fatti | `tools/extract_nij.py` | 49 sostanze, molte non controllate: paracetamolo, aspirina, zucchero, sale, bicarbonato, procaina, chinino, glucosio, mannitolo… |
| [NIST/NIJ CADS](https://doi.org/10.18434/mds2-3627) | dati di dipendenti NIST: pubblico dominio negli USA, licenza NIST altrove | `tools/extract_cads.py` | i 17 campioni sequestrati con un composto solo |
| [Chang et al. 2025](https://doi.org/10.1002/ansa.70008) | CC BY 4.0 | `tools/extract_chang.py` | 14 polveri, tra cui saccarosio, paracetamolo, caffeina e xilazina |

Le sostanze stanno in un vocabolario, `data/substances.json`: per ognuna id,
nome, tipo, voce di PsychonautWiki, classe e alias, cioè tutti i nomi raccolti
dalle fonti e i nomi di strada. Le fonti danno solo reazioni: ogni estrattore
cerca il nome della sua fonte fra nomi e alias del vocabolario
(`tools/vocabulary.py`). Gli alias possono essere ambigui ("speed" è
l'anfetamina e la metanfetamina), ma un nome ambiguo o sconosciuto ferma
l'estrazione: una coppia fonte-nome ambigua si risolve a mano in
`data/name-conflicts.json`, un nome nuovo si aggiunge come alias. Gli alias che
una fonte porta e il vocabolario non ha sono un avviso; `rejected` tiene i nomi
che una fonte dà a una sostanza e che non sono suoi ("tea" per la caffeina).

Per PsychonautWiki si cerca il nome del database dei reagenti, non la sostanza
a cui l'API l'ha agganciato: l'aggancio aveva messo la cocaina cloridrato
sotto "Coca", la doxepina sotto "DOx", il PCEEA sotto "PCE", e la stessa
riga della cannabis sotto Cannabis e sotto THC. Nella pagina è "Cannabis
(THC)": il test si fa sulla pianta o sulla resina, e il colore viene dai
cannabinoidi che contiene.

Le letture di una sostanza che più fonti documentano stanno nella stessa
cella, una accanto all'altra: la pagina non sceglie fra le fonti. Ogni cella
espone **tutte** le letture: quando una fonte dà più esiti per la stessa
coppia, la pagina li mostra tutti.

I nomi dei colori diventano colori della palette con le regole di
`tools/colour_names.py`, le stesse del testo di PsychonautWiki: un composto
vale per tutte le sue famiglie ("Pink-orange" è rosa oppure arancione), "-ish"
aggiunge la sua famiglia, "light" e "dark" scelgono la tinta. I testi
originali non entrano nel dataset: l'elenco delle fonti della pagina dice con
quale script e in che data ogni fonte è stata letta.

Alcune scelte su cosa entra:

- **CADS**: solo i campioni con un composto solo. In una miscela il colore non
  si attribuisce a un componente, e nemmeno la sua assenza: CADS 030 contiene
  saccarosio e col Marquis non reagisce, il saccarosio puro sì.
- **Cobalto tiocianato**: resta fuori. NIJ e CADS lo usano da solo, mentre
  la pagina ha lo **Scott** (che poi acidifica ed estrae: resta blu quasi solo
  la cocaina) e il **Morris** (che basifica, per la ketamina). Il cobalto da
  solo dà blu con quasi tutte le ammine: nella colonna dello Scott o del
  Morris sembrerebbe un disaccordo fra le fonti.
- **NIJ**: entrano Mandelin, Marquis, Froehde, Mecke, Simon's e il p-DMAB come
  **Ehrlich**, che è lo stesso reattivo; Dille-Koppanyi, Duquenois-Levine,
  acido nitrico, cloruro ferrico e Zwikker restano fuori. Della tabella 3
  entrano anche i "nessuna reazione".
- **Chang et al.**: le tabelle 3-5, i colori visti dagli autori; la tabella 2
  riassume la letteratura e resta fuori.

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
dati estratti non sono nel repository.

## Portare i dati nella pagina

```bash
python3 tools/extract_psychonautwiki.py --no-csv --schema   # -> sources/PNW.json
python3 tools/extract_nij.py          # NIJ 0604.01  -> sources/NIJ.json
python3 tools/extract_cads.py         # NIST CADS    -> sources/CADS.json
python3 tools/extract_chang.py        # Chang 2025   -> sources/Chang2025.json
python3 tools/fetch_descriptions.py   # Wikipedia, Europe PMC -> data/descriptions.js
python3 tools/build_data.py           # tutte le fonti -> data/reagents.json e .js
```

Gli estrattori scaricano le fonti in `sources/cache/` (con `--offline` usano
solo quello che c'è già) e controllano lo sha256 dei file del NIST e del NIJ:
se la fonte cambia, si fermano. Si fermano anche davanti a un colore, un nome
di sostanza o un campione puro che non conoscono: vanno decisi a mano. CADS e NIJ
leggono i PDF con `pdftotext` (poppler-utils). `sources/` resta fuori dal
repository; `data/reagents.json` ci sta.

`fetch_descriptions.py` riscrive le fonti e l'inglese e non tocca le
traduzioni: dice quali reagenti sono da tradurre e quali vanno rivisti perché l'originale inglese è cambiato
dall'ultima volta.

## La pagina in un file solo

```bash
python3 tools/bundle.py     # -> dist/tabella-dei-colori-dei-reagenti.html
```

La pagina non ha dipendenze esterne (niente moduli, niente `fetch`): il
bundler scioglie il foglio di stile e i quattro script dentro l'HTML e li
minimizza. Il risultato è **un file da circa 250 kB** che si apre con un doppio
clic, funziona offline e si può mandare per email. Lo scarica il link
«Scarica» accanto alla licenza del codice, in fondo alla pagina; accanto alle
licenze dei dati e delle descrizioni ci sono i loro file.

```bash
.venv/bin/pip install rjsmin   # facoltativo: minifica anche il javascript
python3 tools/bundle.py                  # -> dist/tabella-dei-colori-dei-reagenti.html
python3 tools/bundle.py --no-minify      # css e js leggibili (900 kB)
```

Senza `rjsmin` il javascript resta com'era e il file pesa circa 50 kB in
piu'.

## Il formato dei dati

`data/reagents.json` è lo schema di PsychonautWiki, con le letture di tutte le
fonti:

```
sources     { [fonte]: { label, year, url, license, script, fetchedAt } }
palette     { [tinta]: { shades: { light, standard, dark } } }   hex di ogni colore
reagents[]  { id, name, duration?, stir, baseColor?, target? }
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
                           (una lettura ripetuta in più osservazioni compare una volta)
      shape?               spots | ring | precipitate | particles
      fizz?                la reazione fa bolle
      dissolves?           false: il campione non si scioglie
      fade?                il colore che svanisce
```

Un reagente senza letture non compare. `duration` è il tempo del test in
secondi (0 = istantaneo), `stir` dice se va mescolato, `baseColor` è il colore
del reagente stesso. `target` sono le famiglie del colore atteso dai reagenti
che cercano una classe (il blu del Simon's per le ammine secondarie): una
lettura lo contiene o no. I reagenti senza `target` danno un'impronta.

I grigi sono una famiglia sola, `gray`, che va dal grigio (`gray.light`) al
grigio scuro (`gray.standard`) al nero (`gray.dark`).

Una coppia che una fonte non documenta non ha letture di quella fonte: è
"nessun dato". PsychonautWiki marca ogni esito con `isPositive`, che dice se
è un indizio della sostanza, non se il colore cambia; un esito negativo che
nomina un colore ("Dark brown" col Simon's) dà quel colore, perché è quello
che si vede, e "no instant reaction" non dà letture. Tutto il resto — lo stato della cella, il disaccordo fra
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
data/reagents.json          il dataset (il vocabolario e le reazioni delle fonti)
data/substances.json        il vocabolario delle sostanze
data/name-conflicts.json    le coppie fonte-nome risolte a mano
data/reagents.js            lo stesso dataset, come script (per file://)
data/descriptions.js        le descrizioni dei reagenti, con fonti e licenza
tools/extract_*.py          estraggono le fonti in sources/, PsychonautWiki compresa
tools/colour_names.py       dai nomi dei colori delle fonti alla palette
tools/source_schema.py      quello che gli estrattori hanno in comune
tools/vocabulary.py         a quale sostanza va un nome di una fonte
tools/build_data.py         unisce le fonti e porta il dataset nella pagina
tools/fetch_descriptions.py recupera le descrizioni dei reagenti
tools/bundle.py             la pagina in un file solo
tools/serve.py              server di sviluppo
assets/                     la pagina
```

## Licenze

| Parte | Licenza |
|---|---|
| Codice (`index.html`, `assets/`, `tools/`) | [AGPL-3.0](LICENSE) |
| Dati della tabella (`data/reagents.*`, `data/substances.json`, `data/name-conflicts.json`) | [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) |
| Descrizioni dei reagenti (`data/descriptions.js`) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |
| Testi e documenti | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) |

I dati della tabella sono un adattamento delle fonti elencate sopra, che
restano con la loro licenza: la licenza non commerciale vale per lo schema, la
pulizia, l'organizzazione e la conversione dei colori di questo progetto, non
per i dati delle fonti. Le descrizioni restano in
CC BY-SA perché vengono in gran parte da Wikipedia. Consultare la pagina, a
qualunque scopo, non è regolato da nessuna di queste licenze.

## Avvertenza

I test con reagenti sono **solo preliminari**. Un colore non è
un'identificazione, e un risultato negativo **non esclude** la presenza di una
sostanza. Per più reagenti servono più test. I dati coprono una parte
limitata delle sostanze: la copertura di ogni reagente è indicata nella
pagina, e le sostanze senza dati sono elencate esplicitamente.
