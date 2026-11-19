/* The page: one table, ordered by what the user observed.
 *
 * State is small and lives in one place; every view is derived from it.
 */

/* the page is loaded as classic scripts so that it works from disk too;
   this IIFE keeps its constants out of the global scope */
(() => {
  const { STRINGS } = window.I18N;
  const {
    HUES, SHADES,
    hueOf, shadeOf, stripOf, cssGradient, colorName, captionOf, hexFor,
    hueName, modifierName,
  } = window.Colors;

  const DATA = window.REAGENTS;
  /* the descriptions of the reagents: their licence, their sources and
     the texts by language */
  const DESCRIPTIONS = window.DESCRIPTIONS || {};
  /* the reagents in alphabetical order, everywhere: the table, the select
     and the reagent cards; the source orders them by coverage */
  DATA.reagents.sort((a, b) => a.name.localeCompare(b.name));
  /* how many substances each reagent documents: the coverage the headers
     of the table and the reagent cards show */
  for (const reagent of DATA.reagents) {
    reagent.known = DATA.substances.filter((substance) => substance.reactions[reagent.id]).length;
    reagent.total = DATA.substances.length;
  }

  /* A reading is a colour, "no reaction" (no colours) or an inconsistent
     result (null). Without a proportion it is at the recommended one. */
  function levelOf(reading) {
    return reading.proportion || "standard";
  }

  function isColour(reading) {
    return !!reading.colors?.length;
  }

  function isNoReaction(reading) {
    return reading.colors?.length === 0;
  }

  /* What a reading says besides its colours: it fizzes, the colour comes
     in spots or a ring, a colour fades away. */
  function readingExtras(reading) {
    const out = [];
    if (reading.shape) out.push(t(`shapes.${reading.shape}`));
    if (reading.fizz) out.push(t("readingFizz"));
    if (reading.fade) {
      out.push(interpolate(t("readingFade"), { color: colorName(reading.fade, state.lang) }));
    }
    return out;
  }

  /* The colours of a reading that are the reaction. A reagent with a colour
     of its own — the yellow of the Mandelin — is registered as the first
     phase of every reading: it is the drop on the sample before anything
     happens, not the reaction. A reading that is nothing but that colour
     is a reaction that did not happen. */
  function reactionColors(reading, reagentId) {
    const base = REAGENT_BY_ID[reagentId]?.baseColor;
    if (!reading.colors) return null;
    return base && reading.colors[0] === base ? reading.colors.slice(1) : reading.colors;
  }

  /* The same for what the user saw: a first phase in the reagent's own
     hue is the reagent. Seeing only that is seeing nothing happen. */
  function seenReaction(seen) {
    const base = REAGENT_BY_ID[seen.reagent]?.baseColor;
    if (seen.noReaction) return [];
    if (base && seen.stages[0]?.hue === hueOf(base)) return seen.stages.slice(1);
    return seen.stages;
  }

  /* Do the sources of a cell disagree? One sees a colour and another sees
     nothing happen, or two report colours with nothing in common. Each
     source is taken as a whole: the alternatives one source gives ("orange
     or brown") are not a disagreement. */
  function sourcesDisagree(readings, reagentId) {
    const reactions = readings.map((reading) => reactionColors(reading, reagentId));
    if (reactions.some((colors) => colors?.length) && reactions.some((colors) => colors?.length === 0)) {
      return true;
    }
    const huesBySource = new Map();
    readings.forEach((reading, index) => {
      if (!reactions[index]?.length) return;
      if (!huesBySource.has(reading.source)) huesBySource.set(reading.source, new Set());
      for (const color of reactions[index]) huesBySource.get(reading.source).add(hueOf(color));
    });
    const sets = [...huesBySource.values()];
    return sets.some((first, index) =>
      sets.slice(index + 1).some((second) => ![...first].some((hue) => second.has(hue))));
  }

  /* The theme the reader chose, or the system's. The page starts dark and
     the script in the head applies this before the first paint, so there
     is no flash of the wrong colour. */
  function storedTheme() {
    try {
      const t = localStorage.getItem("theme");
      if (t === "light" || t === "dark") return t;
    } catch (e) { /* file:// can block the storage */ }
    return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  /* the warning, once closed, stays closed on the next visit */
  function storedBannerClosed() {
    try {
      return localStorage.getItem("bannerClosed") === "1";
    } catch (e) { /* file:// can block the storage */ }
    return false;
  }
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  /* The little clock that says "how long the test takes": it is drawn
     once and used both in the cards of the next test and in the tiles
     of the observations. */
  function clockIcon() {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "clock-icon");
    svg.setAttribute("viewBox", "0 0 16 16");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("focusable", "false");
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", "8");
    circle.setAttribute("cy", "8");
    circle.setAttribute("r", "6.4");
    const hands = document.createElementNS("http://www.w3.org/2000/svg", "path");
    hands.setAttribute("d", "M8 4.4V8l2.6 1.7");
    svg.append(circle, hands);
    return svg;
  }

  const state = {
    lang: "it",
    /* the page opens with the theme of the system; the button overrides it */
    theme: storedTheme(),
    bannerClosed: storedBannerClosed(),
    /* {id, reagent, noReaction, proportion, stages:[{hue, modifier}]}
       Every test carries its own proportion of product to reagent: one test
       can be loaded differently from the next. */
    observations: [],
  };

  /* the proportions of product to reagent, from less product to more */
  const PROPORTION_SCALE = ["low", "standard", "high"];

  /* ── l'indirizzo che si può condividere ──────────────────────────
     Le osservazioni stanno nel frammento dell'indirizzo: il link porta
     con sé i test che hai fatto e la pagina non deve salvare niente
     (D47). Il formato è leggibile, così si può anche correggerlo a mano:

       #obs=marquis:orange.deep@high;robadope:none&lang=en

     ogni osservazione è  reagente : fasi @ proporzione
     ogni fase è  tinta[.intensità]  e le fasi sono separate da "+";
     "none" vuol dire nessuna reazione; una fase vuota è una fase
     ancora da scegliere. */
  function encodeState() {
    /* Only the completed tests go into the link: a row still in progress
       is not something to share, and the link must not change because
       the reader has chosen another reagent for the next test. When
       there is nothing completed, the link is empty. */
    const parts = state.observations.filter(isActive).map((o) => {
      let stages;
      if (o.noReaction) {
        stages = "none";
      } else {
        stages = o.stages
          .map((st) => (st.hue ? st.hue + (st.modifier ? "." + st.modifier : "") : ""))
          .join("+");
      }
      const prop = o.proportion && o.proportion !== "standard"
        ? "@" + o.proportion : "";
      return `${o.reagent}:${stages}${prop}`;
    });
    if (!parts.length) return "";
    let frag = "obs=" + parts.join(";");
    if (state.lang !== "it") frag += "&lang=" + state.lang;
    return frag;
  }

  function decodeState(frag) {
    const out = { observations: [], lang: null };
    for (const chunk of frag.split("&")) {
      const eq = chunk.indexOf("=");
      if (eq < 0) continue;
      const key = chunk.slice(0, eq);
      const value = chunk.slice(eq + 1);
      if (key === "lang") {
        if (value === "en" || value === "it") out.lang = value;
        continue;
      }
      if (key !== "obs") continue;
      for (const one of value.split(";")) {
        if (!one) continue;
        const colon = one.indexOf(":");
        if (colon < 0) continue;
        const reagent = one.slice(0, colon);
        if (!DATA.reagents.some((r) => r.id === reagent)) continue;
        let rest = one.slice(colon + 1);
        let proportion = "standard";
        const at = rest.indexOf("@");
        if (at >= 0) {
          const prop = rest.slice(at + 1);
          if (prop === "high" || prop === "low") proportion = prop;
          rest = rest.slice(0, at);
        }
        const stages = [];
        let noReaction = false;
        if (rest === "none") {
          noReaction = true;
        } else {
          for (const one2 of rest.split("+")) {
            if (!one2) { stages.push({ hue: null, modifier: null }); continue; }
            const dot = one2.indexOf(".");
            const hue = dot < 0 ? one2 : one2.slice(0, dot);
            const mod = dot < 0 ? null : one2.slice(dot + 1);
            if (!HUES.includes(hue)) continue;
            stages.push({
              hue,
              modifier: SHADES.includes(mod) ? mod : null,
            });
          }
        }
        if (!stages.length && !noReaction) continue;
        out.observations.push({
          id: Math.random().toString(36).slice(2),
          reagent,
          noReaction,
          proportion,
          stages: noReaction ? [{ hue: null, modifier: null }] : stages,
          auto: true,
        });
      }
    }
    return out;
  }

  /* The address bar is where the link lives: it is updated as the
     observations change, so that copying the address is copying the
     link. The history is not filled with steps: replaceState, and when
     the browser refuses (some file:// pages), replace. */
  function syncUrl() {
    const frag = encodeState();
    const url = location.pathname + location.search + (frag ? "#" + frag : "");
    try {
      history.replaceState(null, "", url);
    } catch (e) {
      try { location.replace(url); } catch (e2) { /* nothing we can do */ }
    }
  }

  function loadFromUrl() {
    const from = decodeState(location.hash.replace(/^#/, ""));
    state.observations = from.observations;
    if (from.lang) state.lang = from.lang;
  }

  let lastFocused = null;

  /* ── helpers ──────────────────────────────────────────────────── */

  function t(key) {
    const s = STRINGS[state.lang];
    return key.split(".").reduce((o, k) => (o ? o[k] : undefined), s) ?? key;
  }

  function interpolate(str, vars) {
    return str.replace(/\{(\w+)\}/g, (_, k) => (vars[k] !== undefined ? vars[k] : `{${k}}`));
  }

  /* The same, as nodes: the values go in bold, so that they stand out from
     the sentence around them. */
  function interpolateStrong(str, vars) {
    const fragment = document.createDocumentFragment();
    for (const part of str.split(/(\{\w+\})/)) {
      const name = part.match(/^\{(\w+)\}$/)?.[1];
      if (name && vars[name] !== undefined) {
        const strong = document.createElement("strong");
        strong.textContent = vars[name];
        fragment.append(strong);
      } else if (part) {
        fragment.append(part);
      }
    }
    return fragment;
  }

  const REAGENT_BY_ID = Object.fromEntries(DATA.reagents.map((r) => [r.id, r]));

  function reagentName(id) {
    return REAGENT_BY_ID[id]?.name ?? id;
  }

  function typeName(type) {
    return t(`types.${type}`) ?? type;
  }

  /* ── matching ─────────────────────────────────────────────────── */

  /* Does a documented reading match what the user saw?
   *
   * "pieno"      the reading contains what was observed
   * "parziale"   it does, with something left to check: the reaction goes
   *              on after what was seen, the colour comes back, the
   *              intensity is not the same, the reading is for another
   *              amount of product
   * "differenze" it does, but the user saw something no source documents
   *              (phases after the documented end): it still counts as a
   *              match, a weaker one
   * "no"         the two have nothing in common
   *
   * The warnings say why a match is not full, so a match is full exactly
   * when there are none. Each is a string key, the values in conflict —
   * which the popover writes in bold — and its kind: "check" for what is
   * left to check, "difference" for what contradicts the documentation. */
  function matchReading(reading, seen) {
    const none = { outcome: "no", warnings: [] };
    /* the reaction only: the reagent's own colour is left out on both
       sides */
    const colors = reactionColors(reading, seen.reagent);
    const stages = seenReaction(seen);
    /* nothing happened: it matches a reading where nothing happens */
    if (!stages.length) {
      return colors?.length === 0 ? { outcome: "pieno", warnings: [] } : none;
    }
    if (!colors?.length) return none;
    const docHues = colors.map(hueOf);
    const last = docHues.length - 1;
    const sequence = (colors) => captionOf(colors, state.lang).replace(/\n→ /g, " → ");
    const warnings = [];

    if (stages.length === 1) {
      /* A single colour: what matters is where it falls in the documented
         reaction. The final colour is the result. A colour that comes
         before the end means the reaction goes on; the final colour that
         also appears earlier means the reaction comes back to it, and the
         user has to be sure to be at the end. */
      const one = stages[0];
      const first = docHues.indexOf(one.hue);
      if (first < 0) return none;
      const atEnd = docHues[last] === one.hue;
      if (!atEnd) {
        warnings.push({ kind: "check", key: "partialLater", vars: {
          seen: hueName(one.hue, state.lang),
          rest: sequence(colors.slice(first + 1)),
        } });
      } else if (first < last) {
        warnings.push({ kind: "check", key: "partialReturn", vars: {
          hue: hueName(one.hue, state.lang),
          before: hueName(docHues[last - 1], state.lang),
        } });
      }
      /* the intensity is compared on the phase the colour matches */
      const docShade = shadeOf(colors[atEnd ? last : first]);
      if (one.modifier && docShade && one.modifier !== docShade) {
        warnings.push({ kind: "check", key: "partialIntensity", vars: {
          doc: modifierName(docShade, state.lang),
          seen: modifierName(one.modifier, state.lang),
        } });
      }
    } else {
      /* Several phases: they have to appear in the documented reaction in
         the same order, not necessarily one right after the other. A phase
         can be short enough to be missed, at the start or in between: the
         match stands, and says which. Phases seen after the documented end
         are a difference; a phase that strays while the documented
         reaction goes on is no match. */
      const positions = [];
      let from = 0;
      for (const stage of stages) {
        const position = docHues.indexOf(stage.hue, from);
        if (position < 0) break;
        positions.push(position);
        from = position + 1;
      }
      if (!positions.length) return none;
      const extra = stages.slice(positions.length);
      const lastMatched = positions[positions.length - 1];
      if (extra.length && lastMatched !== last) return none;
      const seenCaption = (stages) => stages.map((stage) => hueName(stage.hue, state.lang)).join(" → ");
      if (positions[0] > 0) {
        warnings.push({ kind: "check", key: "partialMissedStart", vars: {
          missed: sequence(colors.slice(0, positions[0])),
        } });
      }
      positions.forEach((position, index) => {
        const previous = positions[index - 1];
        if (index === 0 || position === previous + 1) return;
        warnings.push({ kind: "check", key: "partialMissedBetween", vars: {
          from: hueName(docHues[previous], state.lang),
          to: hueName(docHues[position], state.lang),
          missed: sequence(colors.slice(previous + 1, position)),
        } });
      });
      if (lastMatched < last) {
        warnings.push({ kind: "check", key: "partialLater", vars: {
          seen: seenCaption(stages),
          rest: sequence(colors.slice(lastMatched + 1)),
        } });
      }
      if (extra.length) {
        warnings.push({ kind: "difference", key: "differenceExtraPhases", vars: {
          extra: seenCaption(extra),
          last: hueName(docHues[last], state.lang),
        } });
      }
    }
    /* the reading is for a different amount of product: the match is real,
       but weaker */
    const level = seen.proportion || "standard";
    if (levelOf(reading) !== level) {
      warnings.push({ kind: "check", key: "partialProportion", vars: {
        doc: t(`proportionShort.${levelOf(reading)}`),
        seen: t(`proportionShort.${level}`),
      } });
    }
    const outcome = warnings.some((warning) => warning.kind === "difference") ? "differenze"
      : warnings.length ? "parziale" : "pieno";
    return { outcome, warnings };
  }

  /* The best outcome over every reading of a cell. */
  function matchCell(readings, seen) {
    if (!readings) return "no";
    /* an observation where the colour has not been chosen yet says nothing:
       it matches nothing and contradicts nothing */
    if (!seen.noReaction && (!seen.stages.length || seen.stages.some((s) => !s.hue))) {
      return "no";
    }
    /* the outcomes from the strongest to the weakest */
    const rank = ["no", "differenze", "parziale", "pieno"];
    let best = "no";
    for (const reading of readings) {
      const { outcome } = matchReading(reading, seen);
      if (rank.indexOf(outcome) > rank.indexOf(best)) best = outcome;
    }
    /* The user saw no reaction and a source documents a colour: a real
       contradiction, and the one that may point at the technique (old
       reagent, too little sample). The opposite — the user saw a colour
       and a source says nothing happens — is not a conflict, just the
       substance being ruled out: the cell shows the source's reading, so
       the reason is visible. */
    if (best === "no" && !seenReaction(seen).length &&
        readings.some((reading) => reactionColors(reading, seen.reagent)?.length)) {
      return "conflitto";
    }
    return best;
  }

  /* Evaluate a substance against all the observations.
   * Returns {hits: [{reagent, outcome}], conflicts: n} */
  /* An observation that says nothing yet — no colour, no "no reaction" —
     takes no part in the matching: it would only move rows around without
     any reason. */
  function isActive(obs) {
    if (obs.noReaction) return true;
    return obs.stages.some((st) => st.hue);
  }

  function activeObservations() {
    return state.observations.filter(isActive);
  }

  /* A match, full or not, counts as a match. */
  function isHit(outcome) {
    return outcome === "pieno" || outcome === "parziale" || outcome === "differenze";
  }

  /* Evaluate a substance against all the observations.
   *
   * The observations become a bit mask: one bit per observation, in the
   * order they were made, the first one being the most significant. A
   * substance that matches the first two and not the third is 110, and
   * comes before one that matches only the third (001). The mask is also
   * what the sorting uses.
   */
  function evaluate(substance) {
    const bits = [];
    let mask = 0;
    let conflicts = 0;
    for (const seen of activeObservations()) {
      const readings = substance.reactions[seen.reagent];
      const outcome = matchCell(readings, seen);
      const hit = isHit(outcome);
      /* is there any data for this substance with this reagent? */
      const hasData = !!readings;
      bits.push({ seen, outcome, hit, hasData });
      mask = (mask << 1) | (hit ? 1 : 0);
      if (outcome === "conflitto") conflicts++;
    }
    return {
      bits, mask, conflicts,
      hits: bits.filter((b) => b.hit),
      /* the tests it fits with something no source documents */
      differences: bits.filter((b) => b.outcome === "differenze").length,
    };
  }

  /* ── the table ────────────────────────────────────────────────── */

  /* The substances that the tests the user made cannot say anything about:
     no data for any of the reagents used. */
  function missingSubstances() {
    const used = [...new Set(activeObservations().map((o) => o.reagent))];
    if (!used.length) return new Set();
    const out = new Set();
    for (const s of DATA.substances) {
      const blind = used.every((r) => !s.reactions[r]);
      if (blind) out.add(s.id);
    }
    return out;
  }

  /* The columns: the reagents you are testing with come first, in the order
     you started using them, then all the others in alphabetical order. */
  function orderedReagents() {
    const used = [];
    /* only the tests that are actually filled in move a column: an
       observation that has just been added and has no colour yet must not
       shuffle the table under the reader's eyes */
    for (const obs of activeObservations()) {
      if (!used.includes(obs.reagent)) used.push(obs.reagent);
    }
    const rest = DATA.reagents
      .map((r) => r.id)
      .filter((id) => !used.includes(id));
    return [...used, ...rest]
      .map((id) => DATA.reagents.find((r) => r.id === id))
      .filter(Boolean);
  }

  function buildHead(table) {
    const head = table.tHead;
    head.textContent = "";
    const tr = document.createElement("tr");

    const thSub = document.createElement("th");
    thSub.scope = "col";
    thSub.className = "col-substance";
    thSub.textContent = t("colSubstance");
    /* The other columns have two lines (name and coverage). This one had
       only the name, and the empty half of the cell showed as a gap
       between the header and the first row. */
    const subSmall = document.createElement("small");
    subSmall.textContent = String(DATA.substances.length);
    thSub.append(subSmall);
    tr.append(thSub);

    for (const r of orderedReagents()) {
      const th = document.createElement("th");
      th.scope = "col";
      th.dataset.reagent = r.id;
      th.textContent = r.name;
      const small = document.createElement("small");
      small.textContent = r.known + "/" + r.total;
      th.append(small);
      tr.append(th);
    }
    head.append(tr);
  }

  /* A note can come in two languages. */
  function noteText(note) {
    if (!note) return "";
    if (typeof note === "string") return note;
    return note[state.lang] || note.en || "";
  }

  function cellNode(substance, reagentId, ev) {
    const td = document.createElement("td");
    td.title = `${substance.name} · ${reagentName(reagentId)}`;
    const readings = substance.reactions[reagentId];
    const obs = state.observations.find((o) => o.reagent === reagentId);
    /* The substance fits some of the observations and not this one: the
       cell says so — and says whether it is a contradiction or a hole in
       the data. */
    const bitsHere = (ev?.bits || []).filter((b) => b.seen.reagent === reagentId);
    const fitsHere = bitsHere.some((b) => b.hit);
    const fitsSomewhere = (ev?.mask || 0) > 0;
    const hasDataHere = bitsHere.some((b) => b.hasData) || !!readings;

    if (!readings) {
      /* the absence is written, not drawn: a hatched square says "there is
         nothing here", the words say "there is nothing here" */
      const d = document.createElement("div");
      d.className = "cell-no-data";
      d.textContent = t("noData");
      td.append(d);
      /* Nobody documented this substance with this reagent: if the
         substance fits the other tests, this one could not have excluded
         it. A warning, not a negative. Only for the reagents that were
         actually tested: for the others "no data" is just "no data". */
      if (fitsSomewhere && bitsHere.length && !fitsHere) {
        td.classList.add("cell-warning");
        td.title += " — " + t("warningNoData");
      }
      return td;
    }

    const wrap = document.createElement("div");
    wrap.className = "cell";

    const outcome = obs ? matchCell(readings, obs) : null;
    /* The proportion of the test the user made with this reagent: it tells
       which of the readings in this cell is the one being compared. */
    const level = obs ? (obs.proportion || "standard") : null;

    /* Every documented reading is shown, grouped by proportion: the cell is
       a reference, and the reader has to see what is documented at every
       proportion to understand what the comparison means. */
    const levels = ["standard", "low", "high"].filter((lv) =>
      readings.some((reading) => isColour(reading) && levelOf(reading) === lv));

    /* Which of the readings of this cell are the ones the user saw? The
       match is marked on the reading itself, not on the cell, and by the
       same comparison that sorts the table: a reading is outlined exactly
       when it matches, fully or not. */
    const seenHere = activeObservations().filter((o) => o.reagent === reagentId);
    const matches = (reading) =>
      seenHere.some((sn) => matchReading(reading, sn).outcome !== "no");

    const lines = document.createElement("div");
    lines.className = "cell-readings";
    /* Readings that look the same are shown once: what matters is the
       reading, not how many sources gave it. Which sources gave it is in
       the popover. */
    const shown = new Set();
    for (const lv of levels) {
      const tag = document.createElement("span");
      tag.className = lv === level ? "cell-prop cell-prop-on" : "cell-prop";
      tag.textContent = t(`proportion.${lv}`);
      lines.append(tag);
      for (const reading of readings) {
        if (!isColour(reading) || levelOf(reading) !== lv) continue;
        const extras = readingExtras(reading);
        const key = `${lv}|${captionOf(reading.colors, "en")}|${extras.join()}`;
        if (shown.has(key)) continue;
        shown.add(key);
        const line = document.createElement("div");
        line.className = "reading-line";
        const isMatch = matches(reading);
        if (isMatch) line.classList.add("reading-match");
        const strip = document.createElement("div");
        strip.className = "strip";
        strip.style.background = cssGradient(stripOf(reading.colors));
        const cap = document.createElement("span");
        cap.className = isMatch ? "cell-cap cap-match" : "cell-cap";
        cap.textContent = captionOf(reading.colors, state.lang);
        /* A strip that matches with something left to check gets a "!"
           beside it: a click lists everything there is to check about
           that reading. */
        const warnings = isMatch ? matchReading(reading, obs).warnings : [];
        /* the sources that gave this reading: it is shown once, but more
           than one source may have documented it */
        const sources = [...new Set(readings
          .filter((other) => isColour(other) && levelOf(other) === lv &&
            captionOf(other.colors, "en") === captionOf(reading.colors, "en"))
          .map((other) => other.source))];
        if (warnings.length) {
          const stripRow = document.createElement("div");
          stripRow.className = "strip-row";
          const warn = document.createElement("button");
          warn.type = "button";
          warn.className = warnings.some((warning) => warning.kind === "difference")
            ? "warn-btn warn-btn-difference" : "warn-btn";
          warn.textContent = "!";
          warn.setAttribute("aria-label", t("warningsLabel"));
          warn.addEventListener("click", (event) =>
            openWarnings(event, substance, reagentId, reading, sources, warnings));
          stripRow.append(strip, warn);
          line.append(stripRow, cap);
        } else {
          line.append(strip, cap);
        }
        if (extras.length) {
          const note = document.createElement("span");
          note.className = "cell-extra";
          note.textContent = extras.join(" · ");
          line.append(note);
        }
        lines.append(line);
      }
    }
    /* A source that saw no reaction is shown next to the colours the other
       sources saw: the disagreement has to be visible in the cell. */
    const others = [
      ["no-reaction", readings.filter(isNoReaction)],
      ["inconsistent", readings.filter((reading) => reading.colors === null)],
    ];
    for (const [key, list] of others) {
      if (!list.length) continue;
      /* a "no reaction" is a reading like any other: it says at which
         proportion it was seen. The label is not repeated when the cell
         already named that proportion for the colours. */
      if (!levels.includes("standard")) {
        const tag = document.createElement("span");
        tag.className = "cell-prop";
        tag.textContent = t("proportion.standard");
        lines.append(tag);
        levels.push("standard");
      }
      const line = document.createElement("div");
      line.className = "reading-line";
      /* the empty bar: a reading with no colour still has the shape of a
         reading, so the descriptions stay in the same column */
      const bar = document.createElement("div");
      bar.className = "strip strip-empty";
      line.append(bar);
      const span = document.createElement("span");
      span.className = "cell-text";
      span.textContent = key === "no-reaction" ? t("noReaction") : t("inconsistent");
      /* a "no reaction" that matches what the user saw is written like
         the colours, and the cell is outlined: there is no colour to
         frame, so the frame goes on the cell */
      if (key === "no-reaction" && list.some(matches)) {
        span.classList.add("cell-match");
        /* the square is the reading: it is the one that gets the green
           dashed frame */
        line.classList.add("reading-match");
      }
      line.append(span);
      lines.append(line);
    }
    wrap.append(lines);

    /* The link is in the flow, at the foot of the cell: absolute, it could
       land on top of the last reading. */
    const foot = document.createElement("div");
    foot.className = "cell-foot";
    const b = document.createElement("button");
    b.type = "button";
    b.className = "info-btn";
    b.textContent = t("sourcesLink");
    const n = new Set(readings.map((reading) => reading.source)).size;
    const total = Object.keys(DATA.sources).length;
    b.setAttribute("aria-label",
      `${substance.name} — ${reagentName(reagentId)}: ` +
      interpolate(t("sourcesWithData"), { n, t: total }));
    b.addEventListener("click", (ev) => openPopover(ev, substance, reagentId));
    foot.append(b);
    /* the foot is anchored to the cell, not to the readings: it is always
       at the bottom of the cell, and the readings leave it the room */
    td.append(foot);

    td.append(wrap);

    if (obs) {
      td.dataset.outcome = outcome || "no";
      /* A substance that fits no test at all is simply excluded, and
         stays quiet: the contradiction only matters when the other tests
         do fit it. */
      if (outcome === "conflitto" && fitsSomewhere) {
        td.classList.add("cell-conflict");
        td.title += " — " + t("conflictColour");
      }
      /* The substance fits the other tests but not this one: the cell says
         so. A substance that fits nothing is simply excluded, and stays
         quiet. Only for the reagents that were actually tested: for the
         others the cell is just a cell. */
      if (fitsSomewhere && bitsHere.length && !fitsHere &&
          !isHit(outcome) && outcome !== "conflitto" && hasDataHere) {
        td.classList.add("cell-conflict");
        td.title += " — " + t("conflictObservation");
      }
      /* the match is marked three times over: the cell takes the accent
         tint, the strip that corresponds gets an outline, and the name of
         the colour is in green */
      if (isHit(outcome)) td.classList.add("cell-hit");
    }
    return td;
  }

  function rowNode(substance, ev) {
    const tr = document.createElement("tr");
    if (ev.hits.length) tr.className = "row-match";

    const th = document.createElement("th");
    th.scope = "row";
    const nameWrap = document.createElement("span");
    nameWrap.className = "substance-name";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = substance.name;
    btn.title = substance.name;
    btn.addEventListener("click", () => openDetail(substance));
    nameWrap.append(btn);
    /* an alias already contained in the name would just repeat it
       (it stays in the data, so the search still finds it) */
    const extra = (substance.aliases || []).find(
      (a) => !substance.name.toLowerCase().includes(a.toLowerCase()));
    if (extra) {
      const al = document.createElement("span");
      al.className = "substance-alias";
      al.textContent = extra;
      nameWrap.append(al);
    }
    th.append(nameWrap);
    /* the type goes on a second line, and only when it says something:
       "Sostanza" is the default and would only be noise */
    if (substance.info.type !== "Substance") {
      const tag = document.createElement("span");
      tag.className = "substance-type";
      tag.textContent = typeName(substance.info.type);
      th.append(tag);
    }
    tr.append(th);

    /* the cells follow the order of the columns */
    for (const r of orderedReagents()) tr.append(cellNode(substance, r.id, ev));
    return tr;
  }

  /* ── the table ────────────────────────────────────────────────── */

  /* The table is built as one group per row-group. Each group has a single
   * sticky block holding, in this order, the name of the group and the names
   * of the columns: the title sits above the column headers, and both leave
   * together with their own group. */
  function buildTable(groups) {
    const host = $("#tables");
    host.textContent = "";

    const area = document.createElement("div");
    area.className = "table-area";

    const built = [];
    let tableCount = 0;
    for (const g of groups) {
      const wrap = document.createElement("div");
      wrap.className = "group";

      const head = document.createElement("div");
      head.className = "group-head";

      /* an empty title takes no space: it is the separator between the
         groups, and with one group there is nothing to separate */
      let title = null;
      if (g.title) {
        title = document.createElement("div");
        title.className = "group-title";
        const label = document.createElement("span");
        label.textContent = g.title;
        title.append(label);
        /* how many are in the group: the number a reader looks for, 0
           included */
        const count = document.createElement("span");
        count.className = "group-count";
        count.textContent = String(g.items.length);
        title.append(count);
        if (g.note) {
          const note = document.createElement("span");
          note.className = "group-note";
          note.textContent = g.note;
          title.append(note);
        }
        title.setAttribute("aria-hidden", "true");
        head.append(title);
      }

      const strip = document.createElement("div");
      strip.className = "thead-bar";
      strip.setAttribute("aria-hidden", "true");
      head.append(strip);

      const sc = document.createElement("div");
      sc.className = "table-scroll";
      sc.tabIndex = -1;
      /* the skip link points to the first table that really has rows */
      sc.id = tableCount === 0 ? "table-scroll" : "";

      if (g.empty) {
        /* Nothing matched: the section stays, and says what happened,
           where to look and what to check — in that order. */
        const empty = document.createElement("div");
        empty.className = "group-empty";
        const body = document.createElement("p");
        body.className = "group-empty-text";
        body.textContent = t(g.emptyText || "matchesEmptyText");
        empty.append(body);
        if (g.emptyExtra) {
          const extra = document.createElement("p");
          extra.className = "group-empty-hint";
          extra.textContent = g.emptyExtra;
          empty.append(extra);
        }
        if (g.conflicts) {
          const conflicts = document.createElement("p");
          conflicts.className = "group-empty-conflicts";
          conflicts.textContent = g.conflicts === 1
            ? t("matchesEmptyConflictOne")
            : interpolate(t("matchesEmptyConflicts"), { n: g.conflicts });
          empty.append(conflicts);
        }
        const hint = document.createElement("p");
        hint.className = "group-empty-hint";
        hint.textContent = t("matchesEmptyHint");
        empty.append(hint);
        wrap.append(head, empty);
        area.append(wrap);
        built.push({ sc, table: null, title, strip });
        continue;
      }

      const table = document.createElement("table");
      table.className = "data-table";
      const cap = document.createElement("caption");
      cap.className = "sr-only";
      cap.textContent = g.title || t("tableTitle");
      table.append(cap);
      const thead = document.createElement("thead");
      table.append(thead);
      buildHead(table);
      const tb = document.createElement("tbody");
      tb.setAttribute("aria-label", g.title || t("restTitle"));
      for (const item of g.items) tb.append(rowNode(item.s, item.ev));
      table.append(tb);
      tableCount++;

      sc.append(table);
      wrap.append(head, sc);
      area.append(wrap);
      built.push({ sc, table, title, strip });
    }
    host.append(area);

    /* The horizontal scrollbar of the tables: a real scrollbar, always
       visible under the tables, that drives them. The tables keep their
       own native scroll (hidden), so the keyboard and the trackpad work
       as usual; this one is the visible handle. */
    /* The scrollbar is drawn by hand: the native ones are hidden, and in
       Firefox the native ones hide themselves anyway, with a size nobody
       controls. */
    const hbar = document.createElement("div");
    hbar.className = "hbar";
    hbar.id = "hbar";
    hbar.tabIndex = 0;
    hbar.setAttribute("role", "scrollbar");
    hbar.setAttribute("aria-label", t("hbarLabel"));
    hbar.setAttribute("aria-controls", "table-scroll");
    hbar.setAttribute("aria-orientation", "horizontal");
    hbar.setAttribute("aria-valuemin", "0");
    hbar.setAttribute("aria-valuemax", "0");
    hbar.setAttribute("aria-valuenow", "0");
    const thumb = document.createElement("div");
    thumb.className = "hbar-thumb";
    hbar.append(thumb);
    host.append(hbar);

    /* dragging the thumb scrolls the tables */
    let thumbDrag = null;
    thumb.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      /* the pointer is captured: the drag goes on outside the bar */
      try { thumb.setPointerCapture(ev.pointerId); } catch (e) { /* no capture */ }
      thumbDrag = { x: ev.clientX, left: thumb.offsetLeft };
    });
    thumb.addEventListener("pointermove", (ev) => {
      if (!thumbDrag) return;
      const max = thumbTravel(thumb.offsetWidth);
      const left = Math.min(max, Math.max(0, thumbDrag.left + ev.clientX - thumbDrag.x));
      thumb.style.left = `${left}px`;
      const sc = document.querySelector(".table-scroll");
      if (sc) {
        /* the thumb's travel is the track (minus the pinned column), the
           table's travel is the scrollable width: the two are put in
           proportion */
        const range = scrollRange(sc);
        /* the same travel the cursor is clamped to: otherwise the table
           stops a couple of pixels short of the end */
        const travel = Math.max(1, thumbTravel(thumb.offsetWidth));
        const pos = Math.min(1, Math.max(0, left / travel));
        for (const b of built) if (b.sc) b.sc.scrollLeft = pos * range.total;
      }
    });
    const thumbEnd = () => { thumbDrag = null; };
    thumb.addEventListener("pointerup", thumbEnd);
    thumb.addEventListener("pointercancel", thumbEnd);

    /* the keyboard moves the tables */
    hbar.addEventListener("keydown", (ev) => {
      const sc = document.querySelector(".table-scroll");
      if (!sc) return;
      const step = 60;
      let d = 0;
      if (ev.key === "ArrowRight") d = step;
      else if (ev.key === "ArrowLeft") d = -step;
      else if (ev.key === "Home") { sc.scrollLeft = 0; ev.preventDefault(); return; }
      else if (ev.key === "End") { sc.scrollLeft = sc.scrollWidth; ev.preventDefault(); return; }
      else return;
      ev.preventDefault();
      for (const b of built) if (b.sc) b.sc.scrollLeft += d;
    });

    /* the bar is measured once the layout has settled, so that its sizes
       are right from the first frame */
    requestAnimationFrame(() => { syncHBarGeometry(); syncHBar(); });
    return { built };
  }

  /* How much of the table can be scrolled: the first column is pinned, so
     it does not scroll and does not count. Its width is known from the
     layout: measuring it here would force a reflow in the middle of the
     scroll, and the scroll would go in jerks. */
  let pinnedWidth = 0;

  function scrollRange(sc) {
    const total = Math.max(0, sc.scrollWidth - sc.clientWidth);
    const free = Math.max(1, total - pinnedWidth);
    return { total, free, pinnedW: pinnedWidth };
  }

  /* The width of the track: it is the width of the tables, and it is known
     even when the bar is not visible (a hidden fixed bar has no width). */
  let hbarTrack = 0;

  /* How far the cursor can travel: the inner width of the strip (its
     borders do not count), minus the cursor and a margin of one pixel on
     each side. With this the cursor never sticks out of the strip, it keeps
     a pixel of air on both ends, and the table can still be scrolled to the
     very end. */
  function thumbTravel(w) {
    return Math.max(0, barInner - w - 2 * thumbMargin);
  }

  /* The borders of the bar and the margin of the cursor: they do not
     change between two measurements, and measuring them costs a style
     recalculation. */
  let barInner = 0;
  let thumbMargin = 0;

  function measureBar() {
    const hbar = $("#hbar");
    const thumb = hbar && hbar.querySelector(".hbar-thumb");
    if (!hbar) return;
    const cs = getComputedStyle(hbar);
    barInner = Math.max(0, (hbarTrack || 0)
      - (parseFloat(cs.borderLeftWidth) || 0)
      - (parseFloat(cs.borderRightWidth) || 0));
    thumbMargin = thumb ? (parseFloat(getComputedStyle(thumb).marginLeft) || 0) : 0;
  }

  /* The external bar follows the tables: same width, same position, and
     it is only there while the tables are on screen. */
  function syncHBar() {
    const hbar = $("#hbar");
    if (!hbar) return;
    const sc = document.querySelector(".table-scroll");
    if (!sc) return;
    const range = scrollRange(sc);
    const thumb = hbar.querySelector(".hbar-thumb");
    if (thumb) {
      const w = range.total > 0
        ? Math.max(36, Math.round(hbarTrack * (sc.clientWidth / sc.scrollWidth)))
        : hbarTrack;
      thumb.style.width = `${w}px`;
      /* the thumb travels over the whole track, above every column */
      const travel = thumbTravel(w);
      const pos = range.total > 0 ? travel * (sc.scrollLeft / range.total) : 0;
      /* no rounding: a half pixel of error would put the cursor past the
         point it belongs to, and would make it jump when the tables are
         scrolled from elsewhere */
      thumb.style.left = `${pos}px`;
    }
    /* the ARIA values follow the scroll */
    hbar.setAttribute("aria-valuemax", String(Math.round(range.total)));
    hbar.setAttribute("aria-valuenow", String(Math.round(sc.scrollLeft)));
  }

  /* The bar itself follows the tables: same width, same position, and it
     is only there while the tables are on screen. Its place comes from the
     page, so it is measured when the page moves — not when the table
     scrolls sideways: there a measurement would force a reflow in the
     middle of the animation, and the scroll would go in jerks. */
  function syncHBarGeometry() {
    const hbar = $("#hbar");
    const area = document.querySelector(".table-area");
    if (!hbar || !area) return;
    const r = area.getBoundingClientRect();
    const vh = window.innerHeight;
    const left = Math.max(0, r.left);
    const track = Math.min(r.width, window.innerWidth - left);
    hbarTrack = track;
    hbar.style.left = `${left}px`;
    hbar.style.width = `${track}px`;
    measureBar();

    /* it is only there while the tables are on screen */
    const on = r.top < vh - 30;
    hbar.classList.toggle("hbar-on", on);
    if (!on) return;
    /* The bottom of the strip is the higher of the two: the foot of the
       window, or the foot of the table. While the table continues below,
       the strip stays on the window; as soon as the table ends, the strip
       hangs under its last row and goes up with it. */
    const gap = parseFloat(
      getComputedStyle(document.documentElement).getPropertyValue("--hbar-gap")) || 0;
    const offset = Math.max(0, vh - r.bottom) + gap;
    hbar.style.bottom = `${offset}px`;
    hbar.classList.toggle("hbar-attached", offset > 0);
  }

  /* The widths of the columns are measured once and then reused: measuring
   * them on every render would force a reflow of the whole table, which
   * costs two hundred milliseconds on the full list. They only change when
   * the language changes. */
  /* The width of the columns does not depend on the rows that happen to
     be on screen. The table of the matches has few rows: measuring there
     gave a column narrower than what the cells of the other tables need,
     and the content spilled out of the cell (the strip of the colour
     didn't fit). The width is computed from what a cell has to hold: the
     strip, the description of a reading, the label of the proportion. */
  function computeColumnWidths() {
    const root = getComputedStyle(document.documentElement);
    const name = parseFloat(root.getPropertyValue("--col-substance")) || 210;
    const cap = document.querySelector(".data-table .cell-cap, .data-table .cell-text");
    const strip = document.querySelector(".data-table .strip");
    const td = document.querySelector(".data-table td");
    const capMax = cap ? parseFloat(getComputedStyle(cap).maxWidth) : 108;
    const stripW = strip ? parseFloat(getComputedStyle(strip).width) : 84;
    /* The label of the proportion does not wrap, so it has to be the
       column that gives it room. The three labels are measured with the
       font of the cell: the widest one is the one in bold. */
    let labelW = 0;
    const prop = document.querySelector(".data-table .cell-prop");
    if (prop) {
      const cs = getComputedStyle(prop);
      const ctx = document.createElement("canvas").getContext("2d");
      ctx.font = `600 ${cs.fontSize} ${cs.fontFamily}`;
      /* the canvas does not know about the letter spacing: it is added
         by hand, or the measurement would be short */
      const spacing = parseFloat(cs.letterSpacing) || 0;
      for (const key of ["proportion.standard", "proportion.high", "proportion.low"]) {
        const text = t(key);
        labelW = Math.max(labelW, ctx.measureText(text).width + text.length * spacing);
      }
    }
    const pad = td
      ? parseFloat(getComputedStyle(td).paddingLeft) +
        parseFloat(getComputedStyle(td).paddingRight)
      : 12;
    return {
      name: Math.ceil(name),
      reading: Math.ceil(Math.max(stripW, capMax, labelW) + pad + 1),
    };
  }

  function lockColumnWidths(tables) {
    /* a group without rows (the empty "matches" section) has no table */
    const withRows = tables.filter((tb) => tb.table);
    if (!withRows.length) return;
    const { name, reading } = computeColumnWidths();
    /* the pinned column does not scroll: the bar of the scroll needs to
       know how wide it is */
    pinnedWidth = name;
    for (const { table } of withRows) {
      const head = table.querySelector("thead tr");
      const n = head ? head.cells.length : 1;
      const widths = [name, ...Array(Math.max(0, n - 1)).fill(reading)];
      let colgroup = table.querySelector("colgroup");
      if (!colgroup) {
        colgroup = document.createElement("colgroup");
        table.insertBefore(colgroup, table.firstChild);
      }
      colgroup.textContent = "";
      widths.forEach((w) => {
        const col = document.createElement("col");
        col.style.width = `${w}px`;
        colgroup.append(col);
      });
      table.classList.add("fixed-layout");
      table.style.width = `${widths.reduce((a, b) => a + b, 0)}px`;
    }
  }

  /* The groups scroll sideways together. */
  function syncScrollers(tables) {
    /* The scroll of a trackpad arrives in bursts, and the work is done
       once per frame: in the event handler it would fall in the middle
       of the animation, and the movement would go in jerks.

       Moving the other scrollers fires their own scroll event. It is
       recognised by the value — the one we imposed — and ignored: taken
       for a scroll of the reader, it would put the tables back where they
       were. */
    let scheduled = false;
    let source = null;
    let synced = 0;
    const onScroll = (ev) => {
      const sc = ev.target;
      if (sc.scrollLeft === synced) return;
      if (!source) source = sc;
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        const from = source;
        source = null;
        if (!from) return;
        synced = from.scrollLeft;
        for (const other of tables) {
          if (other.sc !== from && other.sc.scrollLeft !== synced) {
            other.sc.scrollLeft = synced;
          }
        }
        syncHeaderStrip();
        syncHBar();
      });
    };
    for (const { sc } of tables) {
      sc.addEventListener("scroll", onScroll, { passive: true });
    }
  }

  /* The column headers live in their own strip, inside the sticky block of
   * the group. The table keeps its own horizontal scroll, so the strip is
   * shifted sideways in sync with it. The widths come from the shared
   * colgroup, so the strip and the columns cannot drift apart. */
  function buildHeaderStrip(built) {
    for (const { table, strip } of built) {
      if (!table) continue;
      strip.textContent = "";
      const headRow = table.tHead?.rows[0];
      if (!headRow) continue;

      const cols = table.querySelector("colgroup")?.children;
      const widths = cols ? [...cols].map((c) => c.getBoundingClientRect().width) : [];
      if (!widths.length) continue;

      const pinned = document.createElement("div");
      pinned.className = "thead-pinned";
      const shifted = document.createElement("div");
      shifted.className = "thead-shifted";

      let acc = 0;
      [...headRow.cells].forEach((cell, i) => {
        const box = document.createElement("div");
        box.className = "thead-cell";
        box.style.width = `${widths[i]}px`;
        /* the nodes are copied, not the text: the coverage is a separate
           element and has to look like one */
        for (const node of cell.childNodes) box.append(node.cloneNode(true));
        /* the first column is pinned in the table body, so it is pinned here */
        if (i === 0) {
          box.style.left = "0px";
          pinned.append(box);
        } else {
          box.style.left = `${acc}px`;
          shifted.append(box);
        }
        acc += widths[i];
      });
      strip.append(pinned, shifted);
      /* The cells are absolutely positioned, so the strip has no height of
       * its own. The natural height is measured first (a cell with the name
       * and the coverage is taller than one with only the name), then every
       * cell is stretched to it. */
      const cellsOf = () => [...strip.querySelectorAll(".thead-cell")];
      for (const c of cellsOf()) c.style.height = "auto";
      const h = Math.max(...cellsOf().map((c) => c.offsetHeight), 28);
      strip.style.height = `${h}px`;
      for (const c of cellsOf()) c.style.height = "100%";
    }
    syncHeaderStrip();
    requestAnimationFrame(() => syncHeaderStrip());
  }

  /* The picker must stay inside the page: it opens where there is room,
   * flips above or to the side when there is not, and scrolls inside itself
   * when even that is not enough. */
  function placePopover(det) {
    const pop = det.querySelector(".picker-pop");
    if (!pop) return;
    pop.classList.remove("open-up");
    pop.style.maxHeight = "";
    pop.style.maxWidth = "";
    pop.style.left = "";
    pop.style.top = "";
    pop.style.bottom = "";

    const r = det.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    const w = pop.offsetWidth;
    const h = pop.offsetHeight;

    const below = vh - r.bottom - 10;
    const above = r.top - 10;
    const up = below < Math.min(h, 220) && above > below;
    const room = Math.max(140, up ? above : below);

    pop.style.maxHeight = `${room}px`;
    pop.style.overflowY = "auto";
    if (up) pop.classList.add("open-up");

    /* Sideways: the picker is never cut. It keeps the size it wants and
       slides along the button — the least it has to move to stay inside
       the window. Only when the window is narrower than that does it
       shrink, and then only to what the window has. */
    const spaceRight = vw - r.left - 10;
    const width = Math.min(w, Math.max(180, vw - 20));
    if (width < w) pop.style.maxWidth = `${width}px`;
    pop.style.left = `${Math.min(0, spaceRight - width)}px`;
  }

  function syncHeaderStrip() {
    const sc = $("#table-scroll");
    if (!sc) return;
    for (const bar of document.querySelectorAll(".thead-bar")) {
      const shifted = bar.querySelector(".thead-shifted");
      if (shifted) shifted.style.transform = `translateX(${-sc.scrollLeft}px)`;
    }
  }


  function renderTable() {
    /* the table is rebuilt from scratch: the sideways scroll has to be put
       back where it was */
    const keepScroll = document.querySelector(".table-scroll")?.scrollLeft || 0;
    const list = DATA.substances;
    const withObs = activeObservations().length > 0;

    let matched = [];
    let rest = [];
    if (withObs) {
      for (const s of list) {
        const ev = evaluate(s);
        if (ev.hits.length) matched.push({ s, ev });
        else rest.push(s);
      }
      /* How many tests the substance fits comes first: a substance that
         fits two of three tests is stronger evidence than one that fits
         only the first test, and the mask alone did not say so (with
         three tests, 100 came before 011). Then the mask, so that two
         substances that fit the same tests are next to each other, and
         then the name. Among the substances that fit as many tests, the
         ones where the user saw something no source documents come
         after. */
      matched.sort((a, b) => b.ev.hits.length - a.ev.hits.length ||
        a.ev.differences - b.ev.differences ||
        b.ev.mask - a.ev.mask ||
        a.s.name.localeCompare(b.s.name));
    } else {
      rest = list.slice().sort((a, b) =>
        typeOrder(a) - typeOrder(b) || a.name.localeCompare(b.name));
    }

    const groups = [];
    if (withObs) {
      /* The substances that fit every test, and the ones that fit only
       * some of them: the second list is what is left of the AND, and
       * telling the two apart is the point of several tests. */
      const nObs = activeObservations().length;
      const k = candidateThreshold(nObs);
      const total = matched.filter((m) => m.ev.hits.length === nObs);
      /* The partial matches are still candidates: they fit at least two
       * thirds of the tests, like the ones the panel of the next test
       * works on. The incongruent ones fit some tests but contradict
       * too many of them. */
      const partial = matched.filter((m) => m.ev.hits.length < nObs && m.ev.hits.length >= k);
      const incongruent = matched.filter((m) => m.ev.hits.length < k);
      const fewer = partial.length + incongruent.length;
      /* The total group is always there, even when it is empty: an empty
       * table section says "nothing matched" better than its absence. */
      groups.push({
        title: nObs > 1 ? t("matchesTotalTitle") : t("matchesTitle"),
        items: total,
        empty: total.length === 0,
        conflicts: DATA.substances.filter((s) => evaluate(s).conflicts).length,
        emptyText: nObs > 1 ? "matchesTotalEmptyText" : null,
        emptyExtra: fewer
          ? interpolate(t("matchesPartialEmptyHint"), { n: fewer })
          : null,
      });
      /* the other two are sections of their own, but only when there are
       * any: an empty section is noise */
      if (partial.length) {
        groups.push({
          title: t("matchesPartialTitle"),
          note: interpolate(t("matchesAtLeast"), { k, n: nObs }),
          items: partial,
        });
      }
      if (incongruent.length) {
        groups.push({
          title: t("matchesIncongruentTitle"),
          note: interpolate(t("matchesFewer"), { k, n: nObs }),
          items: incongruent,
        });
      }
    }
    if (rest.length) {
      /* the "other substances" title only makes sense when there is another
         group above it */
      groups.push({ title: withObs ? t("restTitle") : "", items: rest.map((s) => ({ s, ev: evaluate(s) })) });
    }

    const { built } = buildTable(groups);
    lockColumnWidths(built);
    syncScrollers(built);
    buildHeaderStrip(built);
    /* the table is new: the bar has to be measured again */
    syncHBarGeometry();
    syncHBar();
    /* and back where the reader had scrolled to */
    for (const { sc } of built) {
      if (sc) sc.scrollLeft = keepScroll;
    }
  }


  function typeOrder(s) {
    return { Substance: 0, Adulterant: 1, Class: 2, Forms: 3 }[s.info.type] ?? 4;
  }

  /* ── the next test to make ───────────────────────────────────────
     Which reagent tells the candidates apart most? The candidates are
     the substances that fit at least two thirds of the tests the reader
     has made: the ones that fit all of them, and the ones that fit most
     of them. The others are ruled out.

     For each other reagent the candidates are grouped by the answer the
     documentation gives — the colours it documents, or "nothing
     happens". The reader sees one colour, so the groups are counted per
     colour: a colour can be the answer of more than one documented
     trajectory. If the test is done and one colour comes out, only the
     candidates that document it survive; the candidates the reagent says
     nothing about survive whatever the answer is.

     The number shown is the average (how many are left on average) and
     the worst case (the biggest group): the order follows the average,
     and between two tests that are equally good the faster one comes
     first.

     The readings are taken at the recommended proportion: the next test
     is made with a new dose of the same substance. */
  /* The colours a cell documents at the recommended proportion: the set of
     answers the reader can give. "no reaction" is one of them, written
     as "~". Null when nobody documented the cell: the test cannot say
     anything about that substance. */
  function answerHues(readings, reagentId) {
    if (!readings) return null;
    const hues = new Set();
    for (const reading of readings) {
      if (levelOf(reading) !== "standard") continue;
      const colors = reactionColors(reading, reagentId);
      if (colors?.length === 0) hues.add("~");
      if (colors?.length) for (const color of colors) hues.add(hueOf(color));
    }
    return hues.size ? [...hues] : null;
  }

  /* The readings of a cell, as the panel writes them: the phases of a
     reading one after the other, with the arrow; the different readings
     separated by a comma, because they come from different sources and
     they do not necessarily agree. */
  function cellReadings(readings) {
    if (!readings) return [];
    const out = [];
    for (const reading of readings) {
      if (levelOf(reading) !== "standard") continue;
      /* the caption of the phases, on one line: the arrow keeps the
         phases together */
      const caption = isNoReaction(reading) ? t("noReaction")
        : isColour(reading) ? captionOf(reading.colors, state.lang).replace(/\n→ /g, " → ")
        : null;
      if (caption && !out.includes(caption)) out.push(caption);
    }
    return out;
  }

  /* How long a test takes, in seconds. It is the tie-breaker between two
     tests that are equally good: a test that answers in half a minute is
     better than one that takes five. A reagent with no time comes last. */
  function timingSeconds(r) {
    return r.duration ?? Infinity;
  }

  /* The time of a test, as the page writes it: "30 s", "5 min",
     "istantanea", and whether the sample has to be stirred. */
  function timingText(r) {
    if (r.duration == null) return "";
    const time = r.duration === 0 ? t("timingInstant")
      : r.duration < 60 ? `${r.duration} s` : `${Math.round(r.duration / 60)} min`;
    return r.stir ? `${time}, ${t("timingStir")}` : time;
  }

  /* The candidates: the substances that fit at least two thirds of the
     tests that have been made.

     The others are ruled out: with four tests, a substance that fits one
     of them is not a candidate any more. Counting it drowned the real
     ones in noise — most substances are documented for a single reagent,
     and they all entered the pool as soon as that reagent was used.

     The threshold is two thirds, rounded up: with three tests two are
     enough, with four three are. A pool can only shrink when a test is
     added, so the panel never loses its footing. */
  function candidatePool() {
    const n = activeObservations().length;
    const k = candidateThreshold(n);
    const pool = [];
    for (const s of DATA.substances) {
      const ev = evaluate(s);
      if (ev.hits.length >= k) pool.push({ s, ev });
    }
    return { n, k, pool };
  }

  /* how many tests a substance has to fit to stay a candidate */
  function candidateThreshold(n) {
    return Math.ceil((2 * n) / 3);
  }

  /* What a reagent would leave of the candidates.

     The reader looks at the test and sees one colour, not a trajectory:
     a colour can be the answer of more than one documented trajectory
     ("giallo → rosso" and "rosso" both end in red). The candidates are
     therefore counted per colour.

     The average is the expectation over the colour that comes out: every
     candidate is as likely as the others, and the colour it gives is one
     of the ones documented for it, each with the same probability. The
     worst case is the biggest group left. */
  function reagentOutcome(candidates, reagentId) {
    const sets = candidates.map((c) => answerHues(c.s.reactions[reagentId], reagentId));
    /* the candidates nobody documented: the test cannot rule them out */
    const uncovered = sets.filter((s) => s === null).length;
    const byColour = new Map();
    sets.forEach((set, i) => {
      if (!set) return;
      for (const hue of set) {
        if (!byColour.has(hue)) byColour.set(hue, []);
        byColour.get(hue).push(i);
      }
    });
    /* nobody documented this reagent for any candidate: the test says
       nothing at all */
    const n = candidates.length;
    if (!byColour.size) return { mean: n, worst: n };
    let sum = 0;
    let worst = uncovered;
    for (const idx of byColour.values()) {
      const left = uncovered + idx.length;
      let w = 0;
      for (const i of idx) w += 1 / sets[i].length;
      sum += w * left;
      worst = Math.max(worst, left);
    }
    /* The colour that comes out is one of the documented ones, and every
       candidate is as likely as the others: the sum of the weights is the
       number of candidates. The candidates nobody documented for this
       reagent cannot predict the colour: in that case only they are
       left, and the test rules the others out. */
    const mean = (sum + uncovered * uncovered) / n;
    return { mean, worst };
  }

  function nextTests() {
    const obs = activeObservations();
    if (!obs.length) return null;
    const { n, k, pool } = candidatePool();
    /* the reagents already used are not on offer: the reaction would be
       the one that has already been seen */
    const used = new Set(obs.map((o) => o.reagent));

    /* No substance is compatible: the colours that were described cannot
       go together. */
    if (!pool.length) {
      return { mode: "empty", n, k, total: DATA.substances.length };
    }

    /* One substance is compatible: there is nothing to tell apart, but
       there can be tests that would confirm it. */
    if (pool.length === 1) {
      const only = pool[0];
      const list = [];
      for (const r of DATA.reagents) {
        if (used.has(r.id)) continue;
        const readings = cellReadings(only.s.reactions[r.id]);
        if (!readings.length) continue;
        list.push({
          id: r.id, name: r.name, readings,
          cell: only.s.reactions[r.id],
          seconds: timingSeconds(r),
          timing: timingText(r),
        });
      }
      list.sort((a, b) => a.seconds - b.seconds || a.name.localeCompare(b.name));
      return { mode: "one", n, k, candidate: only.s, list };
    }

    const list = [];
    for (const r of DATA.reagents) {
      if (used.has(r.id)) continue;
      const { mean, worst } = reagentOutcome(pool, r.id);
      list.push({
        id: r.id, name: r.name, mean, worst,
        seconds: timingSeconds(r),
        timing: timingText(r),
      });
    }
    if (!list.length) return { mode: "flat", n, k, candidates: pool.length };
    list.sort((a, b) => a.mean - b.mean || a.worst - b.worst ||
      a.seconds - b.seconds || a.name.localeCompare(b.name));
    /* the list is worth showing only if some test can still tell the
       candidates apart */
    if (list[0].mean >= pool.length - 0.005) {
      return { mode: "flat", n, k, candidates: pool.length };
    }
    return { mode: "many", n, k, candidates: pool.length, list };
  }

  /* The row in progress takes the reagent that is chosen, and the colour
     picker opens on it. */
  function useReagent(reagentId) {
    const draft = [...state.observations].reverse().find((o) => !isActive(o));
    if (!draft) return;
    draft.reagent = reagentId;
    draft.auto = false;
    renderObservations();
    const dets = document.querySelectorAll("#obs-list .picker");
    const last = dets[dets.length - 1];
    if (!last) return;
    last.open = true;
    requestAnimationFrame(() => { if (last.open) placePopover(last); });
  }

  /* The button that adds the reagent to the observations. */
  function nextAddButton(r) {
    const add = document.createElement("button");
    add.type = "button";
    add.className = "btn next-add";
    add.textContent = t("nextAdd");
    /* on a narrow screen the button cannot afford the whole label:
       the short one is shown, the full one stays in the tooltip */
    add.dataset.short = t("nextAddShort");
    add.setAttribute("aria-label",
      interpolate(t("nextUse"), { reagent: r.name }));
    add.title = interpolate(t("nextUse"), { reagent: r.name });
    add.addEventListener("click", () => useReagent(r.id));
    return add;
  }

  /* The strips of a cell at the recommended proportion: the same strips
     the table draws, so that the card and the cell look alike. */
  function cardStrips(readings) {
    const wrap = document.createElement("div");
    wrap.className = "next-card-strips";
    const shown = new Set();
    for (const reading of readings) {
      if (levelOf(reading) !== "standard") continue;
      if (isNoReaction(reading)) {
        if (shown.has("~")) continue;
        shown.add("~");
        wrap.append(stripLine(null, t("noReaction")));
        continue;
      }
      if (!isColour(reading)) continue;
      const key = captionOf(reading.colors, "en");
      if (shown.has(key)) continue;
      shown.add(key);
      wrap.append(stripLine(cssGradient(stripOf(reading.colors)),
        captionOf(reading.colors, state.lang).replace(/\n→ /g, " → ")));
    }
    return wrap;
  }

  /* A strip of a reading and its caption. */
  function stripLine(background, caption) {
    const line = document.createElement("div");
    line.className = "reading-line";
    const strip = document.createElement("div");
    strip.className = background ? "strip" : "strip strip-empty";
    if (background) strip.style.background = background;
    const cap = document.createElement("span");
    cap.className = "next-card-cap";
    cap.textContent = caption;
    line.append(strip, cap);
    return line;
  }

  /* A card of the next test: the reagent, the time, what it tells
     apart, and the button that adds it to the observations. */
  function nextCard(r, first, useless) {
    const card = document.createElement("article");
    card.className = "next-card";
    if (first) card.classList.add("next-card-best");
    if (useless) card.classList.add("next-card-useless");

    const head = document.createElement("div");
    head.className = "next-card-head";
    const name = document.createElement("span");
    name.className = "next-card-name";
    name.textContent = r.name;
    /* the time, with a little clock: it says "how long it takes" at a
       glance, without taking the room of the name */
    const when = document.createElement("span");
    when.className = "next-card-when";
    const clock = clockIcon();
    const time = document.createElement("span");
    time.textContent = r.timing;
    when.append(clock, time);
    when.hidden = !r.timing;
    head.append(name, when);
    card.append(head);

    /* the body: the readings the test is expected to give when there is
       a single candidate, otherwise how many candidates are left */
    if (r.cell) {
      card.append(cardStrips(r.cell));
    } else {
      const num = document.createElement("div");
      num.className = "next-card-num";
      const mean = Math.max(1, Math.round(r.mean));
      const worst = Math.max(mean, Math.round(r.worst));
      const left = mean === worst ? `${mean}` : `${mean}–${worst}`;
      if (useless) {
        num.textContent = t("nextNone");
      } else {
        /* the label says what the number is: it does not reduce the
           candidates, it reduces the *possibilities* */
        const lbl = document.createElement("span");
        lbl.className = "next-card-lbl";
        lbl.textContent = t("nextReducesTo");
        const count = document.createElement("span");
        count.className = "next-card-count";
        count.textContent = left === "1"
          ? t("nextLeftOne")
          : interpolate(t("nextLeft"), { n: left });
        /* a range goes from the average to the worst case */
        if (mean !== worst) {
          count.title = interpolate(t("nextRange"), { mean, worst });
        }
        num.append(lbl, count);
      }
      card.append(num);
    }

    /* A test that rules nothing out is still worth adding: it may be the
       only one at hand, and recording it says something anyway. The card
       is muted, not disabled. */
    card.append(nextAddButton(r));
    return card;
  }

  /* What the panel was last built from: the completed tests and the
     language. The test in progress does not count, so choosing its reagent
     (or adding one from a card) does not rebuild the cards and their
     sideways scroll. */
  let nextTestsKey = null;

  function renderNextTests() {
    const box = $("#next-tests");
    if (!box) return;
    const key = `${state.lang}|${encodeState()}`;
    if (key === nextTestsKey) return;
    nextTestsKey = key;
    box.textContent = "";
    const data = nextTests();
    /* nothing can be told apart: the panel has nothing to say */
    if (!data || data.mode === "flat") { box.hidden = true; return; }
    box.hidden = false;

    const title = document.createElement("h3");
    title.className = "next-title";
    title.textContent = t("nextTitle");
    box.append(title);

    /* no substance is compatible, or only one: that needs a sentence */
    if (data.mode === "empty" || data.mode === "one") {
      const intro = document.createElement("p");
      intro.className = "next-intro";
      intro.textContent = data.mode === "empty"
        ? interpolate(t("nextEmpty"), { t: data.total })
        : interpolate(t("nextOne"), { name: data.candidate.name });
      box.append(intro);
      if (data.mode === "empty") return;
    }

    /* the cards: the first one is the best test */
    const row = document.createElement("div");
    row.className = "next-cards";
    /* the row scrolls sideways: it has to be reachable with the keyboard */
    row.tabIndex = 0;
    row.setAttribute("role", "group");
    row.setAttribute("aria-label", t("nextCardsLabel"));
    let first = true;
    for (const r of data.list) {
      const useless = r.cell ? false : r.mean >= data.candidates - 0.005;
      row.append(nextCard(r, first && !useless, useless));
      if (!useless) first = false;
    }
    box.append(row);
  }

  /* ── observations ─────────────────────────────────────────────── */

  /* The reagents that no *complete* observation is using yet. The row in
     progress does not hold one: its reagent is a suggestion, and any
     completed test may take it over — the row in progress then moves to
     the first one that is free. */
  function freeReagents(except) {
    const used = new Set(
      state.observations
        .filter((o) => o !== except && isActive(o))
        .map((o) => o.reagent));
    return DATA.reagents.filter((r) => !used.has(r.id));
  }

  /* There is always an incomplete row at the end of the list: it is where
     the next test is written. As soon as it is filled in, another one
     appears; when every reagent is used, no row is added. */
  function ensureDraft() {
    const last = state.observations[state.observations.length - 1];
    if (last && !isActive(last)) {
      /* The draft is there. Its reagent is offered automatically — the
         first one that is free — unless the reader has chosen one by
         hand. So the draft follows the free reagents: when a completed
         test has taken its reagent it moves, and when a test is deleted
         the reagent that has been freed comes back to it. */
      const free = freeReagents(last);
      const taken = !free.some((r) => r.id === last.reagent);
      if (free.length && (taken || (last.auto && free[0].id !== last.reagent))) {
        last.reagent = free[0].id;
      }
      return;
    }
    const free = freeReagents(null);
    if (!free.length) return;
    state.observations.push({
      id: Math.random().toString(36).slice(2),
      /* the first free reagent, in alphabetical order */
      reagent: free[0].id,
      /* the reagent was offered, not chosen: the draft keeps following
         the free ones until the reader picks one by hand */
      auto: true,
      noReaction: false,
      proportion: "standard",
      stages: [{ hue: null, modifier: null }],
    });
  }

  /* The "?" beside the proportion: what it is and why it matters. It is
     a picker like the colour one, so it opens on a click (a tooltip would
     not reach a phone) and closes the same way. */
  function proportionHelp() {
    const det = document.createElement("details");
    det.className = "picker";
    const sum = document.createElement("summary");
    sum.className = "help-btn";
    sum.textContent = "?";
    sum.setAttribute("aria-label", t("proportionHelpLabel"));
    const pop = document.createElement("div");
    pop.className = "picker-pop help-pop";
    for (const key of ["proportionHelpWhat", "proportionHelpWhy"]) {
      const paragraph = document.createElement("p");
      paragraph.textContent = t(key);
      pop.append(paragraph);
    }
    det.append(sum, pop);
    return det;
  }

  function renderObservations() {
    const list = $("#obs-list");
    list.textContent = "";
    ensureDraft();

    for (const obs of state.observations) {
      list.append(observationNode(obs));
    }
    renderBlindSpots();
    /* and the address bar is the link: it follows the observations */
    syncUrl();
    /* and the suggestion of the next test */
    renderNextTests();
    /* the link is worth copying only if there is something in it */
    $("#obs-share").hidden = !activeObservations().length;
  }

  function observationNode(obs) {
    const li = document.createElement("li");
    li.className = "obs";

    /* ── the head: the reagent, the time, the delete ── */
    const head = document.createElement("div");
    head.className = "obs-head";

    /* ── the reagent ── */
    const reagentWrap = document.createElement("div");
    reagentWrap.className = "obs-reagent";
    const sel = document.createElement("select");
    sel.setAttribute("aria-label", t("obsReagent"));
    /* one observation per reagent: the ones already used are not on
       offer */
    for (const r of freeReagents(obs)) {
      const opt = document.createElement("option");
      opt.value = r.id;
      opt.textContent = r.name;
      if (r.id === obs.reagent) opt.selected = true;
      sel.append(opt);
    }
    sel.addEventListener("change", () => {
      obs.reagent = sel.value;
      /* the reader has chosen this reagent: the row in progress stops
         following the free ones */
      obs.auto = false;
      renderObservations();
      renderTable();
    });
    reagentWrap.append(sel);

    /* the time of the test, with the little clock: the same sign as the
       cards of the next test */
    const when = document.createElement("span");
    when.className = "obs-when";
    when.append(clockIcon());
    const whenText = document.createElement("span");
    whenText.textContent = timingText(REAGENT_BY_ID[obs.reagent]);
    when.append(whenText);
    /* a reagent with no time documented shows no clock */
    when.hidden = !whenText.textContent;

    /* the time and the delete sit on the right, like in the cards of the
       next test */
    head.append(reagentWrap, when);
    li.append(head);

    /* ── the proportion of product to reagent ── */
    /* the label is written small and the select holds the short names:
       the tile does not grow, and the field still says what it is */
    const field = document.createElement("div");
    field.className = "obs-field";
    const propHead = document.createElement("div");
    propHead.className = "obs-field-head";
    const propLabel = document.createElement("label");
    propLabel.className = "obs-field-label";
    propLabel.textContent = t("obsProportionLabel");
    propLabel.htmlFor = `prop-${obs.id}`;
    propHead.append(propLabel, proportionHelp());
    const propWrap = document.createElement("div");
    propWrap.className = "obs-proportion";
    const prop = document.createElement("select");
    prop.id = `prop-${obs.id}`;
    for (const lv of PROPORTION_SCALE) {
      const opt = document.createElement("option");
      opt.value = lv;
      opt.textContent = t(`proportionShort.${lv}`);
      if (lv === (obs.proportion || "standard")) opt.selected = true;
      prop.append(opt);
    }
    prop.addEventListener("change", () => {
      obs.proportion = prop.value;
      renderTable();
      syncUrl();
    });
    propWrap.append(prop);
    field.append(propHead, propWrap);
    li.append(field);

    /* ── the phases of the reaction ── */
    const reactionField = document.createElement("div");
    reactionField.className = "obs-field";
    const reactionLabel = document.createElement("span");
    reactionLabel.className = "obs-field-label";
    reactionLabel.textContent = t("obsReactionLabel");
    const stagesWrap = document.createElement("div");
    stagesWrap.className = "obs-stages";
    reactionField.append(reactionLabel, stagesWrap);
    li.append(reactionField);

    function renderStages() {
      /* the picker is rebuilt: the overlay it owned has to go, or the plane
         would stay with nothing behind it */
      const wasOpen = [...stagesWrap.querySelectorAll(".picker")].findIndex((d) => d.open);
      hideOverlay();
      stagesWrap.textContent = "";

      /* A phase after the first comes with the arrow that leads into it,
         and the two wrap together: a line never starts with a colour cut
         off from its arrow, nor ends with an arrow that leads nowhere. */
      const arrow = () => {
        const sign = document.createElement("span");
        sign.className = "stage-arrow";
        sign.setAttribute("aria-hidden", "true");
        sign.textContent = "\u2192";
        return sign;
      };
      obs.stages.forEach((st, i) => {
        if (i === 0) {
          stagesWrap.append(stageNode(st, i));
          return;
        }
        const group = document.createElement("span");
        group.className = "stage-group";
        group.append(arrow(), stageNode(st, i));
        stagesWrap.append(group);
      });

      if (wasOpen >= 0) {
        const det = stagesWrap.querySelectorAll(".picker")[wasOpen];
        if (det) det.open = true;
      }

      syncUrl();
      /* The plus that adds another phase comes with its own arrow, and the
         two wrap together. Not when a phase is still waiting for a colour:
         that one is already a plus, and two side by side would be
         confusing. */
      const waiting = obs.stages.some((st) => !st.hue);
      if (!obs.noReaction && !waiting) {
        const tail = document.createElement("span");
        tail.className = "stage-group";
        const add = document.createElement("button");
        add.type = "button";
        add.className = "btn btn-quiet stage-add";
        add.textContent = "+";
        add.setAttribute("aria-label", t("obsAddStage"));
        add.addEventListener("click", () => {
          obs.stages.push({ hue: null, modifier: null });
          renderStages();
          /* the new phase opens right away: the point of the button is to
             choose the colour now, not to go and look for it */
          const dets = stagesWrap.querySelectorAll(".picker");
          const last = dets[dets.length - 1];
          if (!last) return;
          last.open = true;
          /* the panel may have moved while the phase was added: the
             popover is placed again once the layout has settled */
          requestAnimationFrame(() => {
            if (last.open) placePopover(last);
          });
        });
        tail.append(arrow(), add);
        stagesWrap.append(tail);
      }
    }

    function stageNode(st, index) {
      const span = document.createElement("span");
      span.className = "stage";

      const det = document.createElement("details");
      det.className = "picker";
      det.dataset.obs = obs.id;

      /* the choice is staged: the picker shows a preview and only writes it
       * when the colour is confirmed */
      let draft = { hue: st.hue, modifier: st.modifier, noReaction: obs.noReaction };

      const sum = document.createElement("summary");
      sum.className = "swatch-btn";
      const chip = document.createElement("span");
      chip.className = "swatch-chip";
      const label = document.createElement("span");

      function paint() {
        if (obs.noReaction) {
          chip.classList.add("swatch-chip-none");
          chip.style.background = "transparent";
          chip.style.display = "";
          label.textContent = t("obsNoReaction");
        } else if (!st.hue) {
          /* the phase with no colour yet is the dashed button with a
             plus: the same sign as the one that adds another phase */
          chip.style.display = "none";
          sum.classList.add("swatch-btn-plus");
          sum.setAttribute("aria-label", t("obsAddReaction"));
          label.textContent = "+";
        } else {
          chip.classList.remove("swatch-chip-none");
          chip.style.display = "";
          chip.style.background = hexFor(st.hue, st.modifier);
          label.textContent = colorName(`${st.hue}.${st.modifier || "standard"}`, state.lang);
        }
      }
      paint();

      sum.append(chip, label);
      det.append(sum);

      const pop = document.createElement("div");
      pop.className = "picker-pop";

      /* "no reaction" comes first, on its own, and can be clicked again to
         go back to the colours */
      const none = document.createElement("button");
      none.type = "button";
      none.className = "swatch swatch-none";
      const noneBox = document.createElement("span");
      noneBox.className = "box box-none";
      const noneLbl = document.createElement("span");
      noneLbl.className = "lbl";
      noneLbl.textContent = t("obsNoReaction");
      none.append(noneBox, noneLbl);
      none.addEventListener("click", () => {
        draft.noReaction = !draft.noReaction;
        none.setAttribute("aria-pressed", draft.noReaction ? "true" : "false");
        if (draft.noReaction) {
          for (const input of grid.querySelectorAll("input")) input.checked = false;
        }
        showChoice();
      });
      /* a reaction that already has a colour cannot turn into "no
         reaction": the choice is only there for the first phase */
      if (index === 0) pop.append(none);

      /* The colours: a grid of every hue in every shade, as the data has
         them. On a wide screen the hues are the columns and the shades the
         rows; on a phone the grid is turned, a hue per row with its name.
         Each swatch says where it goes, and the stylesheet places it. */
      const fs = document.createElement("fieldset");
      const legend = document.createElement("legend");
      legend.textContent = t("obsColour");
      fs.append(legend);
      const grid = document.createElement("div");
      grid.className = "color-grid";
      grid.style.setProperty("--hues", HUES.length);
      grid.style.setProperty("--shades", SHADES.length);
      SHADES.forEach((shade, shadeIndex) => {
        const name = document.createElement("span");
        name.className = "color-grid-shade";
        name.style.setProperty("--shade-index", shadeIndex);
        name.textContent = modifierName(shade, state.lang);
        grid.append(name);
      });
      HUES.forEach((hue, hueIndex) => {
        const name = document.createElement("span");
        name.className = "color-grid-hue";
        name.style.setProperty("--hue-index", hueIndex);
        name.textContent = hueName(hue, state.lang);
        grid.append(name);
        SHADES.forEach((shade, shadeIndex) => {
          const color = `${hue}.${shade}`;
          const cell = document.createElement("label");
          cell.className = "color-cell";
          cell.style.setProperty("--hue-index", hueIndex);
          cell.style.setProperty("--shade-index", shadeIndex);
          cell.title = colorName(color, state.lang);
          const input = document.createElement("input");
          input.type = "radio";
          input.name = `color-${obs.id}-${index}`;
          input.value = color;
          input.setAttribute("aria-label", colorName(color, state.lang));
          input.addEventListener("change", () => {
            draft.hue = hue;
            draft.modifier = shade;
            draft.noReaction = false;
            showChoice();
          });
          const box = document.createElement("span");
          box.className = "box";
          box.style.background = hexFor(hue, shade);
          cell.append(input, box);
          grid.append(cell);
        });
      });
      fs.append(grid);
      /* the name of the colour chosen: on a wide screen the grid has no
         room for the names of the hues */
      const choice = document.createElement("p");
      choice.className = "color-choice";
      choice.setAttribute("aria-live", "polite");
      fs.append(choice);
      pop.append(fs);
      pop.classList.add("color-pop");

      function showChoice() {
        none.setAttribute("aria-pressed", draft.noReaction ? "true" : "false");
        choice.textContent = draft.noReaction ? t("obsNoReaction")
          : draft.hue ? colorName(`${draft.hue}.${draft.modifier || "standard"}`, state.lang)
          : "";
      }
      syncControls();

      /* the buttons: delete on the left, then cancel and confirm */
      const actions = document.createElement("div");
      actions.className = "picker-actions";

      if (obs.stages.length > 1) {
        const del = document.createElement("button");
        del.type = "button";
        del.className = "picker-del";
        del.textContent = "\u2715";
        del.setAttribute("aria-label", t("obsRemoveStage"));
        del.addEventListener("click", () => {
          obs.stages.splice(index, 1);
          hideOverlay();
          renderStages();
          renderTable();
        });
        actions.append(del);
      }
      actions.append(Object.assign(document.createElement("span"), { className: "picker-sep" }));

      const cancel = document.createElement("button");
      cancel.type = "button";
      cancel.className = "picker-cancel";
      cancel.textContent = t("obsCancel");
      cancel.addEventListener("click", () => { det.open = false; });
      actions.append(cancel);

      const ok = document.createElement("button");
      ok.type = "button";
      ok.className = "picker-ok";
      ok.textContent = t("obsConfirm");
      ok.addEventListener("click", () => {
        st.hue = draft.hue;
        st.modifier = draft.modifier;
        obs.noReaction = draft.noReaction;
        det.open = false;
        /* the observation is now complete: a new empty row appears below */
        renderObservations();
        renderTable();
      });
      actions.append(ok);
      pop.append(actions);

      det.append(pop);
      span.append(det);

      /* The controls follow the draft. The draft is prepared when the
       * picker opens: the "toggle" event arrives too late and would wipe
       * a colour that was just picked. */
      function syncControls() {
        const chosen = draft.hue ? `${draft.hue}.${draft.modifier || "standard"}` : null;
        for (const input of grid.querySelectorAll("input")) {
          input.checked = !draft.noReaction && input.value === chosen;
        }
        showChoice();
      }

      sum.addEventListener("click", () => {
        if (!det.open) {
          draft = { hue: st.hue, modifier: st.modifier, noReaction: obs.noReaction };
          syncControls();
        }
      });

      return span;
    }


    renderStages();

    /* the incomplete tile is not deleted: it is where the next test
       goes, and it has no delete button */
    if (isActive(obs)) {
      const rm = document.createElement("button");
      rm.type = "button";
      rm.className = "btn btn-quiet obs-remove";
      rm.textContent = "\u2715";
      rm.setAttribute("aria-label", t("obsRemove"));
      rm.addEventListener("click", () => {
        state.observations = state.observations.filter((o) => o.id !== obs.id);
        renderObservations();
        renderTable();
      });
      head.append(rm);
    } else {
      li.classList.add("obs-draft");
    }

    return li;
  }



  /* ── popover ──────────────────────────────────────────────────── */

  function openPopover(ev, substance, reagentId) {
    const readings = substance.reactions[reagentId];
    const pop = $("#popover");
    const body = $("#popover-body");
    body.textContent = "";

    /* the title and the badge share a row: the badge is at the top right,
       aligned with the title */
    const head = document.createElement("div");
    head.className = "popover-head";
    const h = document.createElement("h3");
    h.className = "popover-title";
    h.textContent = `${substance.name} · ${reagentName(reagentId)}`;
    head.append(h);
    if (sourcesDisagree(readings, reagentId)) {
      const badge = document.createElement("span");
      badge.className = "badge badge-conflict";
      badge.textContent = t("disputed");
      head.append(badge);
    }
    body.append(head);

    body.append(sourceRows(readings));
    showPopover(ev);
  }

  /* The warnings of a reading that matches only in part: all of them, so
     that nothing has to be picked. The reading is the title — its strip
     and its colours — and the cell and the sources say where it comes
     from. */
  function openWarnings(ev, substance, reagentId, reading, sources, warnings) {
    const body = $("#popover-body");
    body.textContent = "";
    const head = document.createElement("div");
    head.className = "warning-head";
    const strip = document.createElement("div");
    strip.className = "strip";
    strip.style.background = cssGradient(stripOf(reading.colors));
    const title = document.createElement("h3");
    title.className = "popover-title";
    title.textContent = captionOf(reading.colors, state.lang).replace(/\n→ /g, " → ");
    head.append(strip, title);
    const context = document.createElement("p");
    context.className = "warning-context";
    context.textContent = [
      substance.name,
      reagentName(reagentId),
      sources.map((source) => DATA.sources[source]?.label ?? source).join(", "),
    ].join(" · ");
    const list = document.createElement("ul");
    list.className = "warning-list";
    /* what contradicts the documentation comes first */
    const ordered = [...warnings].sort((a, b) =>
      (b.kind === "difference") - (a.kind === "difference"));
    for (const warning of ordered) {
      const item = document.createElement("li");
      if (warning.kind === "difference") item.className = "warning-difference";
      item.append(interpolateStrong(t(warning.key), warning.vars));
      list.append(item);
    }
    body.append(head, context, list);
    showPopover(ev);
  }

  /* The popover is fixed: it opens next to the button that opened it, and
     stays inside the window. It starts from the left edge of the button,
     or ends at its right edge for a button in the right corner. */
  function showPopover(ev, { alignRight = false } = {}) {
    const pop = $("#popover");
    pop.hidden = false;
    lastFocused = ev.currentTarget;
    /* the popover is fixed, so the viewport rectangle can be used as it is */
    const r = ev.currentTarget.getBoundingClientRect();
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    let top = r.bottom + 6;
    if (top + pop.offsetHeight > vh - 8) top = Math.max(8, r.top - pop.offsetHeight - 6);
    let left = alignRight ? r.right - pop.offsetWidth : r.left;
    if (left + pop.offsetWidth > vw - 8) left = vw - pop.offsetWidth - 8;
    pop.style.top = `${Math.max(8, top)}px`;
    pop.style.left = `${Math.max(8, left)}px`;
    showOverlay(pop, () => {
      pop.hidden = true;
      lastFocused?.focus?.();
    });
    pop.querySelector("button, [tabindex]")?.focus?.();
  }

  function closePopover() {
    const pop = $("#popover");
    if (pop.hidden) return;
    pop.hidden = true;
    lastFocused?.focus?.();
  }

  /* ── overlays ──────────────────────────────────────────────────
   * Only one overlay is open at a time: the colour picker, the note about
   * the sources of a cell, the detail of a substance. A plane covers the
   * page while one is open, so a click outside closes it and the page
   * underneath does not react to the pointer. */
  let openOverlay = null;   // {el, close}

  function showOverlay(el, close) {
    if (openOverlay) {
      const previous = openOverlay;
      openOverlay = null;
      previous.close();
    }
    openOverlay = { el, close };
    $("#backdrop").hidden = false;
    lockScroll();
  }

  function hideOverlay() {
    if (!openOverlay) return;
    const overlay = openOverlay;
    openOverlay = null;
    $("#backdrop").hidden = true;
    unlockScroll();
    overlay.close();
  }

  /* while an overlay is open the page underneath does not scroll */
  function lockScroll() {
    const bar = window.innerWidth - document.documentElement.clientWidth;
    document.documentElement.style.overflow = "hidden";
    if (bar > 0) document.body.style.paddingRight = `${bar}px`;
  }

  function unlockScroll() {
    document.documentElement.style.overflow = "";
    document.body.style.paddingRight = "";
  }

  $("#backdrop").addEventListener("click", () => hideOverlay());

  /* the colour picker is a <details>: when it opens it becomes the
     overlay, and when it closes by itself the plane goes away too */
  document.addEventListener("toggle", (e) => {
    const det = e.target;
    if (!det.classList?.contains("picker")) return;
    if (det.open) {
      /* The overlay comes first: it takes the scrollbar away, and the
         page moves a few pixels when it does. The popover is placed
         after, when the layout is the final one. */
      showOverlay(det, () => { det.open = false; });
      placePopover(det);
    } else if (openOverlay && openOverlay.el === det) {
      /* the picker closed on its own: the plane and the scroll go back */
      openOverlay = null;
      $("#backdrop").hidden = true;
      unlockScroll();
    }
  }, true);

  document.addEventListener("scroll", () => closePopover(), true);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (openOverlay) { hideOverlay(); return; }
      if (!$("#detail").hidden) closeDetail();
    }
  });

  /* ── detail panel ─────────────────────────────────────────────── */

  /* The readings of a cell, source by source. Every source is listed,
     always: the ones with readings show all of them, the ones without say
     "nessun dato" — hiding a source would hide the fact that it was asked
     and had nothing to say. A reading at another proportion says which;
     the note of a source is written once, after its readings. */
  function sourceRows(readings) {
    const grid = document.createElement("div");
    grid.className = "detail-reagent";
    for (const key of Object.keys(DATA.sources)) {
      const fromSource = (readings || []).filter((reading) => reading.source === key);
      for (const reading of fromSource.length ? fromSource : [null]) {
        const row = document.createElement("div");
        row.className = reading ? "reading" : "reading reading-empty";
        const strip = document.createElement("div");
        if (reading && isColour(reading)) {
          strip.className = "strip";
          strip.style.background = cssGradient(stripOf(reading.colors));
        } else {
          /* the empty bar: a reading with no colour keeps the shape of a
             reading, so the descriptions stay in the same column */
          strip.className = "strip strip-empty";
        }
        row.append(strip);
        const cap = document.createElement("span");
        cap.className = reading ? "cap" : "cap cap-empty";
        let caption = !reading ? t("noData")
          : isColour(reading) ? captionOf(reading.colors, state.lang)
          : isNoReaction(reading) ? t("noReaction")
          : t("inconsistent");
        if (reading && levelOf(reading) !== "standard") {
          caption += ` · ${t(`proportion.${levelOf(reading)}`)}`;
        }
        if (reading) {
          for (const extra of readingExtras(reading)) caption += ` · ${extra}`;
        }
        cap.textContent = caption;
        row.append(cap);
        const src = document.createElement("span");
        src.className = "src";
        src.textContent = DATA.sources[key].label;
        row.append(src);
        grid.append(row);
      }
      const note = fromSource.find((reading) => reading.note)?.note;
      if (note) {
        const paragraph = document.createElement("p");
        paragraph.className = "reading-note";
        paragraph.textContent = noteText(note);
        grid.append(paragraph);
      }
    }
    return grid;
  }

  function openDetail(substance) {
    const panel = $("#detail");
    const body = $("#detail-body");
    $("#detail-title").textContent = substance.name;
    body.textContent = "";

    const meta = document.createElement("p");
    meta.className = "detail-meta";
    const bits = [typeName(substance.info.type)];
    if (substance.aliases?.length) bits.push(`${t("detailAliases")}: ${substance.aliases.join(", ")}`);
    meta.textContent = bits.join(" · ");
    body.append(meta);

    if (substance.info.wiki) {
      const a = document.createElement("a");
      a.href = substance.info.wiki;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = t("detailWiki");
      body.append(a);
    }

    /* One tab per reagent: the readings of that reagent, one row per
       source. */
    const tabs = document.createElement("div");
    tabs.className = "detail-tabs";
    tabs.setAttribute("role", "tablist");
    tabs.setAttribute("aria-label", t("detailReagents"));
    const panels = document.createElement("div");
    panels.className = "detail-panels";

    const buttons = [];
    DATA.reagents.forEach((r, i) => {
      const tab = document.createElement("button");
      tab.type = "button";
      tab.className = "detail-tab";
      tab.id = `detail-tab-${r.id}`;
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-controls", `detail-panel-${r.id}`);
      tab.setAttribute("aria-selected", i === 0 ? "true" : "false");
      tab.tabIndex = i === 0 ? 0 : -1;
      const name = document.createElement("span");
      name.textContent = r.name;
      tab.append(name);
      const small = document.createElement("small");
      small.textContent = `${r.known}/${r.total}`;
      tab.append(small);
      tabs.append(tab);
      buttons.push(tab);

      const pane = document.createElement("div");
      pane.className = "detail-panel";
      pane.id = `detail-panel-${r.id}`;
      pane.setAttribute("role", "tabpanel");
      pane.setAttribute("aria-labelledby", tab.id);
      pane.hidden = i !== 0;
      const readings = substance.reactions[r.id];
      pane.append(sourceRows(readings));
      if (readings && sourcesDisagree(readings, r.id)) {
        /* the badge is out of the grid of the readings: it sits at the
           bottom right of the card and takes its own space */
        const badge = document.createElement("span");
        badge.className = "detail-disputed";
        badge.textContent = t("disputed");
        pane.append(badge);
      }
      panels.append(pane);
    });

    /* the tabs behave like tabs: the arrows move, the space changes */
    const select = (i) => {
      buttons.forEach((b, j) => {
        b.setAttribute("aria-selected", j === i ? "true" : "false");
        b.tabIndex = j === i ? 0 : -1;
        panels.children[j].hidden = j !== i;
      });
      buttons[i].focus();
    };
    tabs.addEventListener("click", (ev) => {
      const b = ev.target.closest(".detail-tab");
      if (!b) return;
      select(buttons.indexOf(b));
    });
    tabs.addEventListener("keydown", (ev) => {
      const i = buttons.indexOf(document.activeElement);
      if (i < 0) return;
      let j = null;
      if (ev.key === "ArrowRight") j = (i + 1) % buttons.length;
      else if (ev.key === "ArrowLeft") j = (i - 1 + buttons.length) % buttons.length;
      else if (ev.key === "Home") j = 0;
      else if (ev.key === "End") j = buttons.length - 1;
      if (j === null) return;
      ev.preventDefault();
      select(j);
    });

    body.append(tabs, panels);

    panel.hidden = false;
    panel.focus();
    showOverlay(panel, () => { panel.hidden = true; });
  }

  function closeDetail() {
    $("#detail").hidden = true;
    /* the panel is an overlay: closing it has to take the backdrop and the
       scroll lock with it */
    hideOverlay();
    $("#detail-close").focus();
  }

  $("#detail-close").addEventListener("click", closeDetail);

  /* ── the sources section ──────────────────────────────────────── */

  /* The glossary of the reagents: what each one is for, how long it takes,
     how much data there is, and — where it is documented — what happens
     when the amount of product is not the usual one. */
  function renderReagents() {
    const ul = $("#reagent-list");
    ul.textContent = "";
    for (const r of DATA.reagents) {
      const li = document.createElement("li");
      li.className = "reagent-item";

      const head = document.createElement("div");
      head.className = "reagent-head";
      const name = document.createElement("span");
      name.className = "reagent-name";
      name.textContent = r.name;
      /* the time, with the same little clock as the tiles */
      const when = document.createElement("span");
      when.className = "next-card-when";
      const time = document.createElement("span");
      time.textContent = timingText(r);
      when.append(clockIcon(), time);
      when.hidden = !time.textContent;
      head.append(name, when);
      li.append(head);
      /* how many substances the sources document with this reagent */
      const coverage = document.createElement("p");
      coverage.className = "reagent-meta";
      coverage.textContent = interpolate(t("reagentCoverage"), { n: r.known, t: r.total });
      li.append(coverage);

      /* the description, in the chosen language, with where it comes from
         and whether it was translated: not every reagent has one */
      const description = DESCRIPTIONS.locales?.[state.lang]?.reagents[r.name];
      if (description) {
        const note = document.createElement("p");
        note.className = "reagent-note";
        note.textContent = description.description;
        li.append(note, sourceButton(r, description.source));
      }
      ul.append(li);
    }
  }

  /* "Source", at the foot of the card: it opens the popover with the link
     and whether the text was translated */
  function sourceButton(reagent, source) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "btn btn-quiet reagent-source";
    button.textContent = t("reagentSource");
    button.addEventListener("click", (ev) => openDescriptionSource(ev, reagent, source));
    return button;
  }

  function openDescriptionSource(ev, reagent, source) {
    const body = $("#popover-body");
    body.textContent = "";
    const title = document.createElement("h3");
    title.className = "popover-title";
    title.textContent = `${reagent.name} · ${t("reagentSource")}`;
    /* the main source, with its licence; the link is the exact place */
    const main = DESCRIPTIONS.sources?.[source.main];
    const mainLine = document.createElement("p");
    mainLine.className = "description-source";
    mainLine.textContent = main ? [main.label, main.license].join(" · ") : "";
    const link = document.createElement("a");
    link.href = source.href;
    link.target = "_blank";
    link.rel = "noopener";
    /* the address without the protocol, readable: "Simon's", not "Simon%27s" */
    link.textContent = decodeURI(source.href).replace(/^https?:\/\//, "");
    const linkLine = document.createElement("p");
    linkLine.className = "description-source";
    linkLine.append(link);
    const translation = document.createElement("p");
    translation.className = "description-source muted";
    translation.textContent = t(source.translated ? "reagentSourceTranslated" : "reagentSourceOriginal");
    body.append(title);
    if (main) body.append(mainLine);
    body.append(linkLine, translation);
    showPopover(ev);
  }

  /* The sources of the dataset, then those of the descriptions of the
     reagents, which are not in the dataset; the descriptions are one file,
     downloaded once for all of their sources. */
  function renderSources() {
    const ul = $("#source-list");
    ul.textContent = "";
    for (const src of Object.values(DATA.sources)) {
      ul.append(sourceItem(src));
    }
    for (const src of Object.values(DESCRIPTIONS.sources || {})) {
      ul.append(sourceItem(src));
    }
    const download = $("#descriptions-download");
    download.textContent = "";
    download.hidden = !DESCRIPTIONS.sources;
    if (DESCRIPTIONS.sources) download.append(descriptionsDownload());
  }

  function sourceItem(src) {
    const li = document.createElement("li");
    const name = document.createElement("div");
    name.className = "source-name";
    const a = document.createElement("a");
    a.href = src.url;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = src.label;
    name.append(a);
    li.append(name);
    const meta = document.createElement("div");
    meta.className = "source-meta";
    meta.textContent = [src.year, src.license].filter(Boolean).join(" · ");
    li.append(meta);
    return li;
  }

  /* The file is made from the descriptions the page has loaded: the
     single-file page has no data/ folder to link to. It is made once, and
     the link drawn again in the other language reuses it. The comment at
     the top of the original is not in the data: the licence is. */
  let descriptionsUrl = null;

  function descriptionsDownload() {
    if (!descriptionsUrl) {
      const content = `/* Licence: ${DESCRIPTIONS.license} */\n`
        + "window.DESCRIPTIONS = " + JSON.stringify(DESCRIPTIONS, null, 1) + ";\n";
      descriptionsUrl = URL.createObjectURL(new Blob([content], { type: "text/javascript" }));
    }
    const link = document.createElement("a");
    link.download = "descriptions.js";
    link.href = descriptionsUrl;
    link.textContent = t("descriptionsDownload");
    return link;
  }

  /* substances whose absence from the data is worth naming out loud:
     the ones a negative result must not be read as an all-clear */
  const NOTABLE = ["Fentanyl", "Synthetic opioids", "Levamisole", "PCP", "GHB"];

  /* The well-known substances the tests made cannot see: no data for any
     of the reagents used, so a negative result says nothing about them. */
  function renderBlindSpots() {
    const paragraph = $("#blind-spots");
    const missing = missingSubstances();
    const names = DATA.substances
      .filter((substance) => missing.has(substance.id) && NOTABLE.includes(substance.name))
      .map((substance) => substance.name);
    paragraph.hidden = !names.length;
    paragraph.textContent = names.length
      ? interpolate(t("blindSpots"), { names: names.join(", ") })
      : "";
  }

  /* ── language and theme ───────────────────────────────────────── */

  function applyStrings() {
    document.documentElement.lang = state.lang;
    for (const el of $$("[data-i18n]")) {
      const key = el.dataset.i18n;
      const value = t(key);
      if (typeof value === "string") {
        el.textContent = interpolate(value, { t: DATA.substances.length });
      }
    }
    $("#lang-toggle").textContent = STRINGS[state.lang].otherLang;
    $("#lang-toggle").setAttribute("aria-label",
      `${STRINGS[state.lang].otherLang} — ${STRINGS[state.lang].langName}`);
    $("#theme-toggle").setAttribute("aria-label", t("themeToggle"));
    $("#detail-close").setAttribute("aria-label", t("detailClose"));
    $("#banner-close").setAttribute("aria-label", t("bannerClose"));
    $("#banner-open").setAttribute("aria-label", t("bannerOpen"));
    /* the single-file page has no link to itself */
    const download = $("#bundle-link");
    if (download) download.title = t("downloadHint");
    $(".skip-link")?.setAttribute("href", "#table-scroll");
    const skip = document.querySelector(".skip-link");
    if (skip) skip.textContent = t("skip");
  }

  /* The warning is open in the card, or closed behind a "!" in its
     corner. */
  function renderBanner() {
    $("#banner").hidden = state.bannerClosed;
    $("#banner-open").hidden = !state.bannerClosed;
  }

  /* the same warning, in the popover */
  function openBanner(ev) {
    const body = $("#popover-body");
    body.textContent = "";
    const text = document.createElement("p");
    text.className = "popover-banner";
    text.textContent = t("banner");
    body.append(text);
    showPopover(ev, { alignRight: true });
  }

  function applyTheme() {
    document.documentElement.dataset.theme = state.theme;
    $("#theme-icon").textContent = state.theme === "dark" ? "☀" : "◐";
  }

  /* Dragging inside the table scrolls it, sideways and up and down, the
   * way a finger would. Only with the mouse: with the finger the browser
   * already scrolls, and taking it over would break the gesture. The
   * buttons and the links keep their own behaviour. */
  let drag = null;
  let lastDrag = 0;

  /* Is the pointer on the scrollbar of the scroller?
     The browser has to handle the scrollbar alone: in Firefox it is
     drawn on top of the content, so the click reaches the element and
     would start a drag that goes the opposite way — and the pointer
     capture would steal the click from the scrollbar itself. */
  function overScrollbar(sc, ev) {
    if (!sc) return false;
    /* a scroller with no scrollbar has nothing to avoid */
    const cs = getComputedStyle(sc);
    if (cs.scrollbarWidth === "none") return false;
    const r = sc.getBoundingClientRect();
    /* the classic scrollbar takes its space: the band is exact. The
       overlay one takes none: a band of twelve pixels is guessed. */
    const barH = sc.offsetHeight - sc.clientHeight;
    const barW = sc.offsetWidth - sc.clientWidth;
    const h = barH > 0 ? barH : 12;
    const w = barW > 0 ? barW : 12;
    /* the horizontal scrollbar, at the bottom */
    if (ev.clientY >= r.bottom - h && ev.clientX >= r.left && ev.clientX <= r.right) {
      return true;
    }
    /* the vertical one, on the side: only if the scroller can scroll
       vertically, otherwise that edge is ordinary content */
    if (cs.overflowY !== "hidden" &&
        ev.clientX >= r.right - w && ev.clientY >= r.top && ev.clientY <= r.bottom) {
      return true;
    }
    return false;
  }

  function initDrag() {
    /* the tables and the cards of the next test are both scrollers that
       can be dragged with the mouse */
    const hosts = [$("#tables"), $("#next-tests")].filter(Boolean);
    const onDown = (ev) => {
      /* Only with the mouse. With a finger the browser does the scrolling:
         it has the inertia, and it locks the axis of the gesture (one
         swipe, one direction) — which is how every touch screen works.
         Worse, when it starts the pan it cancels the pointer, so a drag
         of our own would die half way through. */
      if (ev.pointerType !== "mouse" || ev.button !== 0) return;
      /* the scrollbar has its own drag: it must not drag the table too */
      if (ev.target.closest(".hbar")) return;
      if (ev.target.closest("button, a, input, select, textarea, summary")) return;
      /* The scroller under the pointer. In the tables, the titles and the
         header strip drag the table too; in the panel of the next test only
         the row of cards scrolls, and elsewhere the text is just text. */
      const sc = ev.target.closest(".next-cards")
        || ev.target.closest(".table-scroll")
        || (ev.target.closest("#tables") ? document.querySelector(".table-scroll") : null);
      if (!sc) return;
      /* a click on the scrollbar belongs to the scrollbar */
      if (overScrollbar(sc, ev)) return;
      drag = {
        x: ev.clientX, y: ev.clientY,
        sy: window.scrollY,
        /* the starting position of the scroll: the new one is computed
           from it, so the content follows the pointer exactly */
        sl: sc ? sc.scrollLeft : 0,
        sc,
        moved: false,
      };
      /* the pointer is captured: the drag goes on even outside the table
         and even outside the window */
      try { ev.target.setPointerCapture(ev.pointerId); } catch (e) { /* no capture */ }
      document.body.classList.add("dragging");
    };
    const onMove = (ev) => {
      if (!drag) return;
      const dx = ev.clientX - drag.x;
      const dy = ev.clientY - drag.y;
      if (!drag.moved) {
        if (Math.abs(dx) + Math.abs(dy) < 4) return;
        drag.moved = true;
      }
      /* vertical: the page follows the pointer */
      window.scrollTo(window.scrollX, drag.sy - dy);
      /* horizontal: the content follows the pointer */
      if (drag.sc) drag.sc.scrollLeft = drag.sl - dx;
    };
    const end = () => {
      if (!drag) return;
      if (drag.moved) lastDrag = Date.now();
      document.body.classList.remove("dragging");
      drag = null;
    };
    /* a drag is not a click: the first click after it is swallowed */
    const swallow = (ev) => {
      if (Date.now() - lastDrag < 250) {
        ev.preventDefault();
        ev.stopPropagation();
      }
    };
    for (const host of hosts) {
      host.addEventListener("pointerdown", onDown);
      host.addEventListener("pointermove", onMove);
      host.addEventListener("pointerup", end);
      host.addEventListener("pointercancel", end);
      host.addEventListener("click", swallow, true);
    }
  }

  /* ── boot ─────────────────────────────────────────────────────── */

  function init() {
    $("#lang-toggle").addEventListener("click", () => {
      state.lang = state.lang === "it" ? "en" : "it";
      applyStrings();
      renderReagents();
      renderSources();
      renderObservations();
      renderTable();
    });
    $("#theme-toggle").addEventListener("click", () => {
      state.theme = state.theme === "light" ? "dark" : "light";
      try { localStorage.setItem("theme", state.theme); } catch (e) { /* no storage */ }
      applyTheme();
    });
    $("#banner-close").addEventListener("click", () => {
      state.bannerClosed = true;
      try { localStorage.setItem("bannerClosed", "1"); } catch (e) { /* no storage */ }
      renderBanner();
      $("#banner-open").focus();
    });
    $("#banner-open").addEventListener("click", openBanner);
    /* Copying the address is copying the link: the observations are in
       the fragment. The clipboard is not always there (a page opened from
       the disk, an old browser), so there is a fallback. */
    let shareTimer = null;
    $("#obs-share").addEventListener("click", async () => {
      const btn = $("#obs-share");
      const url = location.href;
      let done = false;
      try {
        await navigator.clipboard.writeText(url);
        done = true;
      } catch (e) {
        const ta = document.createElement("textarea");
        ta.value = url;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.top = "0";
        ta.style.opacity = "0";
        document.body.append(ta);
        ta.select();
        try { done = document.execCommand("copy"); } catch (e2) { done = false; }
        ta.remove();
      }
      if (!done) return;
      btn.textContent = t("obsShareDone");
      clearTimeout(shareTimer);
      shareTimer = setTimeout(() => { btn.textContent = t("obsShare"); }, 2200);
    });
    /* The table is rebuilt, so the sideways scroll has to be put back where
       it was; and the rebuild waits for the resizing to settle. The width of
       the columns does not depend on the window (they are measured from the
       content), so there is nothing to measure again. */
    let resizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const open = document.querySelector(".picker[open]");
        if (open) {
          placePopover(open);
        } else {
          renderTable();
        }
        syncHBarGeometry();
        syncHBar();
      }, 140);
    });
    /* the bar under the tables follows the page */
    /* the page moves: the bar has to follow it. The cursor of the bar
       does not move: the table has not scrolled sideways. */
    window.addEventListener("scroll", () => { syncHBarGeometry(); }, { passive: true });
    /* A link pasted in the address bar of an open page has to work: when
       the fragment changes and it is not our own change, the observations
       are read again. */
    window.addEventListener("hashchange", () => {
      if (location.hash.replace(/^#/, "") === encodeState()) return;
      loadFromUrl();
      applyStrings();
      renderObservations();
      renderTable();
    });
    /* the link may carry the observations: they are read before the
       first render, and the page starts with them already there */
    loadFromUrl();
    applyTheme();
    applyStrings();
    renderBanner();
    initDrag();
    renderReagents();
    renderObservations();
    renderTable();
    renderSources();
  }

  init();

})();
