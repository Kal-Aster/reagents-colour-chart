# Design — Reagent colour chart

Esplorazione di come organizzare la pagina prima di implementarla.

Fonte dati: [List of reagent testing color charts](https://en.wikipedia.org/wiki/List_of_reagent_testing_color_charts)
(CC BY-SA 4.0, oldid `1302153309`). Estrazione in `tools/build_data.py` → `data/reagents.json`.

---

## 1. Cosa abbiamo davvero nei dati

| | |
|---|---|
| Sostanze | **82** (44 Substance, 25 Adulterant, 7 Forms, 6 Class) |
| Reagenti | **8** — Folin's, Froehde, Liebermann, Mandelin, Marquis, Mecke, Morris, Simon's |
| Celle | **656** (82 × 8) |
| "?" (sconosciuto) | **510 — 78%** |
| "No reaction" | 43 — 7% |
| Colore documentato | **103 — 16%** |
| Righe "Custom reagents" | 14 (classe → reagente indicato) |
| Stringhe di colore distinte | 79 |
| Riferimenti bibliografici | 11 fonti (peer-reviewed, NIJ, vendor, community, forum) |

**Il dato più importante della pagina è la copertura, non i colori.** Nessuna delle 82
sostanze ha dati per tutti gli 8 reagenti. Per reagente:

| Reagente | Documentate | | Reagente | Documentate |
|---|---|---|---|---|
| Mandelin | 33/82 | | Simon's | 19/82 |
| Marquis | 32/82 | | Liebermann | 4/82 |
| Mecke | 29/82 | | Folin's | 2/82 |
| Froehde | 26/82 | | Morris | 1/82 |

Da qui discende una regola di progetto non negoziabile: **`?` deve essere
visibilmente diverso da "no reaction"**, e ogni vista deve mostrare quanto è
completa. Un utente che vede una cella vuota deve capire "nessun dato", non
"nessuna reazione".

### Data quality (trovato durante l'estrazione)

- Il wikitext di Wikipedia ha **virgolette non chiuse** negli attributi `style`
  (es. `style="background:#f27b21; |`) e celle scritte come `| | testo`.
  Il parser li gestisce.
- La cella **PMA / Froehde** contiene letteralmente `n` (typo di Wikipedia).
  Il gradiente della cella (`#8a9b4b → #833c0c`) dice verde → marrone:
  override manuale in `COLOR_OVERRIDES`, con nota in pagina.
- 87/103 celle colorate hanno un hex di sfondo di Wikipedia; le altre 16 no.
  Wikipedia sceglie i colori in modo incoerente (`Moderate olive` e `Dark olive`
  sono entrambi `#808000`), quindi **useremo una palette curata** e terremo
  l'hex di Wikipedia solo come metadato.
- Le intestazioni hanno apici spuri `A`/`B` (Folin's, Morris, Simon's): artefatti
  di template, rimossi.

---

## 2. Il modello del colore

Questo è il cuore del "filtra per colore". Le 79 stringhe non sono colori: sono
**frasi descrittive** con intensità, sfumature e sequenze temporali.

Esempi reali: `Deep purplish red`, `Violet and orange streaks`,
`White > light yellow > black`, `Green > to Blue or Yellow`,
`Strong reddish orange/Dark reddish brown`, `Grey with smoke`.

Proponiamo di normalizzarle in una struttura a 3 livelli:

```
stages[]  →  una "tappa" della reazione (progressione nel tempo)
  groups[]  →  sfumature parallele nella stessa tappa ("orange/brown", "violet AND orange")
    primary[]     → tinte principali      ["purple"]
    qualifiers[]  → tinte secondarie      ["red"]    (da "purplish", "greyish", "w/ hints of")
    modifier      → intensità             "deep" | "dark" | "light" | "very" | "moderate" | "brilliant" | "strong"
    note          → timing/altro          ["slow"]
```

Regole del parser (in `tools/build_data.py::parse_color`, già implementate e
verificate sulle 79 stringhe):

- `>` / `->` / `to` separano le **tappe** (progressione).
- `/`, `and`, `or` separano le **sfumature** parallette.
- Gli aggettivi in `-ish` (`bluish`, `purplish`, `reddish`, `greenish`…) sono
  **qualificatori**, non tinta principale: `Deep purplish red` = rosso profondo
  con tendenza al viola.
- `blackish red` → primary `red`, qualifier `black` (rosso quasi nero).
- `no reaction` e `?` sono stati, non colori.

Risultato: **12 famiglie di tinta** (yellow, orange, brown, red, pink, purple,
blue, green, olive, black, grey, white) e 9 qualificatori.

**Palette curata**: per ogni (tinta × intensità) un hex scelto bene e coerente,
con testo bianco o nero calcolato per il contrasto (WCAG AA). Il colore da solo
non porta mai l'informazione: accanto c'è sempre la descrizione testuale.

### 2.1 Le traiettorie: il colore che cambia nel tempo

Alcune sostanze non danno un colore ma una **sequenza**. Il modello le rappresenta
con `trajectory`:

```json
"trajectory": {
  "pattern":    [["yellow"], ["green"]],   // tinta a ogni tappa
  "modifiers":  [null, null],
  "len":        2,
  "kind":       "shift",
  "reverts":    false,
  "simple":     false
}
```

Quattro tipi di evoluzione:

| `kind` | Significato | Esempio dai dati |
|---|---|---|
| `static` | un solo colore, nessuna evoluzione documentata | 82 celle |
| `shift` | la tinta cambia | 2C-B Marquis: giallo → verde |
| `intensify` | stessa tinta, più scuro/chiaro | Levamisole Liebermann: marrone → marrone molto scuro |
| `revert` | il colore esce e **torna indietro** | non presente in Wikipedia, ma esiste in pratica |

Il caso `revert` è il più diagnostico in assoluto: *«diventa subito giallo, poi
rosso, poi di nuovo giallo; se non diventa di nuovo giallo è un'altra
sostanza»*. Il ritorno è l'informazione, non il colore d'arrivo.

**Conseguenza per il matching**: un'osservazione non è un colore ma una
sequenza, e il confronto ha tre esiti — **piena** (la sequenza documentata
contiene quella osservata), **parziale** (la sequenza documentata prevede un
ritorno che non è stato osservato), **conflitto** (le tinte non coincidono).
Il caso "parziale" non esiste senza il modello delle traiettorie.

In Wikipedia le evoluzioni sono 41 celle su 102 (39%): abbastanza per rendere
la feature utile, ma il modello deve restare capace di representingne di più.

### 2.2 Le fonti in disaccordo

Una cella può contenere più osservazioni (modello `observations[]`), ciascuna con
la sua fonte. Esempio reale: *Mescaline / Froehde* è scritto come
`"Green > to Blue or Yellow"` — ma sono **due fonti diverse** (Virginia vs
Bunk Police) che riportano colori diversi, non una sfumatura. La cella va
marcata "fonti in disaccordo" e il match diventa *possibile*, non *certa*.

Le fonti si ordinano per qualità dichiarata e visibile:
peer-reviewed (O'Neal 2013) > NIJ/governativo (2000) > vendor > community > forum/video.

---

## 2.b Le fonti, e come si estraggono

Tre fonti, ciascuna con un metodo di estrazione diverso. Il punto chiave: **i
gradienti si leggono dai pixel**, quindi le traiettorie sono *misurate*, non
trascritte a occhio.

### Fonte 1 — Wikipedia (CC BY-SA 4.0)

`tools/build_data.py` parsa il wikitext ed estrae 82 sostanze × 8 reagenti.
I colori sono descritti **a parole** ("Dark purple to black"), e vengono
scomposti dal modello del §2 in tappe / sfumature / qualificatori.

### Fonte 2 — Grassroots Harm Reduction, "Standard Drug Checking Reagents" (Spring 2026)

`tools/extract_grassroots.py` legge il JPG **a piena risoluzione**
(2992×2372, 300 DPI — il `-1024x812` è solo la miniatura) ed è l'unica versione
esistente: sul server non c'è né SVG né PDF.

Il chart codifica l'evoluzione come **gradiente orizzontale**: bordo sinistro =
colore all'inizio della reazione, bordo destro = colore alla fine. Lo script:

1. individua le 18 righe e le 7 colonne dalla geometria della griglia;
2. distingue le **barre** (riempiono l'altezza della cella) dai box
   **"NO REACTION"** (testo nero su fondo grigio);
3. campiona ogni barra in 11 punti, prendendo la mediana verticale per evitare
   il bordo nero;
4. classifica ogni campione in famiglia di tinta + intensità;
5. raggruppa i campioni in **fasi**, piegando le tinte intermedie di un gradiente
   (giallo → verde passa per l'oliva: non è una fase, è un passaggio).

Risultato: **89 barre + 37 "NO REACTION"**, cioè 126 celle tutte decodificate.
La verifica è immediata: MDMA/Marquis misura viola → nero, 2C-B/Marquis
giallo → verde, Heroin/Marquis malva → rosso — tutti e tre coerenti con la
descrizione di Wikipedia.

Il chart fornisce anche i **tempi** ("0:00 → 0:30 seconds", "INSTANT") e le
**note di protocollo** ("primo passo", "secondo reagente per MDMA"), che sono il
materiale del test successivo consigliato.

#### Il contorno del testo sopra le barre

Quasi tutti i chart stampano il nome della sostanza **sopra** il gradiente, in
bianco con un contorno nero spesso. Campionando tutta l'altezza della barra, il
contorno finiva nel campione e produceva fasi "nero" inesistenti: 5-MeO-DMT
Mandelin risultava *giallo → rosso → nero → rosso* quando la barra è
semplicemente *giallo → rosso*. Ora si legge **solo la fascia superiore** della
barra, che il lettering non tocca.

#### Tre problemi risolti nell'estrazione

1. **Il bordo della barra.** Il campione finale prendeva il bordo nero
   anti-aliasato e produceva una "fase" grigia inesistente. Due detectori di
   background con tolleranze diverse erano il colpevole: uno riconosceva il
   lavanda (200,189,223) e l'altro no.
2. **Le famiglie di tinta hanno confini arbitrari.** Un gradiente verde chiaro →
   verde scuro *passa* per l'oliva, e per nome di famiglia si inventava una fase
   "verde → oliva → verde" che non esiste. Ora i campioni sono raggruppati per
   **angolo di tinta** (tolleranza 20°), non per nome: il risultato è
   "verde → verde (più scuro)".
3. **Il nero non è una tinta.** Un tratto quasi nero è un estremo di luminosità,
   non una fase: viene piegato nel vicino cromatico, così "blu molto scuro" non
   si spezza in blu → nero → blu.

### Le regole delle fasi

Un campione non è una fase. Le regole, in ordine:

1. campioni consecutivi della stessa famiglia formano un gruppo;
2. un gruppo **di un solo campione** cromatico, incastonato fra due altri toni, è
   una **transizione**, non una fase: un gradiente che passa per il magenta
   fra l'arancio e il viola non deve riportare una fase "rosa"
   (è il caso di 5-APB, che ora legge *giallo → viola → nero*);
3. un campione **achromatico** (nero, grigio, bianco) fra due gruppi
   achromatici è parte dello stesso tratto scuro, non una fase a sé;
4. un tratto **nero fra due gruppi cromatici** è uno scurimento lungo il cammino,
   non una fase: 5-MeO-DMT legge *giallo → rosso*, non *giallo → nero → rosso*;
5. quello che resta sono le fasi.

In una fase ci vuole un colore **che esiste da solo**. È anche il principio che
rende affidabile il rilevamento del **ritorno**: il ritorno è quando la tinta
finale torna a una tinta incontrata prima, e una fase spuria falserebbe
quel segnale.

### Cosa resta un'approssimazione

Il nome della tinta resta una **didascalia**, non il dato. Per questo la cella
deve mostrare **il gradiente misurato** (decisione D28): il gradiente è la
verità, il nome è un aiuto. Con 89 celle un nome occasionalmente impreciso non
può più trarre in inganno, perché l'occhio vede il colore vero.

### Fonte 3 — EDM Identity, "Reagent Color Chart" v14 (aprile 2022)

`tools/extract_edm.py` decodifica il chart 2000×1258. La griglia non è regolare
(le righe hanno altezze diverse, alcuni settori sono celle di stato), quindi
sia le colonne sia le righe vengono **rilevate**:

- le colonne si trovano dalla posizione dei **nomi dei reagenti**, letti con OCR:
  i riquadri colorati sono adiacenti e indistinguibili per colore, ma le parole
  sono ben separate, e i confini sono i punti medi tra nomi consecutivi;
- le righe si trovano dalle **linee separatrici** (righe quasi vuote), raggruppate
  e ridotte alla loro linea media;
- ogni cella viene classificata misurando la **run contigua** verticale per
  colonna: una barra riempie la cella, una cella di stato no.

Il chart ha una legenda esplicita: *"ogni barra mostra il cambio di colore
su 20 secondi da sinistra a destra"*. E introduce **tre stati distinti**:
`NO REACTION`, `UNKNOWN` (non testato) e `INCONSISTENT` (risultato incoerente) —
una distinzione che Wikipedia non fa e che è utile.

Il campionamento del gradiente dà 126 traiettorie su 25 sostanze × 9 reagenti.

### Fonte 4 — reagent-tests.uk, "Reagent Test result chart" (2021)

`tools/extract_reagenttests.py` lavora sull'originale da **8272×6028**, il più
grande in assoluto. Questo chart è diverso dagli altri: ogni cella contiene una
**parola** che descrive il colore ("Yellow > Green", "Red > Brown", "Purple >
Black", "No colour change", "None (paper darkens)") su uno sfondo colorato.

Le parole sono la metà più ricca del dato — nominano la **sequenza**, non solo
il colore finale — ma l'OCR del font è ostile: spezza le parole ("Ye ellow",
"Da ark", "Ver ys"), duplica lettere ("yeellow") e legge la freccia come "V".
La riparazione avviene con una **programmazione dinamica** sul vocabolario dei
colori: si cerca la segmentazione che minimizza il costo, accettando una
sostituzione o un carattere spurio dentro una parola.

Lo sfondo colorato viene misurato come **colore modale** della cella: serve
come riserva quando l'OCR non è recuperabile, e come controllo incrociato.

Il chart copre 26 composti × 5 reagenti.

### Fonte 5 — ProTestKit, "Mandelin Pro Test Reactions" (2020)

`tools/extract_protestkit.py` decodifica il chart 1197×8913: ~430 sostanze in
3 colonne, ognuna con il proprio gradiente Mandelin. Le etichette sono lette
con OCR (rapidocr/onnxruntime); i gradienti sono campionati come sopra.

È la fonte che contiene gli esempi di **evoluzione a più fasi** e di **ritorno**
del colore. Su 340 barre: 258 "shift", 59 statiche, **23 con ritorno**.

Esempi reali di ritorno (il caso descritto da chi usa la pagina — *«diventa
giallo, poi rosso, e poi di nuovo giallo; se non diventa di nuovo giallo è
un'altra sostanza»*):

| Sostanza (Mandelin) | Traiettoria misurata |
|---|---|
| a-PVT | giallo → rosso → arancio → **giallo** |
| 3-FPM | giallo → grigio → oliva → **giallo** |
| Methamphetamine 2-FMA | giallo → grigio → **giallo** |
| 2-MMC | giallo → rosso → arancio → rosso → **giallo** |
| 5-MeO-DMT (HCl) | giallo → rosso → nero → rosso |
| Dimethylone | giallo → arancio → bianco → arancio |

### Fonte 6 — Tang et al. (2010), la serie per quantità

`tools/extract_tang.py` legge la figura 3 dell'articolo *Presumptive testing
of amphetamine-type stimulants via colour tests* (ASEAN Journal on Science and
Technology for Development, 27(1): 66-75): il Simon's reagent con
metanfetamina a concentrazioni decrescenti.

| Campione | Colore misurato | Lettura |
|---|---|---|
| solido | `#0F151B` | **nero** |
| 1,3 mg/mL | `#161860` | blu scuro |
| 1,0 mg/mL | `#191F72` | blu |
| 0,8 mg/mL | `#0C1555` | blu scuro |
| 0,6 mg/mL | `#271F4A` | viola scuro |
| 0,4 mg/mL | `#493B85` | viola |
| 0,2 mg/mL | `#7061A0` | viola moderato |
| 0,1 mg/mL | `#87687B` | rosa moderato |

È l'unica fonte in cui l'asse della serie è la **quantità di prodotto** e non
il tempo. Ogni punto porta con sé la sua proporzione
(`high` / `reference` / `low`) e la sua etichetta.

Due avvertenze, entrambe in pagina:

1. le fotografie sono **istantanee**: il tempo di reazione non è specificato,
   quindi una macchia più scura può essere anche un istantanea più tardiva
   della stessa reazione;
2. la riproduzione della figura usata qui è di PRO Test, che a sua volta
   cita l'articolo: prima di pubblicare la pagina va verificata la licenza.

### L'asse della proporzione

La reazione dipende dal **rapporto tra prodotto e reagente**, non dalla dose
assoluta: la stessa quantità di sostanza con il doppio di reagente è una
proporzione più bassa. I tre livelli sono:

- `standard` — la **proporzione consigliata**: quanto dicono i chart (una
  piccola quantità di polvere, come una testa di fiammifero, e una goccia di
  reagente);
- `high` / `low` — quanto dicono le poche fonti che documentano un rapporto
  diverso.

Ogni **osservazione** porta la propria proporzione (`obs.proportion`): un
test può essere caricato diversamente dal successivo. Non c'è un selettore
globale: la tabella segue l'osservazione, colonna per colonna, e le colonne
senza osservazione mostrano la proporzione consigliata.

Le tappe portano la loro proporzione (`stage.proportion = {level, label}`),
così una serie può attraversare più livelli.

Regole:

- ogni lettura in cella è etichettata con la proporzione a cui si riferisce;
  la "proporzione consigliata" c'è sempre, le altre solo quando ci sono;
- se una fonte non documenta la proporzione che hai usato, il confronto cade
  sulla proporzione consigliata e l'esito scende da "pieno" a "parziale": un
  colore documentato per un'altra proporzione non è la stessa cosa;
- quale proporzione è documentata per ciascun reagente è scritto nel
  glossario (è una proprietà delle fonti, uguale per tutte le sostanze).

### Fonti verificate e scartate (per la proporzione)

La ricerca di dati sulla *proporzione* ha battuto diverse piste:

| Fonte | Esito |
|---|---|
| **Erowid** (`/chemicals/meth/`, `/chemicals/amphetamines/testing/`) | La sezione "Drug Testing" riguarda i **test urinari** (immunoassay), non i reagenti colorati: nessuna tabella di colori per sostanza. Non c'è nulla da prendere |
| **Dancesafe** (istruzioni V16) | Le cautele sono **generali**, non per reagente: "a very tiny quantity of a drug may not produce a visible color change", "darker colors may overshadow lighter colors". Vanno nel pannello di sicurezza, non nelle celle |
| **pillreports.net** ("Ecstasy Reagent Test Database") | Il server non risponde (errore 522 da Cloudflare) |
| **reagent-tests.uk** | Le pagine sui reagenti non hanno note di quantità |
| **I chart (Grassroots, EDM, ProTestKit)** | Nessuna dimensione di quantità: sono gradienti nel tempo |
| **Forum bluelight.ru** (citato da Wikipedia) | Ha risultati reali per sostanza e reagente, ma non note di quantità: sarebbe una **sesta fonte di colori**, non di dosi |
| **Articoli scientifici** | È qui che il dato esiste: Tang et al. 2010 (già integrato), Tusiewicz et al. 2021 (serie temporali su MDMA e catinoni), UNODC 2006 (norme di protocollo e saturazione del colore) |

Conclusione: l'asse della proporzione si popola **caso per caso** dagli articoli,
mentre la regola generale (una dose di riferimento) sta una volta sola nel
pannello di sicurezza.

### Il modello unificato: una cella, più osservazioni

Una cella non è un valore: è una **lista di osservazioni**, una per fonte.

```json
"mandelin": {
  "observations": [
    { "source": "wikipedia",   "status": "no-reaction", "text": "No reaction" },
    { "source": "grassroots",  "status": "color", "stages": [...] }
  ],
  "status":   "color",
  "conflict": true,
  "hues":     ["olive", "yellow"],
  "summary":  "oliva → giallo-verde"
}
```

`conflict` è vero quando due fonti non possono essere vere entrambe: status
diversi (colore vs nessuna reazione) oppure famiglie di tinta disgiunte.

### I 28 conflitti trovati

Sono il risultato più utile del lavoro: le due fonti non coincidono, e non
sempre per motivi casuali.

| Sostanza | Reagente | Wikipedia | Grassroots |
|---|---|---|---|
| 2C-B | Mandelin | No reaction | giallo-verde |
| 2C-I | Mandelin | No reaction | arancio → nero |
| Mephedrone | Simon's | No reaction | bianco → blu |
| Mephedrone | Mandelin / Mecke | No reaction | colore |
| Amphetamine | Froehde | Red | No reaction |
| Aspirin | Mandelin | "Grayish olive green" | bianco → grigio → nero |
| Heroin | Froehde/Mandelin/Mecke | colore | colore (tinta diversa) |

Alcuni sono quasi certamente errori di Wikipedia: **la metanfetamina è
un'amina secondaria**, quindi con Simon's deve dare blu, non "no reaction" — e
il chart ha ragione. Altri sono divergenze reali (kit, dosi, tempi diversi).

La regola che ne deriva: **la pagina non sceglie**. Mostra entrambe le
osservazioni, segnala il conflitto, e dice quale fonte è più forte
(peer-reviewed > NIJ > chart di pratiche > community).

### Copertura

| | Wikipedia | + Grassroots | + EDM | + reagent-tests | + ProTestKit |
|---|---|---|---|---|---|
| Sostanze | 82 | 89 | 114 | 116 | **397** |
| Celle | 656 | 720 | 945 | 1075 | **1155** |
| Celle senza dato | 78% | 69% | 43% | 40% | **40%** |
| Celle con conflitto | — | 23 | 39 | 52 | **52** |
| Traiettorie con ritorno | 0 | 1 | 6 | 8 | **23** |
| Traiettorie a 3+ fasi | 21 | 24 | 60 | 90 | **168** |
| Reagenti documentati | 8 | 11 | 11 | 11 | **11** |

Ogni cella espone quante fonti la coprono: 951 celle con una sola fonte, 108 con
due, 48 con tre, 41 con quattro, 5 con cinque, 2 con sei. Le celle coperte da
più fonti sono anche le più affidabili: sono le uniche su cui si può fare
confronto.

### Diritto d'autore

Il chart Grassroots è "© Emanuel Sferios & Grassroots Harm Reduction Network.
All rights reserved. **Distribute freely without changes**", e sul sito è
venduto come prodotto ("Reagent Test Kit Color Chart"). Una trascrizione in
JSON è un Derivative Work: se "senza modifiche" consente la ridistribuzione in
forma strutturata va chiarito con chi ne detiene i diritti. La strada più
sicura: **riprodurre il grafico originale invariato** nella pagina (cosa
esplicitamente consentita) e trattare i dati trascritti come dati citati.

---

## 3. Layout — v1 semplificata

La v1 è **una schermata, una tabella, un filtro**. Il dettaglio del flusso è in
`FLOW.md`; qui la struttura tecnica.

### A. `Elenco per reagente` (default) — colonna singola

> "Ho fatto il test col Marquis, è venuto viola scuro. Cosa può essere?"

Sostanza | Tipo | colore del reagente scelto. Ogni riga con swatch + testo +
fonte + link. Le righe senza dati per il reagente scelto sono **nascoste di
default** (interruttore per mostrarle).

### B. `Matrice completa` — le 8 colonne

82 righe × 8 colonne, intestazioni sticky, prima colonna sticky, scroll
orizzontale su mobile. Ogni cella = swatch + etichetta, mai solo colore.

### C. `Scheda` — una sostanza

Tutti gli 8 reagenti affiancati, le sequenze mostrate come strip di swatch
(giallo → nero), le fonti con il loro tipo, gli alias, i link.

### D. `Colore → sostanze` (reverse lookup)

Non è una vista separata: è la tabella filtrata per colore, con le celle
corrispondenti evidenziate, i conflitti barrati e i vuoti tratteggiati. Con
l'editor di sequenza diventa il confronto di traiettorie.

---

## 4. Funzionalità, per priorità

| # | Funzione | Note |
|---|---|---|
| 1 | Filtro per reagente | select + copertura documentata mostrata accanto |
| 2 | Filtro per colore (tinta / intensità / frase esatta) | il cuore del reverse lookup |
| 3 | Matrice completa + elenco per reagente | viste A e B |
| 4 | Filtro per tipo (Substance/Adulterant/Class/Forms) | le adulteranti vanno evidenziate |
| 5 | Ricerca testo su sostanza/alias | fuzzy, anche per alias ("MDMA" → "MDMA", "ecstasy") |
| 6 | **Combinazione multi-reagente (AND)** | "Marquis viola + Simon's blu → MDMA" — il vero valore per l'uso reale |
| 7 | **URL condivisibile** | filtri nello stato → link da mandare a un amico |
| 8 | Occhiello (`EyeDropper`) | campiona il colore fisico del campione → tinta più vicina |
| 9 | Export CSV / copia | della vista filtrata |
| 10 | Glossario reagenti + "cosa distingue" | es. Marquis: MDMA vs altri fenetilaminici |
| 11 | Sezione "Custom reagents" | 14 righe: classe → reagente che la identifica |
| 12 | Dark mode + print stylesheet | i colori si giudicano su sfondo neutro |

### La combinazione multi-reagente (6) in dettaglio

È la funzione che distingue questa pagina da Wikipedia. Semantica:

- ogni osservazione è `(reagente, tinta[, intensità])`;
- una sostanza è **candidata** (le candidate sono quelle su cui lavora il
  pannello «il prossimo test») se **almeno due terzi** delle osservazioni sono
  compatibili; sono **corrispondenze totali** quelle che le soddisfano tutte
  (D173);
- ogni osservazione può essere marcata come "info" (positivo) oppure "assente"
  ("non ha reagito" = esclude);
- il punteggio ordina per quante osservazioni combaciano, con penalità per
  quelle non documentate (dato mancante ≠ assenza).

Esempio: `Marquis: viola scuro` + `Simon's: nessuna reazione` → MDMA, MDEA, MDA
(candidati principali, con avvertenza che per Simon's i dati mancano per molte
sostanze).

---

## 5. Accessibilità

Il requisito è esplicito, quindi è un criterio di accettazione, non un extra.

- **Il colore non è mai l'unico portatore di informazione**: ogni swatch ha
  accanto la descrizione testuale (WCAG 1.4.1).
- **Tabella semantica vera**: `<table>` con `<caption>`, `<th scope="col">` e
  `<th scope="row">`; le celle di colore hanno `aria-label` con
  sostanza + reagente + colore.
- **Contrasto**: testo bianco o nero calcolato sul colore dello swatch
  (≥ 4.5:1); i bordi dello swatch sono sempre distinguibili dallo sfondo.
- **Tastiera**: tutti i controlli sono elementi nativi (`button`, `select`,
  `input`), focus visibile, skip-link, nessun interazione solo-hover.
- **Screen reader**: regione `aria-live` che annuncia "N risultati"; la
  matrice ha `aria-rowcount`/`aria-colcount` quando filtrata.
- **Non-motion**: `prefers-reduced-motion` rispettato (nessuna animazione
  necessaria).
- **Tema**: chiaro/scuro automatico (`prefers-color-scheme`), i colori restano
  distinguibili in entrambi.
- **Zoom**: layout che regge al 200% senza perdita di contenuto.
- **Offline**: nessuna dipendenza di rete a runtime (il file JSON è locale) —
  importante in contesti con rete scarsa.

---

## 6. Stack

Proponiamo **sito statico senza build step**:

```
index.html            una pagina
assets/app.js         vanilla JS (ES modules), nessun framework
assets/styles.css
data/reagents.json    generato da tools/build_data.py
tools/build_data.py   fetch + parse + color model
tools/serve.py        dev server (opzionale)
```

Motivi:

- si apre con `file://` e si può allegare come singolo file → massima
  condivisibilità, zero installazione per l'utente finale;
- niente `node_modules`, niente build, niente rotta di aggiornamento dei pacchetti;
- il dataset è pre-elaborato: il browser non deve fare il parsing delle frasi
  colore, il modello è già dentro il JSON;
- performance: 167 KB di JSON, tutto in locale, prima paint immediato;
- deployabile su GitHub Pages / Netlify / un qualsiasi serverino senza
  dipendenze.

Alternativa considerata: Vite + TypeScript (migliore DX e tipizzazione, ma
aggiunge un toolchain). Framework SPA (React/Vue): non giustificato, la pagina
è quasi interamente statica e deve funzionare offline.

---

## 7. Struttura finale del file

```
drug-checking-reagents-color-chart/
├── index.html
├── assets/
│   ├── styles.css          design system, temi, print
│   ├── app.js              stato, filtri, rendering
│   ├── colors.js           palette curata + nearest-colour
│   └── data.js             caricamento JSON
├── data/
│   └── reagents.json       (generato, committato)
├── tools/
│   ├── build_data.py       estrazione + modello colore
│   ├── serve.py            dev server
│   └── cache/wikitext.txt  sorgente grezza cache
├── DESIGN.md
└── README.md
```

---

## 8. Domande aperte

1. **Stack**: statico senza build (proposto) vs Vite+TypeScript?
2. **Lingua**: interfaccia in italiano, inglese, o bilingue con toggle?
   (i nomi delle sostanze restano in inglese: sono nomi chimici)
3. **Matching del colore**: solo famiglie di tinta, o anche intensità e frase
   esatta? Con l'occhiello?
4. **Combinazione multi-reagente** con semantica AND: sì o no?
5. **Perimetro dei dati**: solo Wikipedia (massima fedeltà, citazioni) o
   arricchire con altre fonti (reagent-tests.uk, DanceSafe, NIJ)?
6. Priorità: eseguire il set minimo (1, 2, 3, 4 + viste A/B) o tutto subito?

---

## 9. Avvertenze da mantenere in pagina

Il testo introduttivo di Wikipedia va mantenuto, non nascosto:

> I test con reagenti sono **solo preliminari**. Un colore non è
> un'identificazione, e un risultato negativo **non esclude** la presenza di una
> sostanza. Alcuni tester mostrano il colore della sostanza desiderata senza
> mostrare un colore diverso per un additivo più pericoloso: servono **test
> multipli** per rivelare le adulteranti.

In più: i colori variano tra kit e brand, i dati risalgono al 2000–2024, e per
alcuni reagenti la copertura è di 1-4 sostanze su 82 — la pagina deve dirlo
ovunque, non in una nota a piè di pagina.
