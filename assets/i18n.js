/* Interface strings. Chemical names stay in English; everything around them
 * follows the chosen language. */

const STRINGS = {
  it: {
    langName: "Italiano",
    otherLang: "EN",
    title: "Colori dei test con reagenti",
    download: "Scarica",
    downloadHint: "La pagina in un file solo, da usare anche senza connessione",
    banner:
      "I test colorimetrici sono presuntivi e qualitativi: un colore suggerisce quale sostanza potrebbe esserci, non quanta ce n'è, e un test negativo non la esclude. Solo un'analisi di laboratorio, come la gascromatografia-spettrometria di massa (GC-MS), dà una risposta certa.",
    skip: "Salta alla tabella",
    bannerClose: "Chiudi l'avviso",
    bannerOpen: "Mostra l'avviso",

    obsTitle: "Osservazioni",
    obsReagent: "Reagente",
    obsColour: "Colori",
    obsRemove: "Togli l'osservazione",
    obsNoReaction: "nessuna reazione",
    obsProportionLabel: "Proporzione",
    proportionHelpLabel: "Che cos'è la proporzione",
    proportionHelpWhat:
      "Quanta sostanza per quanto reagente. Quella consigliata è una punta di polvere, grande come una testa di fiammifero, per una goccia di reagente.",
    proportionHelpWhy:
      "Con più sostanza il colore si scurisce e può sembrare nero; con meno può essere chiaro o non vedersi. Quasi tutti i colori della tabella sono documentati alla proporzione consigliata: se ne hai usata un'altra, indicalo qui.",
    obsReactionLabel: "Reazione",
    proportion: {
      standard: "proporzione consigliata",
      high: "proporzione alta",
      low: "proporzione bassa",
    },
    /* the short ones, for the select: the long label is written above */
    proportionShort: {
      standard: "consigliata",
      high: "alta",
      low: "bassa",
    },
    obsAddReaction: "+ aggiungi reazione",
    obsAddStage: "Aggiungi una fase",
    obsCancel: "annulla",
    obsConfirm: "conferma",
    obsRemoveStage: "Togli la fase",
    partialReturn:
      "Nella documentazione {hue} compare due volte: verifica che il tuo sia quello finale, dopo {before}.",
    partialLater: "La reazione va avanti: dopo {seen} la documentazione prevede ancora {rest}.",
    partialMissedStart: "La documentazione inizia con {missed}: potresti non aver visto le prime fasi.",
    partialMissedBetween:
      "Fra {from} e {to} la documentazione prevede anche {missed}: potresti non averlo visto.",
    differenceExtraPhases:
      "Hai visto {extra} dopo {last}: nessuna fonte lo documenta. Può succedere aspettando più del tempo indicato o con un test venuto male: se puoi, ripeti il test.",
    partialIntensity:
      "L'intensità documentata è {doc}, tu hai indicato {seen}: verifica quale delle due hai visto.",
    partialProportion:
      "Questa lettura è documentata alla proporzione {doc}, tu hai indicato la proporzione {seen}: il colore può variare in base alla proporzione tra sostanza e reagente.",
    warningsLabel: "Cosa verificare su questa lettura",
    conflictColour:
      "una fonte riporta un colore: controlla reagente e dose",
    conflictObservation:
      "questa sostanza non corrisponde a questo test, ma sì agli altri",
    nextTitle: "Prossimo test",
    nextOne:
      "Resta solo {name}. Un altro test la conferma se dà il colore indicato.",
    nextEmpty:
      "Nessuna delle {t} sostanze è compatibile con i test che hai fatto: i colori che hai descritto non possono stare insieme. Togli un test e riguarda.",
    nextNone: "non distingue niente",
    nextReducesTo: "Riduce a:",
    nextCardsLabel: "i test consigliati",
    nextLeft: "{n} candidati",
    nextLeftOne: "1 candidato",
    nextRange: "{mean} in media, {worst} nel caso peggiore",
    nextAdd: "Aggiungi alle osservazioni",
    nextAddShort: "Aggiungi",
    nextUse: "Aggiungi alle osservazioni: {reagent}",
    obsShare: "copia il link",
    obsShareDone: "link copiato",

    tableTitle: "La tabella",
    hbarLabel: "Scorri la tabella lateralmente",
    coverage: "{n} su {t} documentate",
    colSubstance: "Sostanza",
    matchesEmptyText:
      "Nessuna sostanza dà questo colore con questo reagente.",
    matchesEmptyConflicts:
      "Per {n} sostanze una fonte riporta un colore dove tu non hai visto reazione: il reagente potrebbe essere vecchio, o la sostanza troppo poca.",
    matchesEmptyConflictOne:
      "Per 1 sostanza una fonte riporta un colore dove tu non hai visto reazione: il reagente potrebbe essere vecchio, o la sostanza troppo poca.",
    matchesEmptyHint:
      "Se hai usato più o meno sostanza del solito, indicalo nella proporzione oppure ripeti il test.",
    matchesTitle: "Corrispondenze",
    matchesTotalTitle: "Corrispondenze totali",
    matchesPartialTitle: "Corrispondenze parziali",
    matchesIncongruentTitle: "Corrispondenze incongruenti",
    matchesAtLeast: "almeno {k} test su {n}",
    matchesFewer: "meno di {k} test su {n}",
    matchesTotalEmptyText:
      "Nessuna sostanza dà questi colori con tutti i test.",
    matchesPartialEmptyHint:
      "{n} sostanze soddisfano solo una parte dei test: sono qui sotto.",
    restTitle: "Altre sostanze",
    noData: "nessun dato",
    noReaction: "nessuna reazione",
    inconsistent: "risultato incoerente",
    disputed: "fonti in disaccordo",
    warningNoData:
      "nessuno ha documentato questa sostanza con questo reagente: il test non poteva escluderla",
    sourcesWithData: "{n} fonti su {t} hanno dati",
    sourcesLink: "fonti",

    detailClose: "Chiudi il dettaglio",
    detailAliases: "Alias",
    detailReagents: "Reagenti",
    detailWiki: "Vedi la voce della fonte",
    timingInstant: "istantanea",
    timingStir: "mescola",
    readingFizz: "fa bolle",
    readingFade: "{color} svanisce",
    shapes: {
      spots: "a macchie",
      ring: "ad anello",
      precipitate: "con precipitato",
      particles: "con particelle",
    },

    types: {
      Substance: "Sostanza",
      Adulterant: "Adulterante",
      Class: "Classe",
      Forms: "Forme",
    },

    blindSpots: "Questi test non dicono niente su: {names}.",

    dataTitle: "Reagenti e fonti",
    dataReagents: "Reagenti",
    reagentCoverage: "Dati per {n} sostanze su {t}",
    reagentSource: "Fonte",
    reagentSourceOriginal: "Testo originale, non tradotto.",
    reagentSourceTranslated: "Testo tradotto dall'originale.",
    dataSources: "Fonti e licenze",
    descriptionsDownload: "Scarica le descrizioni dei reagenti (descriptions.js)",

    themeToggle: "Cambia tema chiaro/scuro",
  },

  en: {
    langName: "English",
    otherLang: "IT",
    title: "Reagent test colours",
    download: "Download",
    downloadHint: "The page in a single file, to use offline too",
    banner:
      "Colour tests are presumptive and qualitative: a colour suggests which substance might be there, not how much of it, and a negative test does not rule it out. Only a laboratory analysis, such as gas chromatography–mass spectrometry (GC-MS), gives a certain answer.",
    skip: "Skip to the table",
    bannerClose: "Close the warning",
    bannerOpen: "Show the warning",

    obsTitle: "Observations",
    obsReagent: "Reagent",
    obsColour: "Colours",
    obsRemove: "Remove the observation",
    obsNoReaction: "no reaction",
    obsProportionLabel: "Proportion",
    proportionHelpLabel: "What the proportion is",
    proportionHelpWhat:
      "How much substance for how much reagent. The recommended one is a pinch of powder, the size of a match head, for one drop of reagent.",
    proportionHelpWhy:
      "With more substance the colour darkens and can look black; with less it can be pale or not show at all. Almost every colour in the table is documented at the recommended proportion: if you used another one, say so here.",
    obsReactionLabel: "Reaction",
    proportion: {
      standard: "recommended proportion",
      high: "high proportion",
      low: "low proportion",
    },
    proportionShort: {
      standard: "recommended",
      high: "high",
      low: "low",
    },
    obsAddReaction: "+ add reaction",
    obsAddStage: "Add a phase",
    obsCancel: "cancel",
    obsConfirm: "confirm",
    obsRemoveStage: "Remove the phase",
    partialReturn:
      "In the documentation {hue} appears twice: check that yours is the final one, after {before}.",
    partialLater: "The reaction goes on: after {seen} the documentation still expects {rest}.",
    partialMissedStart: "The documentation starts with {missed}: you may have missed the first phases.",
    partialMissedBetween:
      "Between {from} and {to} the documentation also has {missed}: you may have missed it.",
    differenceExtraPhases:
      "You saw {extra} after {last}: no source documents it. It can happen if you waited longer than the stated time or the test went wrong: if you can, repeat the test.",
    partialIntensity:
      "The documented intensity is {doc}, you set {seen}: check which of the two you saw.",
    partialProportion:
      "This reading is documented at the {doc} proportion, you set the {seen} proportion: the colour can vary with the proportion of substance to reagent.",
    warningsLabel: "What to check about this reading",
    conflictColour:
      "a source reports a colour: check reagent and dose",
    conflictObservation:
      "this substance does not fit this test, but it does fit the others",
    nextTitle: "Next test",
    nextOne:
      "Only {name} is left. Another test confirms it if it gives the colour shown.",
    nextEmpty:
      "None of the {t} substances is compatible with the tests you made: the colours you described cannot go together. Remove a test and look again.",
    nextNone: "tells nothing apart",
    nextReducesTo: "Reduces to:",
    nextCardsLabel: "the suggested tests",
    nextLeft: "{n} candidates",
    nextLeftOne: "1 candidate",
    nextRange: "{mean} on average, {worst} at worst",
    nextAdd: "Add to the observations",
    nextAddShort: "Add",
    nextUse: "Add to the observations: {reagent}",
    obsShare: "copy the link",
    obsShareDone: "link copied",

    tableTitle: "The table",
    hbarLabel: "Scroll the table sideways",
    coverage: "{n} of {t} documented",
    colSubstance: "Substance",
    matchesEmptyText:
      "No substance gives this colour with this reagent.",
    matchesEmptyConflicts:
      "For {n} substances a source reports a colour where you saw no reaction: the reagent may be old, or the sample too small.",
    matchesEmptyConflictOne:
      "For 1 substance a source reports a colour where you saw no reaction: the reagent may be old, or the sample too small.",
    matchesEmptyHint:
      "If you used more or less substance than usual, set the proportion or repeat the test.",
    matchesTitle: "Matches",
    matchesTotalTitle: "Total matches",
    matchesPartialTitle: "Partial matches",
    matchesIncongruentTitle: "Inconsistent matches",
    matchesAtLeast: "at least {k} of {n} tests",
    matchesFewer: "fewer than {k} of {n} tests",
    matchesTotalEmptyText:
      "No substance gives these colours with every test.",
    matchesPartialEmptyHint:
      "{n} substances fit only some of the tests: they are listed below.",
    restTitle: "Other substances",
    noData: "no data",
    noReaction: "no reaction",
    inconsistent: "inconsistent result",
    disputed: "sources disagree",
    warningNoData:
      "nobody documented this substance with this reagent: the test could not have excluded it",
    sourcesWithData: "{n} of {t} sources have data",
    sourcesLink: "sources",

    detailClose: "Close the detail",
    detailAliases: "Aliases",
    detailReagents: "Reagents",
    detailWiki: "See the source's entry",
    timingInstant: "instant",
    timingStir: "stir",
    readingFizz: "fizzes",
    readingFade: "{color} fades",
    shapes: {
      spots: "in spots",
      ring: "in a ring",
      precipitate: "with a precipitate",
      particles: "with particles",
    },

    types: {
      Substance: "Substance",
      Adulterant: "Adulterant",
      Class: "Class",
      Forms: "Forms",
    },

    blindSpots: "These tests say nothing about: {names}.",

    dataTitle: "Reagents and sources",
    dataReagents: "Reagents",
    reagentCoverage: "Data for {n} of {t} substances",
    reagentSource: "Source",
    reagentSourceOriginal: "Original text, not translated.",
    reagentSourceTranslated: "Text translated from the original.",
    dataSources: "Sources and licences",
    descriptionsDownload: "Download the reagent descriptions (descriptions.js)",

    themeToggle: "Switch light/dark theme",
  },
};

window.I18N = { STRINGS };
