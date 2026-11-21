# Decisioni prese

Registro delle decisioni prese in discussione, con la data e il motivo.
Le decisioni non ancora prese sono in fondo.

---

## 2026-11-15 — Struttura dati e pipeline

| # | Decisione | Motivo |
|---|---|---|
| D1 | Fonte dati v1: **Wikipedia** ("List of reagent testing color charts", oldid `1302153309`) | Massima tracciabilità, ogni cella citata |
| D2 | Il modello dati pre-elabora i colori **a build time** (`tools/build_data.py`), il browser non fa parsing | Il JSON contiene già tappe, tinte, qualificatori, modificatori |
| D3 | Il "?" (78% delle celle) è uno **stato**, distinto da "no reaction" | L'errore più pericoloso di una tabella di riduzione del danno: vuoto letto come "negativo" |
| D4 | Ogni cella = lista di **osservazioni** con la fonte, non un valore unico | Wikipedia a volte unisce due fonti in disaccordo nella stessa cella |
| D5 | Le fonti sono ordinate per qualità dichiarata (peer-reviewed > NIJ > vendor > community > forum) | Per non presentare un video YouTube come se fosse uno studio forense |
| D6 | Override manuali per le celle rotte di Wikipedia, con nota in pagina | Es. PMA/Froehde: "n" + gradiente copiato dalla cella vicina → "No reaction" |

---

## 2026-11-15 — Modello del colore

| # | Decisione | Motivo |
|---|---|---|
| D7 | Un colore = **tappe** (progressione) → **sfumature** parallele → {tinte primarie, qualificatori, intensità} | Le 79 frasi della fonte non sono colori ma descrizioni con intensità, sfumature e sequenze |
| D8 | Gli aggettivi in `-ish` (`bluish`, `purplish`) sono **qualificatori**, non tinta primaria | "Deep purplish red" = rosso profondo tendente al viola |
| D9 | Esistono **4 tipi di evoluzione**: `static`, `shift`, `intensify`, `revert` | Il caso `revert` (il colore torna indietro) è il più diagnostico in assoluto |
| D10 | Palette **curata** di 12 famiglie × intensità, non gli hex di Wikipedia | Gli hex di Wikipedia sono incoerenti ("Moderate olive" e "Dark olive" sono lo stesso #808000) |
| D11 | Il colore non è mai l'unico portatore di informazione | Regola madre su una pagina di colori (WCAG 1.4.1) |

---

## 2026-11-15 — Flusso (v1 semplificata)

| # | Decisione | Motivo |
|---|---|---|
| D12 | **Una schermata**, una tabella, un filtro. Nessuna modalità, nessun wizard | "Più semplice per ora": le funzioni ricche sono backlog, non struttura portante |
| D13 | Il reverse lookup "colore → sostanze" **non è una vista separata**: è la tabella filtrata per colore | Una sola meccanica, tre usi |
| D14 | Le righe che **corrispondono** al colore osservato vanno **in cima**, separate da un divisore, seguite da tutte le altre | Tutto resta consultabile, ma le corrispondenze sono subito visibili |
| D15 | Il selettore colore è uno **swatch + nome** (non un campo di testo) | Si vede e si sceglie un colore, non si scrive una frase |
| D16 | L'editor di sequenza descrive **una traiettoria per reagente**, senza limite artificiale di tappe | L'evoluzione si osserva su un reagente alla volta |
| D17 | Si **introduce subito il concetto di tempo** nel modello, anche se poche fonti lo danno | Così la struttura è pronta quando arriveranno fonti con tempi ("0:00 → 0:30 s") |
| D18 | Il banner "solo preliminari" è **una riga compatta sempre visibile**, non una barra a tutta larghezza | Sul telefono lo spazio verticale è la risorsa scarsa; la versione operativa dell'avvertenza sono le cifre di copertura |
| D19 | Il **chart Grassroots Harm Reduction entra in v1** come fonte #2 | I gradienti *sono* l'evoluzione nel tempo; aggiunge tempi, "NO REACTION", 3 reagenti in più e copertura più densa |
| D20 | Stack: **statico senza build step**, vanilla JS, JSON locale | Si apre con `file://`, funziona offline, zero dipendenze |
| D21 | UI **bilingue IT/EN** con toggle; i nomi delle sostanze restano in inglese con `lang="en"` | Sono nomi chimici; lo screen reader li pronuncia correttamente |
| D22 | Matching: famiglie di tinta + intensità + frase esatta; corrispondenza diretta e sfumatura **distinte** | Una sfumatura è un indizio, una corrispondenza diretta è un indizio forte: non vanno mischiate |
| D23 | I gradienti dei chart vengono **estratti campionando i pixel**, non trascritti a occhio | La traiettoria diventa un dato misurato; rende possibile il confronto tra fonti |
| D24 | Ogni cella = **lista di osservazioni** (una per fonte) + flag `conflict` | 16 conflitti reali tra Wikipedia e Grassroots: la pagina non deve scegliere da sola, deve mostrare entrambe le letture |
| D25 | Il chart Grassroots entra **anche come immagine originale, invariata**, nella pagina | "Distribute freely without changes": la riproduzione è consentita, la trascrizione no (vedi O1) |
| D26 | Il chart ProTestKit (Mandelin) entra come **fonte #3** | ~430 sostanze con gradienti misurati: è la fonte con le evoluzioni a più fasi e i ritorni di colore |
| D27 | Il dato "PMA / Froehde" **non viene forzato** a una risoluzione | La fonte Wikipedia è rotta ("n") e il chart Grassroots dice "verde pallido": il conflitto si mostra, non si arbitra |
| D28 | La cella mostra **il gradiente misurato**, non un colore piatto | Il gradiente è il dato reale; il nome del colore è solo una didascalia. Un nome sbagliato non può più trarre in inganno |
| D29 | Le traiettorie sono segmentate **per angolo di tinta**, non per nome famiglia | I confini fra famiglie sono arbitrari e un gradiente li attraversa: per nome verrebbero inventate fasi che il chart non mostra |
| D30 | Le fonti non vengono "mediate": ogni cella espone tutte le osservazioni | 23 conflitti reali. La pagina mostra entrambe le letture e segnala il conflitto |

---

## 2026-11-16 — Editor delle osservazioni e lettura della tabella

| # | Decisione | Motivo |
|---|---|---|
| D31 | Nel selettore **"nessuna reazione" sta prima dei colori**, su una riga tutta sua | Le sezioni si leggono nell'ordine in cui si sceglie: che cosa è successo, il colore, l'intensità |
| D32 | L'intensità è **visibile solo quando un colore è scelto** (nascosta altrimenti, non creata al volo) | Con "nessuna reazione" o senza colore l'intensità non significa niente; crearla al volo rompeva il pannello dopo la scelta |
| D33 | La tendina **si posiziona dove c'è spazio**: si ribalta in alto, si apre a sinistra, si restringe e scorre dentro | Con lo scroll bloccato dal piano, una tendina fuori pagina sarebbe irraggiungibile |
| D34 | Nel selettore la scelta è **in anteprima** e si applica solo con "conferma" | Chiudere la tendina al click sul colore non dava il tempo di scegliere l'intensità |
| D35 | I tasti sono: **elimina** a sinistra (rosso), separatore, **annulla** discreto, **conferma** evidente | L'eliminazione sparisce quando la fase è l'unica: non c'è niente da eliminare |
| D36 | Il modificatore `very` si chiama **"molto scuro"**, non "molto" | "grigio molto" non dice niente: `very` è la variante più scura di ogni tinta, non una degree a sé |
| D37 | Le celle della striscia di intestazione hanno **l'altezza della striscia** (misurata sul testo) e il contenuto **centrato in verticale** | La cella "Sostanza", alta una riga, lasciava vedere le coperture delle colonne che passavano sotto |
| D38 | In una cella **"nessuna reazione" compare una volta sola**, con il numero delle fonti (`×3`) | Quattro fonti che dicono la stessa cosa occupavano quattro righe senza aggiungere informazione; l'elenco delle fonti resta nel popover |

---

## 2026-11-16 — La quantità di prodotto

| # | Decisione | Motivo |
|---|---|---|
| D39 | Il **caricamento** diventa un asse del modello, non un colore | "Nero con Simon's" e "nero con Marquis" non sono la stessa cosa: uno dipende dalla quantità, l'altro dal tempo. Mischiarli rende ambigua la parola "nero" |
| D40 | Le tappe portano il loro livello (`stage.loading`), il selettore sceglie il livello mostrato | Una serie attraversa più livelli (Tang: da solido a 0,1 mg/mL): il filtro deve poter selezionare un sottoinsieme di tappe |
| D41 | Se una cella non ha dati al livello scelto, mostra le letture a dose di riferimento **segnate con una linea tratteggiata** | La cella non può sembrare vuota (sembra un dato mancante), ma nemmeno far credere che quei colori valgano a dosi elevate |
| D42 | Un confronto a un livello diverso da quello documentato dà **"parziale"**, mai "pieno" | Il colore è documentato, ma per un'altra quantità: non è la stessa corrispondenza |
| D43 | La convenzione di caricamento è dichiarata nel **pannello di sicurezza** | I colori dei chart valgono per una dose di riferimento: con una dose ridotta la reazione può non vedersi, con una dose generosa il colore si scurisce |
| D44 | La prima fonte per quantità è **Tang et al. (2010), figura 3** | Unica serie found in cui l'asse è la quantità; copre proprio il caso della metanfetamina con Simon's |

---

## 2026-11-16 — La pagina come strumento consultabile

| # | Decisione | Motivo |
|---|---|---|
| D45 | Nel glossario dei reagenti compaiono **nota di protocollo, tempi e copertura** (dati già presenti nel file, mai mostrati) | Il lettore non poteva sapere a cosa serve ogni reagente né quanto tempo dà: informazioni già estratte che non arrivavano a schermo |
| D46 | Le note sul **caricamento** stanno nel glossario, solo dove una fonte le documenta | Meglio una nota citata per un reagente che una regola generica ripetuta: la regola generale (dose di riferimento) è nel pannello di sicurezza |
| D47 | Le osservazioni dell'utente **non vengono salvate in pagina** | Sono lo stimolo per costruire lo strumento, non un dato da pubblicare: restano in memoria, nella sessione |

| D48 | Le schede dei reagenti sono **tradotte** e raggruppate per **set standard / specialistici** | Le intestazioni delle tabelle di Wikipedia ("Folin's—Mandelin") non sono un gruppo che un lettore può usare; il gruppo vero è quello del chart Grassroots |

| D49 | L'asse si chiama **proporzione** (prodotto : reagente), non "dose" | La quantità assoluta non è la variabile: la stessa sostanza con più reagente dà una reazione più debole |
| D50 | La proporzione sta **in ogni osservazione**, non in un selettore globale | Un test può essere caricato diversamente dal successivo: il rapporto è una scelta che si dichiara |
| D51 | Ogni lettura in cella porta l'etichetta della **proporzione**; "proporzione consigliata" sempre, le altre solo se esistono | Il lettore deve sapere a quale rapporto si riferisce il colore; le proporzioni documentate per reagente stanno nel glossario |
| D52 | L'assenza di dati si **scrive** ("nessun dato"), non si disegna, e **tutte le fonti** sono elencate nelle tendine e nel dettaglio | Un quadratino tratteggiato dice "qui non c'è niente" ma non quale fonte manca; una fonte elencata con "nessun dato" dice che l'abbiamo cercata e non aveva niente |
| D53 | La sezione **"Corrispondenze" c'è anche quando è vuota**, con un empty state che dice perché | Una sezione che sparisce non dice nulla; l'empty state dice quante sostanze non corrispondono, quante sono in conflitto e che il colore dipende anche dalla proporzione |

| D54 | Un'osservazione **senza colore** non partecipa al riordinamento | Un test appena aggiunto non deve spostare le righe: il riordinamento ha senso solo quando c'è un colore da confrontare |
| D55 | Le **colonne** seguono l'uso: prima i reagenti delle osservazioni (nell'ordine in cui sono stati usati), poi tutti gli altri in ordine alfabetico | Chi sta testando con Marquis e Robadope li cerca subito, non in fondo alla tabella |
| D56 | Il link alle fonti è la **parola "fonti"**, non un'icona | Una "i" in un cerchio non dice cosa apre; la parola sì. Sta in alto a destra nella cella |
| D57 | Il popover delle fonti è una **griglia** (colore, descrizione, fonte) | Le righe disallineate rendevano impossibile confrontare le fonti a colpo d'occhio |
| D58 | Il confronto sulla **proporzione è flessibile**: un colore documentato a un'altra proporzione è comunque una corrispondenza (parziale) | Se vedo nero col Simon's e una fonte documenta nero ad alta proporzione, la sostanza è quella: non deve sparire |
| D59 | La cella mostra **tutte le proporzioni documentate**, ognuna con la sua etichetta | La cella è un riferimento: mostrare solo la proporzione in uso nasconde metà dei dati. Se la proporzione del tuo test non è documentata, la cella lo dice |

