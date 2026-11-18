# Piano della pagina

La **tabella è al centro**. Prima c'è solo il campo per le osservazioni che
riordinano le righe; dopo, in fondo, i dettagli della raccolta e i link.

---

## Struttura

```
┌────────────────────────────────────────────────────────────────┐
│ I test con reagenti sono solo preliminari. Non identificano.   │
│ Serve più di un test.                        [IT ▾]            │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  LE MIE OSSERVAZIONI                        [+ aggiungi]       │
│  ┌──────────────────────────────────────────────┐              │
│  │ Marquis   ▮ viola scuro                    ✕ │              │
│  │ Simon's   ▮ nessuna reazione               ✕ │              │
│  └──────────────────────────────────────────────┘              │
│                                                                │
│  12 corrispondenze · 3 in conflitto · 342 senza dati           │
│  [ ] Mostra tutte le 397 sostanze                              │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  LA TABELLA                                                    │
│  Sostanza      │ Tipo      │ Marquis  │ Simon's │ Froehde │ …  │
│  ─────────────────────────────────────────────────────────────  │
│  MDMA          │ Substance │▮ viola→nero│ blu   │ ▮ grigio→│  │
│  MDA           │ Substance │▮ viola→nero│  —    │ ▮ grigio→│  │
│  2C-B          │ Substance │▮ giallo→verde│ —  │ ▮ giallo│  │
│  Amphetamine   │ Substance │▮ rosso→marrone│ — │ ▮ verde  │  │
│  Fentanyl      │ Substance │ ⬚ nessun dato                     │  │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  I DATI E LE RISORSE (in fondo)                                │
│  le 5 fonti · il metodo · le licenze · i link · i limiti noti  │
└────────────────────────────────────────────────────────────────┘
```

---

## Le tre sezioni

### 1. Le mie osservazioni — prima della tabella

Un riquadro che si apre sul click ("+ aggiungi"). Ogni osservazione è una riga:

```
[reagente ▾] [colore ▾]  ✕
```

Il selettore del colore è uno **swatch + nome**: 12 famiglie di tinta, e sotto
l'intensità e la frase esatta come opzioni secondarie.

Con le osservazioni inserite:
- la tabella **si riordina**: le corrispondenze in cima, separate da un divisore,
  tutte le altre sotto, comunque consultabili;
- la colonna del reagente osservato è in evidenza;
- il riepilogo in testa dice quante corrispondenze, quanti conflitti, e **quante
  sostanze non hanno dati** per i reagenti che hai usato.

### 2. La tabella — al centro

Matrice: riga = sostanza, colonne = reagente (11, con scroll orizzontale e
intestazioni e prima colonna sticky).

Ogni cella:
- **0 fonti** → bordo tratteggiato, trattino, "nessun dato". Mai una cella vuota:
  il vuoto verrebbe letto come "nessuna reazione".
- **1 fonte** → la striscia + la didascalia.
- **N fonti** → la striscia + i pallini (uno per fonte).
- **conflitto** → bordo ambigato + badge "fonti in disaccordo".

La striscia è **sempre un gradiente** dal colore iniziale a quello finale:
per i chart sono i campioni pixel veri resi come `linear-gradient`, per le fonti
che dichiarano il colore a parole gli stadi come swatch con freccia. Tutte le
fonti si leggono allo stesso modo e la striscia *è* il dato.

**Il livello delle sostanze.** Di default la tabella elenca le **59 sostanze
pratiche** (quelle con 2+ reagenti documentati: MDMA, cocaina, eroina, ketamina,
2C-B…). Un interruttore "Mostra tutte" porta a 397.

Ma il **matching guarda sempre tutte e 397**, indipendentemente dall'interruttore:
se una sostanza fuori dalle 59 corrisponde alle tue osservazioni, **sale in cima
e la vedi lo stesso**. L'interruttore governa solo ciò che è *elencato*, non
ciò che è *confrontato*. È la differenza tra "non lo vedo" e "non esiste".

