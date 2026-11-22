// Keeps src/data/reciter-profiles.json in step with the reciter registry.
//
// The registry (ml/registry/reciters.json) is the source of truth for who the
// app can recognise. This file holds what the registry does not: portraits,
// categories, biographies and their sources, plus "directory" reciters that
// are listed but not recognised.
//
// This script only ADDS: a registry reciter with no profile gets an empty one.
// It never removes a profile and never overwrites a field someone filled in.
// Usage: node scripts/sync-reciter-profiles.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const path = (p) => fileURLToPath(new URL(p, import.meta.url));
const registry = JSON.parse(
  readFileSync(path("../../ml/registry/reciters.json"), "utf8"),
);
const target = path("../src/data/reciter-profiles.json");
let profiles = [];
try {
  profiles = JSON.parse(readFileSync(target, "utf8"));
} catch {
  // first run
}
const known = new Set(profiles.map((p) => p.id));
let added = 0;
for (const r of registry) {
  if (known.has(r.id)) continue;
  profiles.push({
    id: r.id,
    in_registry: true,
    name_ar: r.name_ar,
    name_en: r.name_en,
  });
  added += 1;
}
writeFileSync(target, `${JSON.stringify(profiles, null, 2)}\n`);
console.log(`${profiles.length} profiles (${added} added)`);