| D60 | La **riga** non viene più dipinta: è la **cella** che corrisponde a mettere in evidenza (anello colorato) | "Quale reagente ha corrisposto?" è la domanda; dipingere tutta la riga la nascondeva. La colonna del nome resta con una tinta leggera |
| D61 | Al passaggio del mouse sulla riga, **tutto** il testo dentro prende l'inchiostro del colore di hover | Le etichette di proporzione e le note restavano scure sul fondo accent: illeggibili |
| D62 | Il vecchio "conflitto" si chiama **"in disaccordo con una fonte"** | Non è un conflitto fra fonti (il flag della cella resta falso): è la tua lettura che una fonte non condivide. La cella dice quale dei due casi è |

| D63 | Al passaggio del mouse la riga **non viene più riapinta** in un colore saturo | Riaprendola l'inchiostro del testo doveva cambiare e qualcosa sfuggiva sempre; ora i colori del testo non cambiano mai e la leggibilità è garantita per costruzione (misurata: 6,3:1 sul fondo dell'hover) |
| D64 | La cella ha **tre stati**: corrispondenza (accent), disaccordo con una fonte (rosso), **avviso** (giallo) | L'avviso copre il caso "hai visto nessuna reazione ma nessuno ha documentato questa sostanza con questo reagente": non è un conflitto, è un test che non poteva escluderla |
| D65 | Il **conflitto fra le fonti** si vede in tabella, con il badge "≠" | Prima si trovava solo nel popover: la cella del methylone con Marquis (le fonti dicono "brown" e altro) sembrava normale |
| D66 | Il CSS e lo script hanno un **parametro di versione** | Senza, il browser serve il foglio vecchio dalla cache: le correzioni non arrivavano |

