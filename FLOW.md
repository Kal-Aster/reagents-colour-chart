# Flusso d'esperienza (v1 semplificata)

Il design tecnico è in `DESIGN.md`. Qui: **come si usa la pagina**.

> **Nota su "più semplice per ora".** La prima bozza prevedeva una "sessione di
> test" con osservazioni multiple, candidati con il "perché" e test successivo
> consigliato. È stato semplificato: **un'unica schermata, una tabella, un
> filtro**. Le funzioni più ricche restano nel backlog (v2) e sono indicate in
> fondo.

---

## 1. Chi la usa

| | **Il banco** (operatore di drug checking) | **Il kit a casa** | **Il curioso** |
|---|---|---|---|
| Situazione | 10-20 campioni al giorno, coda, cliente che aspetta | solo, la sera, con 1-2 test | nessun campione |
| Domanda | "che colore mi aspetto per questa sostanza?" | "il mio campione è MDMA?" | "cos'è questo?" |
| Pressione | alta | media | zero |
| Dispositivo | telefono | telefono | ovunque |

Nella v1 il banco e l'utente domestico usano **la stessa schermata** con filtri
diversi. Il curioso trova la tabella e la legge.

---

## 2. La schermata

Una pagina, tre blocchi, in ordine di importanza decrescente.

```
┌──────────────────────────────────────────────────────────────┐
│  Test con reagenti: solo preliminari, non identificano.  ⓘ  │
├──────────────────────────────────────────────────────────────┤
│  Reagente ▾  │  Colore osservato ▾  │  Tipo ▾  │  Cerca     │
│  Marquis    │  [swatch + nome]      │  tutte  │  _________  │
│  32/82 documentati                  │          │             │
├──────────────────────────────────────────────────────────────┤
│  12 corrispondenze · 3 in conflitto · 51 senza dati         │
├──────────────────────────────────────────────────────────────┤
│  Sostanza         │ Tipo        │ Marquis                   │
│  ───────────────────────────────────────────────────────────│
│  MDMA             │ Substance  │ ▮ viola scuro → nero  ✓   │
│  MDA              │ Substance  │ ▮ viola scuro → nero  ✓   │
│  2C-B             │ Substance  │ ▮ giallo → verde      ✓   │
│  ══════ divisore: "altre sostanze" ══════                   │
│  Amphetamine      │ Substance  │ ▮ rosso‑arancio      ≈   │
│  Fentanyl         │ Substance  │ ⬚ nessun dato              │
└──────────────────────────────────────────────────────────────┘
```

Nessuna modalità, nessun wizard, nessuna scelta iniziale da fare. Si apre e si
usa.

### L'ordinamento: le corrispondenze in cima, tutto il resto sotto

La tabella **non si filtra**: si **ordina**.

```
[ righe che corrispondono al colore osservato ]
═════════════  "altre sostanze"  ═════════════
[ righe in conflitto o sfumatura ]
═════════════  "senza dati per Marquis"  ═════════════
[ righe senza dati — tratteggiate, comunque consultabili ]
```

Tre motivi:

1. **le corrispondenze sono subito visibili**, senza dover scorrere 82 righe;
2. **tutte le sostanze restano consultabili** — l'utente che cerca "cosa mi
   ricorda il fentanyl" la trova comunque, e l'utente del banco deve poter
   sfogliare la colonna intera;
3. **il divisore dice perché le righe sono separate**, e il riquadro in testa
   ("51 senza dati") spiega cosa significa.

L'ordine interno dei gruppi: corrispondenza diretta → sfumatura compatibile →
in conflitto → nessun dato. Dentro ogni gruppo: per tipo (Substance,
Adulterant, Class, Forms), poi alfabetico.

---

## 3. Il filtro "colore osservato" — e come ci aggiunge il tempo

Il punto delicato, e il posto dove la pagina può valere davvero.

### 3.1 Il caso semplice

Il selettore è uno **swatch + nome**: si vede il colore e lo si sceglie.
Nessun campo di testo da compilare.

- 12 tinte (famiglie)
- sotto, l'intensità (opzionale) e la frase esatta (opzionale, bilingue)
- la frase esatta serve a chi ha letto una tabella e cerca quella formulazione;
  per il resto basta lo swatch

Il match avviene a due livelli, e la differenza va resa visibile:

- **corrispondenza diretta** — il colore documentato è quello osservato
  (stessa tinta, stessa intensità)
