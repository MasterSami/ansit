// Copies the ayahs quoted in the interface from the Tanzil Uthmani text into
// src/data/verses.json, so no Quran text is ever typed by hand.
// Usage: node scripts/make-verses.mjs   (needs ml/data/tanzil, see `make data`)
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const WANTED = [{ key: "listen", surah: 7, ayah: 204 }];

const source = fileURLToPath(
  new URL("../../ml/data/tanzil/quran-uthmani.txt", import.meta.url),
);
const lines = readFileSync(source, "utf8").split("\n");
const verses = {};
for (const { key, surah, ayah } of WANTED) {
  const line = lines.find((l) => l.startsWith(`${surah}|${ayah}|`));
  if (!line) throw new Error(`ayah ${surah}:${ayah} not found in ${source}`);
  verses[key] = { surah, ayah, text: line.split("|")[2].trim() };
}
const out = fileURLToPath(new URL("../src/data/verses.json", import.meta.url));
writeFileSync(out, `${JSON.stringify(verses, null, 2)}\n`);
console.log(
  `wrote ${Object.keys(verses).length} verse(s) to src/data/verses.json`,
);