| D67 | "Tu vedi un colore e una fonte dice «nessuna reazione»" **non è un conflitto**: la sostanza è semplicemente esclusa, senza segnalazione | Era il caso di 3-MeO-PCP col Marquis (l'unica fonte che lo documenta dice "No colour change"): la sostanza è fuori, ma segnalarla come problema non aveva senso. Il rosso resta solo per il caso opposto — tu vedi "nessuna reazione" e una fonte documenta un colore — che è quello che può dipendere dalla tecnica |

| D68 | Le osservazioni diventano una **maschera di bit**: una sostanza che corrisponde a due test su tre è 110 e viene prima di una 001 | L'ordine dice subito quanto è solida la corrispondenza; a parità di maschera l'alfabetico tiene vicine le sostanze che si somigliano |
| D69 | Una sostanza che **non corrisponde a nessun** test è semplicemente esclusa, in silenzio | Segnalare anche l'esclusione riempiva la tabella di rosso senza informare: l'esclusione è la risposta normale |
| D70 | Il rosso segnala le sostanze che **corrispondono agli altri test ma non a questo** | È una contraddizione fra le tue osservazioni, non fra una fonte e te: la sostanza si spiega con due test e non con il terzo |
| D71 | Il giallo segnala le sostanze che **non hanno dato** per quel reagente | Nessun dato non è un "no": il test non poteva escluderle |

| D72 | Le evidenziazioni (rosso, giallo) valgono **solo nella sezione "Corrispondenze"** | Nelle "altre sostanze" una cella rossa suggeriva un problema che non c'è: se una sostanza non spiega nessuno dei tuoi test, è esclusa e basta |
| D73 | L'avviso giallo vale solo per i **reagenti che hai testato** | Nelle altre colonne "nessun dato" è semplicemente "nessun dato": non hai fatto quel test, quindi non c'è nulla da segnalare |

| D74 | Le icone "?" e "≠" sono **tolate**: la corrispondenza si segna sulla cella, sulla **striscia** (outline verde) e sul **nome del colore** (verde) | Due simboli da decifrare in una tabella piena di dati; la marcatura è più precisa quando dice *cosa* corrisponde |
| D75 | Un "nessuna reazione" che corrisponde all'osservazione è **in grassetto verde** | Il verde dice "questa è la lettura che hai visto", anche quando non c'è una striscia da contornare |
| D76 | Il "nessun dato" di una fonte è **nascosto** se la cella ha già un colore o un "nessuna reazione" | Due righe contraddittorie nella stessa cella ("arancione" e "nessun dato") non hanno senso: il dettaglio delle fonti sta nel popover |
| D77 | Una colonna **non si sposta** finché l'osservazione non è completa | Aggiungere un test vuoto non deve riordinare la tabella sotto gli occhi di chi sta leggendo |

| D78 | Nelle osservazioni c'è **sempre una riga incompleta**, non un tasto "aggiungi" | Il posto dove scrivere il prossimo test è sempre lo stesso: quando la riga è completa ne compare un'altra, e se hai usato tutti i reagenti non compare niente |
| D79 | **Un test per reagente**: i selettori offrono solo i reagenti non ancora usati | Non ha senso fare due test con lo stesso reagente: la maschera di bit ne prevede uno per osservazione, e la duplicazione confonderebbe l'ordinamento |
| D80 | La riga incompleta **non si cancella** e non sposta le colonne | È un segnaposto, non un dato: cancellarla non avrebbe senso e spostare le colonne sotto gli occhi di chi legge è disorientante |

| D81 | La riga **in corso non occupa un reagente**: i selettori delle osservazioni complete offrono anche il suo, e se una completa lo prende la riga in corso si sposta sul primo libero | Il reagente della riga in corso è una proposta, non un'assegnazione: bloccarlo rendeva impossibile correggere un test (spostare Ehrlich's su Folin's quando Folin's era già suggerito) |

| D82 | La riga in corso prende il **primo reagente libero in ordine alfabetico** | Niente preferenze nascoste: la lista delle osservazioni è prevedibile |
| D83 | La barra dei filtri **sparisce**: restano il contatore e "mostra tutte" accanto | "Reagente" e "tipo" erano ridondanti (la tabella ha già una colonna per reagente); la ricerca non serviva a un utente che legge per test, non per elenco |
| D84 | Il pannello di sicurezza parla dei **reagenti che hai testato**, non di un reagente scelto | Il filtro del reagente non c'è più: l'unico riferimento sensato sono i test che hai fatto |

| D85 | La casella "Mostra tutte" **non cambia etichetta** quando la spunti | Una casella che si rinomina da sola è un interruttore travestito: il contatore accanto dice già quanti elementi ci sono (59 → 397) |

| D86 | Le evidenziazioni (rosso, giallo) valgono **solo per i reagenti che hai testato** | Il rosso compariva anche nelle colonne che non avevi testato: senza un tuo test su quel reagente non c'è nessuna contraddizione da segnalare |

| D87 | La pagina **parte scura** e passa al tema scelto (o a quello di sistema) prima del primo disegno | Un lampo bianco è più fastidioso di uno scuro: il tema giusto viene applicato da uno scriptino nella testa del documento, prima che il browser disegni |
| D88 | Il tema scelto viene **ricordato** (localStorage) | Al ricaricamento la pagina torna come l'ha lasciata, non come è impostata la macchina |
| D89 | Il piè di pagina diventa un **accordion** (FAQ), chiuso per default | Sei paragrafi lunghi costringevano a scorrere per arrivare alla tabella; ora c'è solo quello che serve |
| D90 | Le **licenze restano aperte** | L'attribuzione (CC BY-SA di Wikipedia, copyright dei chart) non dovrebbe stare dietro un clic |
| D91 | In stampa gli accordion sono **tutti aperti** | Le fonti e le licenze devono finire sulla pagina stampata |
| D92 | Gli accordion stanno **esplosi nella pagina**, non dentro una card | Un accordion dentro una card ha due bordi e due livelli di raccolta: meglio una serie di sezioni una dopo l'altra |

| D93 | Le tabelle hanno **una sola scrollbar orizzontale**, sempre visibile in fondo | Due scrollbar native (una per gruppo) e una terza esterna sono troppe: quella esterna le governa entrambe, le native restano ma sono nascoste |
| D94 | La scrollbar esterna è **fissa al fondo della finestra** e sparisce quando le tabelle escono | "Sticky" non funziona per un elemento in fondo a un contenitore alto: verrebbe spinto solo quando lo raggiungi |
| D95 | La scrollbar esterna è **raggiungibile da tastiera** (role=scrollbar con valori ARIA) | Le scrollbar native nascoste non si raggiungono: senza questa, da tastiera non si potrebbe scorrere la tabella in orizzontale |
| D96 | **Trascinando con il mouse** dentro la tabella si scorre in verticale e in orizzontale | Come su uno schermo touch, ma solo col mouse: con il dito il gesto nativo va lasciato stare |

| D97 | La scrollbar esterna è **disegnata a mano** (traccia e cursore), non è quella del browser | Firefox nasconde le scrollbar native e la loro dimensione non è controllabile; disegnarla rende identico il comportamento ovunque |
| D98 | Il cursore della barra viaggia **solo sulla parte che corrisponde all'area scorrevole**, cioè a destra della colonna "Sostanza" | La colonna è fissa e non scorre: un cursore che passa sotto sembra puntare al posto sbagliato |
| D99 | Il drag della tabella usa la **cattura del puntatore** | Il drag prosegue anche se il puntatore esce dalla tabella o dalla finestra, e il rilascio fuori viene registrato |

| D100 | Il drag della tabella calcola la nuova posizione **dalla posizione iniziale**, non sommando gli spostamenti | Sommare faceva accelerare lo scroll: dopo 150px di puntatore la tabella era scorsa di 150px al primo passo e poi sempre più |
| D101 | Il drag del cursore della scrollbar **non avvia anche il drag della tabella | Il cursore è dentro l'area delle tabelle: senza questo filtro i due gestori si litigavano e la tabella andava nel verso opposto |
| D102 | La scrollbar **si ferma alla fine delle tabelle**, risalendo con loro | Incolla al fondo della finestra mentre le tabelle continuano, e le accompagna all'indietro quando finiscono |
| D103 | Il parametro di versione di CSS e script sale a ogni cambio grosso | Senza, il browser serve il file dalla cache e le correzioni non arrivano |

| D104 | Il cursore della scrollbar viaggia su **tutta la traccia**, sopra tutte le colonne | Scostarlo per non finire sotto la colonna "Sostanza" lo faceva sembrare un cursore troncato: la traccia deve corrispondere alla tabella intera |
| D105 | L'area delle tabelle **riserva 16px in fondo** | Sono lo spazio della barra: così l'ultima riga della tabella non finisce sotto di lei |

| D106 | La barra ha **z-index 20**, spigolata, e si **attacca all'ultima riga** quando le tabelle finiscono | La colonna "Sostanza" è fissa con z-index 8 e copriva la barra; e un galleggiante con i bordi tondi sembrava una pillola, non una barra |

| D107 | La traccia della scrollbar si misura sulle **tabelle**, non sulla barra | La barra è `fixed` e vuota: quando non si vede ha larghezza zero, e il cursore veniva calcolato su una traccia di zero pixel (36px, il minimo) |