- **sfumatura compatibile** — la tinta osservata è un *qualificatore* del
  colore documentato (es. osservi "verde", è documentato "verde scuro") o
  viceversa

Le due cose non vanno mischiate: una sfumatura è un indizio, una corrispondenza
diretta è un indizio forte. Nella tabella: bordo pieno + ✓ vs bordo tratteggiato
+ ≈.

### 3.2 Il caso con il tempo: l'evoluzione del colore

Alcune sostanze non danno un colore, danno una **sequenza**. Wikipedia ne
documenta 41 su 102 (19 "shift", 1 "intensify"), per esempio:

- `2C-B` Marquis: **giallo → verde**
- `MDA`/`MDMA` Marquis: **viola scuro → nero**
- `Zucchero` Marquis: **bianco → giallo chiaro → nero**
- `Levamisole` Liebermann: **marrone → marrone molto scuro** (scurimento)

E c'è il caso che descrivi tu, che è il più diagnostico in assoluto:

> *"diventa subito giallo, poi rosso e poi di nuovo giallo, e se non diventa di
> nuovo giallo è un'altra sostanza"*

Qui il **ritorno** è l'informazione: non il colore di arrivo. Una sostanza che
non torna indietro è un'altra sostanza. Questa proprietà va esplicitamente
modellata (`trajectory.kind = "revert"`), non lasciata implicita.

**Come si inserisce nel filtro senza complicare l'interfaccia:**

un interruttore *"il colore cambia nel tempo?"* che, quando attivo, cambia il
selettore colore in un **editor di sequenza**. La sequenza descrive **un
reagente alla volta**: prima si sceglie il reagente, poi si descrive quello che
si è visto.

```
   [giallo ▾]  →  [rosso ▾]  →  [giallo ▾]  [ + tappa ]
   iniziale         poi            alla fine
```

Nessun limite artificiale di tappe (nella pratica sono 2-4, ma il dato non
impone un tetto). Ogni tappa ha una tinta e un'intensità opzionale.