### 3. I dati e le risorse — in fondo

Una sezione compatta, in fondo alla pagina: le 5 fonti con anno e link, come
sono state lette, le licenze, e i limiti noti (copertura parziale, i colori
variano tra kit e brand, i tempi non sempre documentati).

Niente di questo compete con la tabella per l'attenzione.

---

## Il matching del colore

Tre esiti per cella:

| esito | condizione |
|---|---|
| **pieno** | la sequenza documentata contiene quella osservata |
| **parziale** | la documentazione prevede un **ritorno** che non hai osservato |
| **conflitto** | le tinte non hanno niente in comune, o una fonte dice "nessuna reazione" e un'altra un colore |

Il caso "parziale" è il payoff del modello delle traiettorie: senza i tempi si
vedrebbe solo che "giallo" c'è, e si perderebbe l'informazione diagnostica del
ritorno mancante.

L'ordinamento dentro i gruppi: per tipo (Substance → Adulterant → Class →
Forms), poi per **accordo fra fonti** (più fonti corroborano → meno), poi
alfabetico.

---

## Il dettaglio della sostanza

Click su una riga → pannello laterale con:

- nome, tipo, alias, link a Wikipedia
- **tutti** i reagenti con la loro striscia
- per ogni cella: **tutte le letture affiancate**, ognuna con fonte e anno, e i
  conflitti spiegati ("una fonte dice nessuna reazione, tre riportano un colore")
- le fonti citate, con la loro qualità (peer-reviewed / NIJ / chart di pratiche)
- la sezione "custom reagents": quale reagente per quale classe
- le sostanze con lo stesso profilo di colori

---

## Fasi

| fase | contenuto | criterio di "fatto" |
|---|---|---|
| **F1** ✅ | dati, sezione osservazioni, matrice, rendering delle strisce, dettaglio, IT/EN, tema chiaro-scuro, accessibilità | **fatto**: Lighthouse 100/100/100, 397 righe in 18 ms |
| **F2** | il matching: palette, intensità, frase esatta, riordino con divisore, il livello 59/397 con le corrispondenze sempre visibili | "Marquis → viola scuro" mette le corrispondenze in cima, anche quelle fuori dalle 59 |
| **F3** | l'editor di sequenza e il "ritorno mancante" | "giallo → rosso → giallo" distingue le sostanze che tornano |
| **F4** | i conflitti e l'accordo fra fonti nel dettaglio | ogni cella multi-fonte mostra le letture e il verdetto |
| **F5** | URL condivisibile, export CSV, stampa, glossario dei reagenti | un link riapre la stessa situazione |

F1 e F2 sono il nucleo.

---

## Decisioni prese

Tutte le domande sono chiuse: una striscia + icona info, reagenti in ordine
alfabetico con la copertura accanto, editor di sequenza in F3, matrice con
scroll orizzontale e prima colonna sticky, apertura sulle 59 con interruttore.

### L'editor di sequenza: come l'utente la usa

Quando l'utente abilita "il colore cambia nel tempo", la riga dell'osservazione
diventa:

```
[Marquis ▾]  [giallo ▾] → [rosso ▾] → [giallo ▾]  [+ tappa]  ✕
```

Ogni tappa ha una tinta e, opzionalmente, un tempo ("entro 30 s", "dopo 1
minuto"). I tempi restano opzionali: poche fonti li danno.

**Non serve sapere la sequenza completa.** L'utente può scrivere quello che ha
visto e basta:

- scrive **una sola tappa** ("subito giallo") → il sistema confronta il primo
  stadio della traiettoria documentata;
- scrive **"giallo → rosso"** e la documentazione prevede un ritorno → esce
  "parziale: manca il ritorno a giallo", che è l'informazione diagnostica;
- scrive **"giallo → verde"** e la documentazione dice "rosso → verde" →
  "conflitto".

L'utente che non sa se il colore è tornato scrive quello che ha visto: il
sistema dice cosa manca.