| D108 | Il titolo del gruppo **non esiste** quando è vuoto | Con una sola sezione (nessuna osservazione) era una barra vuota sopra le colonne |
| D109 | La barra galleggiante è **a filo del fondo della finestra** (bottom: 0) e attaccata all'ultima riga quando le tabelle finiscono | I 4px di margine facevano una fessura fra la tabella e la barra |
| D110 | Quando è attaccata alla tabella la barra **non proietta ombra** | L'ombra verso l'alto si leggeva come altri 2-3px di fessura fra l'ultima riga e la barra |
| D111 | La striscia **riempie esattamente il padding** della tabella (una variabile sola per le due misure) | Così sta fra l'ultima riga e il bordo della card, senza fessure né sovrapposizioni: la sua altezza è il padding, punto |
| D112 | I due numeri della striscia sono **due variabili CSS** (`--hbar-h`, `--hbar-gap`) | Erano due misure che io facevo coincidere a fatica con la formula del `bottom`: ogni ritocco ne spostava un'altra, e i numeri cambiavano a ogni versione |
| D113 | Il fondo della striscia è **il più in alto fra il fondo della finestra e il fondo della tabella** (`max(0, vh - r.bottom)`) | La formula precedente (che sottraeva padding e altezza) la staccava dal bordo della tabella 22px prima: in quella fascia restava incollata al fondo della finestra e lasciava un gap |

| D114 | La striscia è **2px più alta del padding** della tabella: copre il bordo dell'ultima riga | Così fra le righe e la traccia c'è una riga sola, non due: il bordo della striscia copre quello della riga |
| D115 | Il cursore ha lo ** stesso viaggio** nel drag e nel posizionamento | Con due misure diverse il cursore non arrivava in fondo: la tabella si fermava a 1494 su 1512 |
| D116 | La **firma della build** in fondo alla pagina | Senza, due persone che guardano la stessa pagina non sanno se stanno vedendo lo stesso codice: ogni correzione sembrava non arrivare |
| D117 | Il viaggio del cursore è calcolato sulla **larghezza interna** della striscia (senza i bordi), meno il cursore e un margine di 1px per lato | Con i bordi contati a mano il cursore non sporgeva, ma la tabella si fermava a 1494 su 1512; così va in fondo e resta dentro con un pixel d'aria |
| D118 | La posizione del cursore **non viene arrotondata** | Un `Math.round` faceva sbordare il cursore di mezzo pixel e lo faceva saltare quando la tabella veniva spostata da un altro punto |
| D119 | La colonna "Sostanza" ha **due righe** come le altre: nome e totale | Non serve alla fessura, ma rende la testata uniforme: ogni colonna ha nome e numero |
| D120 | Fra la testa e la tabella c'è **un solo bordo** (quello della testa) | Ce ne erano due, uno dietro l'altro: il bordo inferiore della testa (2px) e quello superiore della tabella (2px) facevano una banda grigia di 4px |
| D121 | Anche "nessuna reazione" porta l'etichetta della **proporzione** | Una cella con un colore e una cella con "nessuna reazione" devono avere la stessa struttura: la lettura è a una proporzione, sempre. L'etichetta non si ripete se la cella l'ha già mostrata |
| D122 | Il link alle fonti è **testo cliccabile** (niente margini, bordi o padding) | Il testo è piccolo e leggero; l'area cliccabile resta quella minima del WCAG grazie a uno pseudo-elemento che la ingrandisce senza occupare spazio |
| D123 | Una lettura **senza colore** ha la stessa forma di una con il colore: una barra vuota (trasparente, bordo tratteggiato) e la didascalia sotto | Le descrizioni delle celle si allineavano solo per caso: con la barra vuota ogni lettura ha la stessa struttura |
| D124 | Il badge "fonti in disaccordo" sta **nel suo blocco**, non nell'angolo del pannello | Era posizionato in assoluto rispetto al pannello: finiva sopra il ✕ di chiusura |
| D125 | I "nessun dato" **non sono in corsivo** e sono più tenui | Il corsivo dava più peso a ciò che manca che a ciò che è stato letto: la gerarchia era capovolta |
| D126 | Il badge "fonti in disaccordo" **non sta nell'angolo** ma sotto il titolo | Le righe non mostrano il disaccordo: una fonte che documenta un colore mentre le altre non hanno nulla non è un disaccordo fra fonti, è solo che una sola documenta. Il badge porta un'informazione che le righe non danno |
| D127 | La didascalia del colore e il testo di stato hanno **la stessa dimensione** | Sono entrambe letture: una cella non deve sembrare diversa a seconda di quello che dice |
| D128 | Il link alle fonti sta **in flusso**, in un piede di cella | In assoluto poteva finire sopra l'ultima lettura; in flusso occupa una riga e non si sovrappone |
| D129 | Il pannello di dettaglio ha **una scheda per reagente** | Undici blocchi lunghi erano illeggibili: con le schede si guarda un reagente alla volta |
| D130 | Nel dettaglio ogni fonte è elencata **anche quando non c'è dato** | Le righe vuote dicono che la fonte non documenta quella sostanza, che è diverso dal non sapere nulla |
| D131 | Il badge del popover sta **sulla riga del titolo**, a destra e sulla stessa baseline | Nell'angolo era staccato dal titolo; era il badge "fonti in disaccordo" della cella, non della tendina |
| D132 | Il testo del badge **va a capo** invece di sbordare | Il badge è un elemento della griglia: la colonna gli dava la larghezza e "fonti in disaccordo" usciva fuori |
| D133 | La cella è una **colonna**: le letture e sotto il link alle fonti | In fila il link finiva accanto alle letture, non sotto |
| D134 | Il link alle fonti sta **sempre in fondo alla cella** | La cella prende l'altezza della riga: il link è a 5px dal bordo in tutte le celle, con una o sei letture |
| D135 | Nel pannello della sostanza il badge sta **in basso a destra della card**, fuori dalla griglia delle letture | Impilato alla griglia ne eredita la larghezza della colonna e il testo sborda; a destra in basso prende il suo spazio e si capisce |
| D136 | La cella resta una **table-cell**: `display: flex` su una td rompe la tabella | Con la td flex le colonne non si allineavano più: la tabella smetteva di essere una tabella |
| D137 | Il link alle fonti è **ancorato alla cella** e le letture gli lasciano il posto | In absolute non può sovrapporsi all'ultima lettura (le letture hanno il padding sotto), ed è sempre a 3px dal fondo in ogni cella |
| D138 | Chiudere il pannello della sostanza **chiude anche il backdrop** e sblocca lo scroll | Il pannello è un overlay: restare indietro il fondo e lo scroll bloccato non aveva senso |