**Il tempo entra subito nel modello**, anche se per ora poche fonti lo danno:
ogni tappa può avere una finestra temporale ("entro 30 secondi", "dopo 1
minuto"). Il chart Grassroots fornisce "0:00 → 0:30 secondi" per la maggior
parte dei reagenti, quindi il dato esiste ed è uniforme: si introduce la
struttura adesso, così non va ripensata dopo.

Il match passa da "un colore" a "una sequenza", con tre esiti:

| Esito | Significato | Come si mostra |
|---|---|---|
| **piena** | la sequenza documentata contiene quella osservata | ✓ pieno |
| **parziale** | la sequenza documentata prevede un rITORNO che tu non hai osservato | ⚠ "manca il ritorno a giallo" |
| **conflitto** | le tinte non coincidono | ✗ |

Il caso "parziale" è il motivo per cui il modello serve: senza i tempi si
vedrebbe solo che "giallo" c'è, e si perderebbe l'informazione diagnostica del
ritorno mancante.

### 3.3 Il colore che non è nel vocabolario

Nessuno dice "purplish red". Se scrivo "beige", "nerd", "giallo sporco" o
"viola scuro" in italiano, il campo deve **proporre** le voci vicine, non
rispondere "nessun risultato". Sotto il campo, le 3-4 proposte più vicine,
selezionabili. Le frasi esatte del vocabolario sono bilingui (IT/EN).

---

## 4. Il colore come informazione, mai come unico canale

Su una pagina di colori questa è la regola madre.

- ogni swatch ha **accanto la descrizione testuale**, sempre
- nella tabella, una cella colorata mostra: **il gradiente misurato** (non un
  colore piatto) + la didascalia testuale. Il gradiente è il dato reale — il
  nome del colore è solo un aiuto, e sbagliare il nome non può più trarre in
  inganno. Le tappe sono separate da una freccia nella didascalia
- il trattino di una cella senza dati è **tratteggiato**, non un vuoto: "?"
  ≠ "nessuna reazione"
- nel confronto cella-per-cella, gli stati sono **parole**: "coincide",
  "in conflitto", "nessun dato" — non solo icone colorate

---

## 5. Il filtro reagente

Il selettore reagente è il filtro principale, e mostra la copertura accanto al
nome, perché è essa che dice quanto puoi fidarti:

> **Marquis** — 32 sostanze su 82 documentate

Reagenti con copertura bassa (Morris 1/82, Folin's 2/82, Liebermann 4/82) lo
dicono apertamente: sono elencati per completezza, non perché servano.

Un campo `common` distingue i reagenti dei kit reali da quelli specialistici
(derivato dalla tabella "Custom reagents" dell'articolo: Morris non compare,
Morris è da laboratorio).

### Colonna singola o tabella completa?

Il selettore reagente ha due modi:

- **colonna singola** (default): sostanza | tipo | colore del reagente scelto.
  Leggibile da telefono, che è dove si sta.
- **tutte le colonne**: la matrice 82 × 8, con intestazioni sticky.

La matrice è per il 84% vuota (78% di celle sconosciute). Per non sembrare un
errore, di default **nasconde le righe che non hanno dati per il reagente
scelto**, con un interruttore per mostrarle.

---

## 6. L'intestazione che racconta la copertura

Sopra la tabella, sempre:

> **12 corrispondenze** · 3 in conflitto · **51 sostanze senza dati per Marquis**

La terza cifra è quella che conta. Un campione che dà "nessuna reazione" con
Marquis **non esclude** 51 sostanze su 82 — tra cui fentanil e opioidi
sintetici, che non hanno dati in nessun reagente.

Questo non è un dettaglio: è l'avvertenza della fonte, resa operativa. E per
questo la cifra va sempre in testa, non in una nota a piè di pagina.

---

## 7. Il percorso completo (v1)

1. **Apro la pagina** → vedo il banner "solo preliminari" e la tabella.
2. **Scelgo il reagente** che ho usato → la tabella si restringe a quella colonna.
3. **Scelgo il colore** che ho visto → le celle corrispondenti si evidenziano,
   i conflitti si barrano, il riepilogo in testa si aggiorna.
4. **Se il colore evolve**, attivo "il colore cambia nel tempo" e descrivo la
   sequenza → il match passa a sequenza, e segnala i ritorni mancanti.
5. **Guardo una sostanza** → click sulla riga → si espande con gli altri
   reagenti (quelli che ho), le fonti, gli alias, i link.
6. **Esco con un link** → l'URL porta i filtri, così posso riaprire la stessa
   situazione o mandarla.

---

## 8. Cosa NON facciamo

- niente account, niente server, niente profili
- niente quiz, niente gamification
- niente stima del rischio di overdose (fuori perimetro, e pericoloso)
- niente "taratura" dei colori sul proprio kit: non abbiamo dati per farlo
- niente foto: nessuna fonte dati lo supporta
- niente edizioni non citate dei dati

---

## 9. Backlog v2 (le cose che oggi tagliamo)

- **Sessione multi-osservazione**: più reagenti con semantica AND, la vera
  potenza del matching ("Marquis viola + Simon's blu → MDMA")
- **"perché" per riga**: ogni osservazione confrontata con la scheda della
  sostanza, in una tabella dentro la riga
- ~~**test successivo consigliato**~~: **fatto** (D162–D180) — il pannello
  «il prossimo test» dice quanti candidati restano dopo ogni reagente non
  ancora usato, contandoli per colore
- **occhiello** (`EyeDropper`): campionare il colore fisico dallo schermo

> **Nota**: il chart Grassroots Harm Reduction **entra in v1** come fonte #2
> (decisione D19). Porta i gradienti (= evoluzione nel tempo), i tempi
> ("0:00 → 0:30 s"), "NO REACTION" esplicito, tre reagenti in più (Robadope,
> Ehrlich, Hofmann) e le note di protocollo. Va deciso come trattare il diritto
> d'autore (decisione aperta O1 in `DECISIONS.md`) e va acquisito il file
> originale per una trascrizione accurata.

---

## 10. Decisioni aperte

Rimandate ai prossimi riferimenti: il registro completo è in `DECISIONS.md`.

1. Il banner "solo preliminari" è una riga in alto o una barra intera?
   → **deciso: riga compatta sempre visibile** (D18)
2. Il selettore colore parte dalla **tinta** o dalla **frase esatta**?
   → **deciso: swatch + nome**, frase esatta in secondo livello (D15)
3. L'editor di sequenza: quante tappe al massimo?
   → **deciso: senza limite, una traiettoria per reagente** (D16)
4. I tempi si inseriscono o restano fuori finché non ci sono fonti che li danno?
   → **deciso: si introducono subito il concetto** (D17)
5. Il riepilogo in testa: una riga o tre cifre con spiegazione al passaggio del
   mouse? → aperto
