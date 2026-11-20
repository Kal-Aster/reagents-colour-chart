/* Colour helpers.
 *
 * The colours come from the data: its palette names the hues, the shades
 * of each hue and their hex. A colour in a reading is written
 * "hue.shade" — "purple.dark". Every swatch is always accompanied by its
 * name.
 */

const PALETTE = window.REAGENTS.palette;

/* the hues and the shades the data knows, in the order of its palette */
const HUES = Object.keys(PALETTE);
const SHADES = Object.keys(PALETTE[HUES[0]].shades);

const HUE_IT = {
  white: "bianco", gray: "grigio", black: "nero",
  red: "rosso", orange: "arancione", yellow: "giallo",
  olive: "oliva", green: "verde", blue: "blu",
  purple: "viola", pink: "rosa", brown: "marrone",
};

const SHADE_IT = { light: "chiaro", standard: "medio", dark: "scuro" };

const HUE_EN = {
  white: "white", gray: "grey", black: "black",
  red: "red", orange: "orange", yellow: "yellow",
  olive: "olive", green: "green", blue: "blue",
  purple: "purple", pink: "pink", brown: "brown",
};

const SHADE_EN = { light: "light", standard: "medium", dark: "dark" };

/* The grays are a scale from grey to black: each shade has its own name,
   and the darkest one is black. */
const GRAY_IT = { light: "grigio", standard: "grigio scuro", dark: "nero" };
const GRAY_EN = { light: "grey", standard: "dark grey", dark: "black" };

function hueName(hue, lang) {
  return (lang === "en" ? HUE_EN : HUE_IT)[hue] ?? hue;
}

function modifierName(shade, lang) {
  if (!shade) return "";
  return (lang === "en" ? SHADE_EN : SHADE_IT)[shade] ?? shade;
}

/* "purple.dark" -> "purple" and "dark" */
function hueOf(color) {
  return color.split(".")[0];
}

function shadeOf(color) {
  return color.split(".")[1] || "standard";
}

function hexFor(hue, shade) {
  const shades = (PALETTE[hue] || PALETTE[HUES[0]]).shades;
  return shades[shade || "standard"] || shades.standard;
}

function hexOfColor(color) {
  return hexFor(hueOf(color), shadeOf(color));
}

/* The strip of a reading: its colours, left to right, in equal parts. */
function stripOf(colors) {
  return colors.map(hexOfColor);
}

function cssGradient(hexes) {
  if (!hexes || !hexes.length) return "transparent";
  if (hexes.length === 1) return hexes[0];
  const step = 100 / (hexes.length - 1);
  return `linear-gradient(to right, ${hexes
    .map((h, i) => `${h} ${(i * step).toFixed(1)}%`)
    .join(", ")})`;
}

/* The name of one colour. The standard shade is the colour itself; the
   grays have a name for each shade. */
function colorName(color, lang) {
  const hue = hueOf(color);
  const shade = shadeOf(color);
  if (hue === "gray") return (lang === "en" ? GRAY_EN : GRAY_IT)[shade] ?? hueName(hue, lang);
  if (shade === "standard") return hueName(hue, lang);
  return `${hueName(hue, lang)} ${modifierName(shade, lang)}`;
}

/* A readable caption for the colours of a reading, in the requested
   language. */
function captionOf(colors, lang) {
  /* Every phase on its own line, the arrow at the beginning of the
     next one: in a narrow cell the sequence is read downwards, and a
     line that breaks in the middle of the arrow is unreadable. */
  return colors.map((color) => colorName(color, lang)).join("\n→ ");
}

/* classic script: the page has to work when opened straight from disk,
   where ES modules are blocked by the browser's same-origin rules */
window.Colors = {
  HUES, SHADES,
  hueOf, shadeOf, hexFor, stripOf, cssGradient, colorName, captionOf, hueName, modifierName,
};