| D139 | C'è un **bundler** che raccoglie la pagina in un file HTML solo | La pagina non ha dipendenze esterne: basta sciogliere il foglio di stile e i quattro script, e compattare il dataset per avere una pagina da aprire con un doppio clic e da mandare per email |
| D140 | Nel file unico il CSS e il JS sono **minimizzati**, con `--no-minify` per leggerli | Il dataset è il 90% del peso (780 kB compressi); il resto scende da 120 a 75 kB. Il minificatore del CSS fa caso alle stringhe (`content: "›"`) e il JS usa rjsmin, se c'è |
| D141 | Su un **touch** la scrollbar esterna sparisce e torna quella nativa | La barra esterna è fissa in fondo allo schermo: si mangia il palmo e ruba lo swipe verticale. Su un telefono la nativa è l'unica indicazione che la tabella continua a destra, e non occupa spazio |
| D142 | La scrollbar esterna sparisce solo dove **non c'è hover** (`hover: none and pointer: coarse`) | Su un computer con schermo touch il puntatore principale è comunque il mouse: la barra deve restare |
| D143 | Sul touch **scorre il browser**, non noi: il drag è solo del mouse | Il browser ha l'inerzia e blocca l'asse del gesto (uno swipe, una direzione), come su ogni schermo touch. E quando parte il pan manda un `pointercancel`: un drag fatto da noi morirebbe a metà, e lo scroll orizzontale si fermerebbe appena comincia il verticale |
| D144 | Una "nessuna reazione" che **corrisponde** ha il **quadratino** contornato di verde tratteggiato e il testo scritto come i colori | Il contorno della cella intera era una gabbia: il segnale va sulla lettura, e la scritta deve avere lo stesso peso di un colore |
| D145 | La tabella **non scrolla mai in verticale** (`overflow-y: hidden`) | Aveva sei pixel di overflow proprio: il browser se li mangiava e sui trackpad, dove ogni scorrimento è piccolo, la pagina restava ferma finche' non si esaurivano |
| D146 | Ricostruendo la tabella si **conserva lo scorrimento laterale** | Al ridimensionamento la tabella veniva ricostruita da zero e ripartiva da sinistra: si perdeva il punto in cui si stava leggendo |
| D147 | Il ridimensionamento **aspetta che si fermi** (140 ms) | La tabella viene ricostruita a ogni evento: durante il trascinamento della finestra sarebbero state decine di ricostruzioni |
| D148 | L'hover **deriva dal colore della cella**, ma di un passo appena: la cella che corrisponde va dal verde tenue a un verde poco più fondo, il conflitto dal rosa tenue a un rosa più fondo, l'avviso lo stesso; il testo **non cambia inchiostro** | L'hover dipingeva l'intera riga di un colore solo e le celle che avevano un loro stato (corrispondenza, conflitto, avviso) li perdevano. Ma il colore pieno urlava, e il contorno verde della lettura che corrisponde spariva dentro il verde |
| D149 | I passi intermedi sono **token dedicati** (`--accent-mid`, `--conflict-mid`, `--warn-mid`), scelti perché il testo dentro la cella resti leggibile (contrasto misurato ≥ 4.5:1) e il contorno della lettura resti visibile | Il passo non si sceglie a occhio: il testo della cella (verde su verde, grigio su ambra) deve continuare a leggersi, e il verde del contorno deve staccare dal fondo |
| D150 | La colonna del nome **cambia anche lei** all'hover, con lo stesso passo delle celle che corrispondono | Le celle cambiavano colore e il nome no: la riga sembrava metà e metà |
| D151 | Le regole dell'hover sulla cella valgono per **qualsiasi riga**, non solo per quelle con corrispondenze | Un conflitto può stare in una riga senza corrispondenze: legato alla classe della riga, il rosso spariva |
| D152 | Il contorno della lettura che corrisponde è **attaccato alla striscia** (via `outline-offset`) | Con un pixel di scarto il contorno sembrava una cornice attorno a un'altra cornice: il segnale che dice "questa è la lettura che hai visto" si staccava dalla striscia che incornicia |
| D153 | I tasti del selettore (elimina, annulla, conferma) restano **in fondo alla tendina, appiccicati** | La tendina scorre e i tasti erano in coda: per confermare una reazione bisognava arrivare in fondo a una lista di colori, e il tasto era lontano da dove si sta guardando |
| D154 | Il "+" che aggiunge una fase di reazione **apre subito il selettore** della fase nuova | Aggiungere la fase e poi andare a cercare il suo pulsante vuoto era un doppio passaggio: il punto del "+" è scegliere il colore subito |
| D155 | La tendina di scelta del colore **non viene mai tagliata**: mantiene le sue 340px e scivola lungo il pulsante quanto basta per restare nella finestra; solo se la finestra è più stretta si stringe a quello che c'è | Prima, quando lo spazio non bastava da nessuna parte, la tendina veniva ristretta sul lato più largo ma restava ancorata a destra: si usciva dalla finestra. La misura che si vuole vale più dell'allineamento al pulsante |
| D156 | L'overlay viene mostrato **prima** di posizionare la tendina | L'overlay toglie la barra di scorrimento e la pagina si sposta di qualche pixel: la tendina era stata posizionata su una misura che subito dopo non era più quella giusta |
| D157 | La riga in progresso **segue i reagenti liberi**: quando si cancella un'osservazione, il reagente che si libera torna a lei | Il reagente della riga incompleta era offerto automaticamente (il primo libero in ordine alfabetico), ma l'offerta non veniva ricalcolata: dopo una cancellazione la riga restava su un reagente vecchio invece di prendere quello appena liberato. Se il lettore ha scelto il reagente a mano, la riga non si muove |
| D158 | Le osservazioni stanno **nel frammento dell'indirizzo**, in un formato leggibile: `#obs=marquis:orange.deep@high;robadope:none&lang=en` | Il link deve poter portare con sé i test fatti senza salvare niente sulla pagina (D47). Il formato è leggibile perché un link si possa anche correggere a mano; reagente, tinta, intensità, proporzione e fasi sono tutti dentro |
| D159 | Nel link vanno **solo le osservazioni complete**: una riga ancora in corso non lo riguarda | Cambiare il reagente della riga incompleta non deve cambiare il link: è una scelta in corso, non un test da condividere. E se non resta nessuna osservazione completa, il link è vuoto |
| D160 | L'ordine delle corrispondenze è **per numero di test soddisfatti**, poi per maschera, poi per nome | L'ordine era per maschera di bit, e il test fatto per primo pesava di più: con tre test, una sostanza che ne soddisfaceva due finiva sotto a una che ne soddisfaceva uno solo. Il numero di corrispondenze è la forza della prova |
| D161 | La tabella ha **tre sezioni**: «Corrispondenze totali», «Corrispondenze parziali», «Altre sostanze» | Il riordinamento metteva in cima le sostanze che corrispondono a più test, ma non diceva quali corrispondono a *tutti* i test: sono quelle che contano. La sezione delle parziali c'è solo se non è vuota (una sezione vuota è rumore); con un solo test la prima sezione si chiama «Corrispondenze» come prima |
| D162 | Il pannello delle osservazioni propone **il test successivo**: per ogni reagente non ancora usato, quanti dei candidati restano (in media e nel caso peggiore), in ordine di quanto restringe | I candidati sono le sostanze che corrispondono a almeno un test fatto. Per ogni reagente le letture (alla **proporzione consigliata**: il test successimo è fatto con una dose nuova) raggruppano i candidati per la risposta che danno: se una risposta arriva, resta solo quel gruppo. Restano anche i candidati di cui il reagente non dice niente. L'ordine è sulla media, il numero è «media–peggiore» |
| D163 | I reagenti **già usati** non sono proposti e non contano | La reazione sarebbe la stessa di quella già osservata: non può distinguere niente di nuovo |
| D164 | La lista dei test proposti compare **solo se qualcosa può ancora essere distinto**, e i reagenti che non distinguono niente stanno in fondo, in grigio, senza il "+" | Una lista che non serve è rumore; ma nasconderla del tutto farebbe pensare che quei reagenti non siano stati tenuti in considerazione |
| D165 | Il numero è scritto **per esteso** ("1 candidato", "1-2 candidati") e il pulsante è un **pulsante con la scritta** ("Aggiungi alle osservazioni") | Il "+" era minuscolo e anonimo, e il numero da solo ("1-2") non diceva di cosa. Su schermo stretto il pulsante prende la scritta breve ("Aggiungi", la versione lunga resta nel tooltip) e la riga va su due righe: nome e numero sopra, tempo e pulsante sotto |
| D166 | La larghezza delle colonne si **calcola da ciò che una cella deve contenere** (la striscia, la didascalia, l'etichetta della proporzione), non dalle righe che in quel momento sono a schermo | Le larghezze venivano misurate sulla prima riga della prima tabella — quella delle corrispondenze, che ha poche righe: una colonna restava stretta (68px dove la striscia da 84px non ci stava) e il contenuto sbordava dalla cella. Le righe cambiano a ogni osservazione: la larghezza non può dipenderne |
| D167 | L'etichetta della proporzione **non va a capo** e la colonna le dà spazio | "proporzione consigliata" è lunga: se la cella è stretta va su due righe e sembra un'altra lettura. La larghezza della colonna tiene conto anche dell'etichetta più lunga, misurata con il carattere del tavolo |
| D168 | Le fasi di una lettura vanno **una per riga**, con la freccia **in testa alla riga** | "blu scuro → blu → blu scuro → viola scuro" in una cella stretta si spezzava nel mezzo, e una riga che si spezza così sembra un'altra lettura. Ora la sequenza si legge in giù, e ogni fase è per sé |
| D169 | Nella cella le proporzioni in **mg/mL non si ripetono**: l'etichetta dice già "proporzione consigliata/alta/bassa" | Erano due modi di dire la stessa cosa nella stessa didascalia. I valori in mg/mL restano nel pannello di dettaglio, dove la quantità non è scritta altrove |
| D170 | Nello scorrimento laterale **non si misura niente**: la larghezza della colonna bloccata, quella del binario e dei bordi sono noti dal layout | Ogni evento di scroll forzava due layout (`getBoundingClientRect` sull'area e sulla colonna bloccata) e tre letture di stile: la misura in mezzo all'animazione fa andare il movimento a scatti. Con le osservazioni le tabelle sono tre e il lavoro si triplica |
| D171 | Il lavoro dello scroll viene fatto **una volta per frame**, nel frame | Lo scroll di un trackpad arriva a raffica: farlo nell'evento lo mette in mezzo all'animazione |
| D172 | Gli eventi di scroll **provocati dalla sincronizzazione** degli altri scroller si riconoscono dal valore e si ignorano | Presi per uno scroll del lettore, rimettevano le tabelle al punto di prima: lo scroll non faceva nulla |
| D173 | I **candidati** del pannello sono le sostanze che soddisfano **almeno due terzi dei test fatti** (arrotondati per eccesso: 2 su 3, 3 su 4) | Erano le sostanze che ne corrispondevano almeno uno: con quattro test il pool arrivava a 106 sostanze e il consiglio diceva «Froehde, 82-86 candidati» — 81 delle quali nessuna fonte documenta con Froehde. La soglia nuova ha un vantaggio: **il pool non può mai crescere** quando si aggiunge un test, quindi il consiglio non impazzisce |
| D174 | I candidati che restano dopo un test si contano **per colore**, non per traiettoria | Chi guarda il test vede **un colore**, e un colore può essere la risposta di più traiettorie documentate ("giallo → rosso" e "rosso" finiscono entrambe in rosso). Contando per traiettoria il pannello prometteva «Mandelin 1-1» mentre in campo il grigio (che vale per 7 degli 8 candidati) ne lasciava 7 |
| D175 | La **media** è l'attesa sul colore che esce: ogni candidato è equiprobabile e il colore è uno di quelli documentati per lui, con la stessa probabilità | Il numero «media – caso peggiore» resta, ma la media è una vera attesa (prima la somma delle probabilità non era normalizzata) |
| D176 | Con **un solo candidato** il pannello lo dice e propone i **test che lo confermerebbero**, con i colori attesi | Non c'è niente da distinguere, ma un altro test può confermare o smentire: «Froehde: nessuna reazione → confermata» |
| D177 | Con **nessun candidato** il pannello dice che i colori descritti non possono stare insieme e invites to rimuovere un test | Il vuoto è un'informazione, non un pannello che sparisce |
| D178 | Il riepilogo e la nota delle **corrispondenze parziali** usano lo stesso conteggio dei candidati | Dicevano «99 corrispondenze» mentre il pannello diceva «3 sostanze compatibili»: due numeri per la stessa cosa |
| D179 | A parità di merito, il **test più veloce** viene prima (la durata è letta dalla frase nei dati) | Simon's è istantanea, Ehrlich's e Hofmann cinque minuti: se due test distinguono uguale, si sceglie quello che si fa prima |
| D180 | `evaluate()` restituisce il **numero di conflitti**: la riga «N sostanze sono in conflitto» sotto «Nessuna corrispondenza totale» non era mai comparsa | Il contatore era sempre zero: il campo non esisteva |
| D181 | Le letture attese si scrivono con la **freccia fra le fasi** di una stessa lettura e la **virgola fra letture diverse** | «bianco → rosso chiaro → arancione chiaro» è una traiettoria: le fasi dello stesso reazione. «arancione chiaro, arancione» sono due fonti che non sono d'accordo. Scrivere tutto con la virgola non diceva nulla, e la freccia da sola nascondeva il disaccordo |
| D182 | Le colonne del pannello hanno **larghezza fissa** (nome 88px, numeri 148px, letture 300px) | Con la larghezza flessibile ogni riga spostava la successiva: il tempo di una riga con un testo lungo finiva sotto il testo della riga sopra. Su schermo stretto (≤640px) la riga diventa a due righe: nome e tempo sopra, letture e pulsante sotto |
| D183 | Il pannello «il prossimo test» è una **fila di card** che scorre di lato, non una lista di righe | Una lista lunga mette il consiglio migliore in cima e gli altri sotto, lontani dagli occhi: con dieci reagenti la lista è una parete. Le card si leggono come una sequenza: la prima è quella da fare, le altre si vedono scorrendo. La prima card è in evidenza (bordo e sfondo colorati, con la scritta «consigliato») |
| D184 | La card del caso **un solo candidato** mostra le **strisce** del colore, come le celle della tabella, e non il solo testo | Il testo dice «bianco → rosso chiaro»: la striscia dice *come si arriva al rosso*, che è quello che si vede in mano. Le letture diverse restano separate dalla virgola nella didascalia |
| D185 | Le card si possono **trascinare col mouse** come le tabelle | Il trascinamento era legato alle tabelle: la stessa mano che scorre le tabelle scorre anche le card |
| D186 | La fila delle card ha la **scrollbar nativa sottile**, colorata con `--line-strong` | Le tabelle hanno la barra disegnata a mano (sono sotto, in fondo alla finestra): una seconda barra disegnata per le card sarebbe un pezzo in più. La card tagliata sul bordo è già il segnale che la fila prosegue |
| D187 | La fila delle card **non aggancia** le card a punti fissi (`scroll-snap`) | Lo snap agganciava la card al punto più vicino: il trascinamento finiva con uno scatto indietro, e il gesto sembrava rotto |
| D188 | La card migliore si distingue **solo con il colore** (bordo e sfondo), senza la scritta «consigliato» | La scritta stava sopra il titolo e faceva disallineare il titolo della prima card con quello delle altre |
| D189 | Il numero dei candidati è preceduto dall'etichetta grigia **«Riduce a:»** | Il numero da solo («3-5 candidati») non diceva che cosa fosse: «Riduce a» dice che il test stringe le possibilità. L'etichetta è grigia, il numero no |
| D190 | Vicino al tempo c'è **un orologino** (SVG inline, 11px, monocromo) | «30 s» da solo è una parola in un angolo: l'orologino dice "tempo" a colpo d'occhio e non ruba spazio al nome del reagente. È decorativo (`aria-hidden`): il testo dice già tutto |
| D191 | Il trascinamento col mouse **non parte quando il puntatore è sulla scrollbar** | In Firefox la scrollbar è disegnata sopra il contenuto: il clic su di lei arrivava all'elemento, partiva il trascinamento (che tirava il contenuto dalla parte opposta) e il `setPointerCapture` rubava il clic alla scrollbar. Ora la fascia della scrollbar è riconosciuta e lasciata al browser: con la scrollbar classica la fascia è esatta, con quella sovrapposta si indovinano dodici pixel |
| D192 | Le card che **non distinguono niente** restano mutate (bordo tratteggiato, nome e numero in grigio) ma **hanno il bottone**: si possono aggiungere alle osservazioni | Un reagente che non restringe i candidati può essere comunque quello che hai sù: registrarne il risultato dice qualcosa. E una card muta senza bottone è un buco: sembra che il test non si possa fare. L'opacità della card intera è stata tolta: rendeva illeggibile il bottone |
| D193 | Le **osservazioni** diventano schede della stessa grammatica delle card, in una griglia che va a capo (non scroll laterale) | La pagina aveva due linguaggi: il form delle osservazioni e le tile del pannello. Le osservazioni erano già caselle con bordo e raggio, ma righe a tutta larghezza: con quattro test la pagina era una parete. Da sole in griglia (280px) vanno a capo e il lettore vede tutto: sono poche e sono l'interazione principale, a differenza delle card che sono un elenco lungo e vogliono lo scroll |
| D194 | La select della proporzione ha l'**etichetta scritta piccola** ("Proporzione dose/reagente") **sopra** e dentro solo "bassa / consigliata / alta" | "proporzione consigliata" dentro la select la faceva larga 181px — la stringa più lunga della pagina. L'etichetta fuori, in carattere piccolo, dice che cos'è il campo; la select dice il valore. Sopra, non accanto: accanto la select sembrava un campo senza nome |
| D195 | La scheda dell'osservazione mostra anche il **tempo del test** con l'orologino, come le card | È la stessa grammatica: reagente in alto a sinistra, tempo e cancellazione in alto a destra. Il tempo serve anche a chi rilegge a posteriori i test che ha fatto |
| D196 | Anche la **reazione** ha la sua etichetta ("Reazione"), come la proporzione | La scheda ha due campi, e senza etichetta la riga dei colori sembrava un'altra cosa senza nome |
| D197 | La fase **senza colore** è il bottone "+" tratteggiato, non la scritta lunga "+ aggiungi reazione"; e il bottone che aggiunge un'altra fase sparisce quando c'è già una fase in attesa | La scritta lunga era un tasto diverso dal "+" che si vede accanto alle chip: due modi per la stessa cosa, con forme diverse. Ora un solo "+", tratteggiato, e il suo compito è chiaro: è quello della fase che aspetta il colore |
| D198 | Il "+" è **alto come le chip** con il colore (34px) | Era 26px: la riga della reazione non si allineava, e il "+" sembrava un pulsante sciolto in mezzo ai campi |
| D199 | La testa della scheda è una **griglia a tre colonne** (reagente, tempo, cancellazione), le righe si **allineano in alto** (`align-items: stretch`) e il bottone "✕" **non ha altezza propria** | La testa era alta 34px con il "✕" e 30px senza (la scheda in corso non ce l'ha): tutto il resto scivolava di qualche pixel. Il primo tentativo fissava l'altezza del bottone a 30px — misurati su Chrome: in Firefox la select è più bassa, il bottone faceva crescere la testa e lo scivolamento tornava. Ora la riga prende l'altezza della select (l'unico pezzo in ogni scheda) e il bottone si stira a quella altezza: nessun numero tarato su un browser |
| D200 | La select della proporzione e i pulsanti della reazione non hanno altezze fisse | Le altezze fisse sono state la causa del problema: un numero giusto per un browser sbagliato per gli altri. Le misure vere (chip 22px, padding) sono le stesse ovunque, quindi si lascia calcolare |
| D201 | Le fonti nuove sono **NIJ 0604.01, NIST CADS e Chang et al. 2025**, oltre a PsychonautWiki | Sono le uniche trovate con una licenza che ne permette l'uso (governo USA, NIST, CC BY 4.0) e con colori per sostanze non psicoattive: zucchero, paracetamolo, procaina, mannitolo… |
| D202 | Ogni fonte ha il suo **script di estrazione**, citato con la data accanto alla fonte | La licenza NIST chiede di dire che cosa è stato cambiato e quando: lo script è la descrizione esatta della conversione dei colori. Vale anche per PsychonautWiki |
| D203 | Un nome composto ("Pink-orange", "reddish brown") diventa **più letture**, una per famiglia | Chi ha visto rosa e chi ha visto arancione devono trovare tutti e due la sostanza: è la regola già usata per il testo di PsychonautWiki |
| D204 | Di CADS entrano **solo i campioni puri**, e le miscele non danno letture dedotte | Il colore di una miscela non si attribuisce a un componente, e nemmeno la sua assenza: CADS 030 contiene saccarosio e non reagisce al Marquis, il saccarosio puro sì |
| D205 | Il **cobalto tiocianato** semplice resta fuori, come gli altri reagenti forensi del NIJ | Non è né lo Scott (acidifica ed estrae) né il Morris (basifica): da solo dà blu con quasi tutte le ammine, e nelle loro colonne sembrerebbe un disaccordo fra le fonti. Il p-DMAB del NIJ entra come Ehrlich, che è lo stesso reattivo |
| D206 | Nelle celle **positive** di PsychonautWiki i campioni restano la spina dorsale, e il **testo li integra** dove nomina qualcosa che nessun campione registra: un'alternativa ("violet / violet-blue" senza il blu) o una tappa con ">" in una fase senza campioni | Un'alternativa senza campione diventava un percorso vuoto, cioè una "nessuna reazione" falsa (circa 40 letture). Il testo non aggiunge niente per la famiglia mancante di un composto ("reddish brown", "red orange") né quando la cella ha un campione che il testo non nomina: quello è la tappa, descritta in altro modo ("rusty brown" col campione rosso) |
| D207 | `isPositive` di PsychonautWiki dice se l'esito **è un indizio** della sostanza, non se il colore cambia: un esito negativo che nomina un colore dà **quel colore** | È la definizione dell'API. "Dark brown" dell'anfetamina col Simon's è quello che si vede: come "nessuna reazione" l'avrebbe esclusa a chi vede marrone. "No instant reaction" è nessun dato (il NIJ dà all'LSD il verde oliva col Marquis); "brown or clear", "possible violet spots", "no color change > light yellow" danno anche nessuna reazione |
| D208 | I reagenti che cercano una classe hanno il **colore atteso** (`target`): Simon's blu, Robadope rosa o rosso, Scott blu, Ehrlich viola, Hofmann blu, viola o rosso, Zimmermann viola o rosso, 4-AP rosa o blu | Basta confrontarlo con i colori registrati: un campo per lettura ("absent") poteva contraddirli. Il Morris resta un'impronta (cocaina e ketamina hanno colori diversi); Gallic e Folin non hanno un colore atteso documentato |
| D209 | Il colore atteso conta solo se è **completo**: presente e senza una forma (niente macchie, niente precipitato) | Le macchie blu dei catinoni con lo Scott non sono il blu della cocaina, e la fonte le marca come esito negativo |
| D210 | La famiglia `black` diventa **`gray`**, una scala: grigio, grigio scuro, nero | `black.light` era un grigio chiaro e `black.standard` un grigio scuro chiamato "nero"; il nero vero delle fonti è `gray.dark`. "Black" va al nero, "grey" al grigio, "greyish black" e "dark grey" al grigio scuro |
| D211 | "Not dissolving" è un campo della lettura (`dissolves: false`), mostrato con gli altri dettagli | È un'osservazione, come le bolle o le macchie |
| D212 | Il **confronto col colore atteso** si fa per fonte: se l'hai visto, corrispondono solo le letture che lo hanno; se non l'hai visto, una lettura dello stesso colore corrisponde come sempre, e un colore diverso è una corrispondenza **parziale** solo se la fonte non documenta il colore atteso per quella sostanza | Chi vede marrone col Simon's resta compatibile con l'LSD ("no blue"), con un avviso sul reagente vecchio, ma non con la MDMA: CADS la documenta "Blue-Purple", e chi vede viola la trova comunque. Per fonte, perché le fonti possono essere in disaccordo; senza toccare il modello, perché le tappe servono al gradiente |
| D213 | Le sostanze stanno in un **vocabolario** (`data/substances.json`): id, nome, tipo, voce di PsychonautWiki, classe, alias. Le fonti danno solo reazioni legate a un id | Le corrispondenze dei nomi erano sparse negli estrattori, e gli alias di PsychonautWiki presi così com'erano mettevano "Doxepin HCl" sotto DOx e "tea" sotto la caffeina |
| D214 | Gli **alias possono essere ambigui**, i nomi delle fonti no: un nome ambiguo o sconosciuto ferma l'estrazione, e si risolve in `data/name-conflicts.json` (coppia fonte-nome) o aggiungendo un alias. Gli alias nuovi di una fonte sono un avviso | Gli alias servono alla ricerca, e i nomi di strada sono condivisi ("speed"); una reazione invece non deve mai andare a una sostanza indovinata |
| D215 | Per PsychonautWiki conta il **nome del database dei reagenti**, non l'aggancio dell'API: la cocaina cloridrato ("Coca") e la cocaina base ("Cocaine (Crack)") sono due voci, la riga di DOx è la doxepina, quella di PCE è il PCEEA (DOx e PCE non hanno dati), Cannabis e THC sono una voce sola, "Cannabis (THC)", perché il campione è la pianta | L'API aggancia le voci alle sostanze del wiki per nome, e ne sbagliava quattro |
| D216 | Una **lettura ripetuta** in più osservazioni della stessa coppia compare una volta: `build_data.py` tiene la prima | La pagina non mostra le osservazioni, quindi due righe uguali non dicevano niente in più; si perde solo che la fonte ha visto il risultato due volte (2C-C col Liebermann, Pethidine col Froehde) |
| D217 | `colors` è una **lista di parti contemporanee**, ognuna una sequenza di tappe `{color?, shape?}`: "reddish with grey spots" è il liquido rosso più le macchie grigie; "purple ring / brown" è una parte sola, anello viola poi tutto marrone; "blue spots" col Morris sono solo le macchie blu, perché il liquido che resta del colore del reattivo non è una parte. Le forme sono tre: macchie (anche le particelle), anello (anche i bordi: la reazione comincia dove il solvente evapora prima), precipitato. Finché le osservazioni non dicono le forme, la pagina legge le parti una dopo l'altra, come prima | Un campo `details` a parte obbligava a decidere cosa è dettaglio e cosa no: le stesse macchie blu stavano in `colors` in una sostanza e nei dettagli in un'altra. La forma sta sulla tappa perché l'anello è l'inizio della reazione, non una parte che resta |
| D218 | Una **"/" di PsychonautWiki è una sequenza** quando la coppia ha una sola osservazione, i campioni registrano i colori nominati nell'ordine del testo e, se la barra è l'ultima tappa, il numero fra parentesi (la classe del colore finale, per reattivo) è del colore nominato per ultimo. Altrimenti è un'alternativa. Le eccezioni sono sovrascritture esplicite (`SLASH_OVERRIDES`), legate alla cella e al suo testo intero | Delle 115 celle con la barra, molte sono passaggi ("yellow / orange (89)" col Marquis: giallo poi arancione, classe finale arancione) e altre esiti diversi riassunti (25B-NBOMe col Mecke: un'osservazione verde, l'altra gialla). Il numero è la classe finale in 828 celle su 861. Con i campioni in ordine inverso (3-MMC col Liebermann) i dati si contraddicono e resta un'alternativa |
| D219 | Il colore atteso conta anche in un **anello**, non nelle macchie né nel precipitato (rivede D209) | L'anello è la reazione che comincia ai bordi e poi si estende: il blu del NEP col Simon's (CADS) e il viola dei catinoni con lo Zimmermann sono il colore atteso. Le macchie e il precipitato sono prodotto che non si scioglie, e la fonte marca le macchie blu dello Scott come esito negativo |
| D220 | Una tappa ha **sempre un colore**; dove il testo non lo dice, le letture si scrivono a mano (`READING_OVERRIDES`) | "Dark precipitation" (4-AcO-MET col Simon's) non nomina una tinta: precipitato grigio scuro o nero, come gli altri precipitati del Simon's |
| D221 | Un'osservazione è una **griglia di fasi**: una riga per fase, una colonna per ogni cosa vista, con la sua forma scelta quando si crea e scritta in cima: liquido (la reazione sciolta), macchie, precipitato, tutte ripetibili (due liquidi sono uno striato, più macchie possono venire da un taglio). Il liquido ha un centro e dei bordi, uguali al centro o di un altro colore: l'anello. La cella è una goccia tonda col colore e la forma; "nessuna reazione" solo nel liquido e solo se nessun altro liquido della fase ha un colore; "non ancora" prima che una cosa compaia; "uguale a prima" dopo; "sparisce" per macchie e precipitato che c'erano. Sotto l'ultima fase c'è la fase dopo, sbiadita e tutta "uguale a prima". Bolle e "non si scioglie" sono due spunte sempre visibili | Le tappe in fila con "poi" e "insieme" non dicevano a cosa si legasse la tappa dopo; la forma di ogni cella permetteva contraddizioni (due liquidi uniformi, "nessuna reazione" accanto a un colore). Con la forma sulla colonna le contraddizioni non si possono scrivere, e l'anello è il liquido che reagisce prima ai bordi, non una cosa in più |
| D222 | Nel confronto **l'aspetto conta in positivo**: lo stesso aspetto documentato rafforza la corrispondenza (a parità di esito viene prima, come le bolle e "non si scioglie" documentati); un colore visto nel liquido che la lettura ha solo in macchie o nel precipitato è parziale; un aspetto che la lettura non documenta è una nota, non un difetto; liquido e bordi sono la stessa reazione | Le fonti annotano di rado come si presenta il colore |
| D223 | Il **confronto è per parti**: ogni cosa vista si confronta con la parte della lettura che le somiglia di più; la lettura corrisponde se ne corrisponde almeno una. Una cosa vista che la lettura non spiega è una nota (un taglio, un'altra sostanza), salvo che nessun liquido visto sia spiegato: allora è parziale. Una parte della lettura che nessuno ha visto è una nota. I bordi colorati attorno a una goccia senza reazione sono l'inizio della sequenza del liquido (lo Zimmermann); attorno a un centro colorato sono una parte a sé (2C-E). Le tonalità della stessa tinta non sono fasi mancate | Mettere le parti in fila trasformava il contemporaneo in successivo ("rosso, poi grigio" per il rosso con macchie grigie) e faceva di un taglio una fase che nessuno documenta |
| D224 | Il **reagente può essere in cristalli**: Marquis, Mecke, Froehde, Liebermann, Ehrlich, Hofmann e Morris (`forms` nei dati), con i cristalli come predefinito. Sui cristalli l'osservazione è una colonna sola di colori, senza forme, bordi né "non si scioglie", e il confronto guarda solo i colori, anche per il colore atteso. Passando a cristalli un test che ha macchie, precipitato o bordi, la pagina chiede conferma e tiene il primo liquido. "Fa bolle" diventa "fa effervescenza" | Quei reagenti si vendono ormai soprattutto in cristalli, con gli stessi colori; le forme esistono perché c'è un liquido in cui la sostanza si scioglie o no, e su un cristallo la questione non si pone |
| D225 | Il **colore atteso che passa** non esclude: se nella lettura compare solo in una fase che poi cambia (l'anello viola dei catinoni con lo Zimmermann, poi marrone), chi non l'ha visto ma ha visto un colore documentato dopo ha una corrispondenza parziale, con l'invito a rifare il test e guardare i primi secondi. Il colore atteso che è il risultato finale continua a escludere (rivede D212) | Il colore che chi testa ha visto è documentato; una fase iniziale e breve si perde facilmente, il risultato finale no |

---

## Decisioni rinviate (backlog v2)

| # | Cosa | Nota |
|---|---|---|
| B1 | Sessione multi-osservazione con semantica AND | La vera potenza del matching ("Marquis viola + Simon's blu → MDMA") |
| B2 | "Perché" per riga: ogni osservazione confrontata con la scheda | |
| B3 | ~~Test successivo consigliato~~ | **Chiuso (D162–D180)**: il pannello esiste e lavora sui candidati (≥2/3 dei test), contando per colore |
| B4 | Occhiello (`EyeDropper`) per campionare il colore fisico | Solo Chrome/Edge, con fallback |
| B5 | Export CSV, riepilogo testuale da copiare | |

---

## Decisioni ancora aperte

| # | Domanda | Proposta |
|---|---|---|
| O1 | Come trattare il diritto d'autore dei chart | **Per ora non bloccante** (uso personale); se la pagina verrà condivisa, chiedere il via libera a chi ne detiene i diritti. Nel frattempo: immagine originale invariata in pagina + dati citati |
| O2 | Come raffinare il matching del colore | Serve confronto con dati più completi e con l'uso reale in campo |
| O3 | Come trattare il caso "no reaction" osservato vs "non osservato" | Due controlli separati |
| O4 | Come presentare il riepilogo in testa alla tabella | Tre cifre con spiegazione al passaggio del mouse |
| O5 | Come impostare il timing nel modello (campo, unità, origine) | "0:00 → 0:30 s" come finestra per tappa |
| O6 | Quanto dato sul caricamento mettere nelle celle | Le fonti con note di quantità (Erowid, Dancesafe) sono sparse e non strutturate: meglio un set curato e citato che una matrice incompleta |
| O7 | ~~Se e come mostrare le osservazioni dell'utente accanto alle fonti~~ | **Chiuso (D47)**: non vengono salvate |
| O8 | Come popolare l'asse del caricamento oltre la metanfetamina con Simon's | Le fonti con dati di quantità sono articoli scientifici, non tabelle: va cercato caso per caso (Tusiewicz et al. 2021 per i catinoni; UNODC per le norme di protocollo) |
| O9 | ~~Il colore atteso nel **confronto** della pagina (D208, D209)~~ | **Chiuso (D212)** |
| O10 | ~~Come rappresentare **due colori insieme**~~ | **Chiuso (D217)**; resta da far dire i dettagli alle osservazioni e contarli nel confronto (O13) |
| O13 | ~~I **dettagli nelle osservazioni**~~ | **Chiuso (D221, D222)** |
| O11 | ~~Le **letture ripetute** fra osservazioni diverse della stessa fonte~~ | **Chiuso (D216)** |
| O12 | ~~Quanto il database dei reagenti di PsychonautWiki **dipende dal NIJ**~~ | **Chiuso, non serve**: la pagina non conta quante fonti concordano, quindi una lettura copiata non cambia il confronto. Torna utile solo se un giorno il confronto peserà le fonti indipendenti |
