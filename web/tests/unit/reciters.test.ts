import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { toArabicDigits } from "@/lib/numerals";
import {
  CATEGORIES,
  getProfile,
  lifespan,
  matchesQuery,
  normalizeArabic,
  PROFILES,
  relatedProfiles,
} from "@/lib/reciterProfiles";

const registry = JSON.parse(
  readFileSync(
    fileURLToPath(
      new URL("../../../ml/registry/reciters.json", import.meta.url),
    ),
    "utf8",
  ),
) as { id: string }[];

describe("reciter profiles data", () => {
  it("has exactly one profile for every reciter in the registry", () => {
    const ids = PROFILES.map((profile) => profile.id);
    expect(new Set(ids).size).toBe(ids.length);
    const missing = registry.filter((r) => !getProfile(r.id)).map((r) => r.id);
    expect(missing).toEqual([]); // run `node scripts/sync-reciter-profiles.mjs`
  });

  it("marks registry membership truthfully", () => {
    const inRegistry = new Set(registry.map((r) => r.id));
    for (const profile of PROFILES) {
      expect([profile.id, profile.in_registry]).toEqual([
        profile.id,
        inRegistry.has(profile.id),
      ]);
    }
  });

  it("never states a fact without a source", () => {
    const known = new Set(CATEGORIES.map((c) => c.id));
    for (const profile of PROFILES) {
      const hasFacts =
        profile.short_bio_ar ||
        profile.bio_ar?.length ||
        profile.born ||
        profile.died ||
        profile.milestones_ar?.length ||
        profile.country_ar ||
        profile.category;
      if (hasFacts) {
        expect(profile.sources?.length, profile.id).toBeGreaterThan(0);
      }
      for (const source of profile.sources ?? []) {
        expect(source.url, profile.id).toMatch(/^https:\/\//);
        expect(source.title.trim(), profile.id).not.toBe("");
      }
      if (profile.category) expect(known.has(profile.category)).toBe(true);
      if (profile.born && profile.died) {
        expect(profile.died.year, profile.id).toBeGreaterThan(
          profile.born.year,
        );
      }
      if (profile.portrait) {
        expect(profile.portrait.src, profile.id).toMatch(/^https:\/\//);
      }
    }
  });
});

describe("reciter search", () => {
  const husary = getProfile("husary")!;

  it("ignores diacritics, hamza forms and the definite article", () => {
    expect(normalizeArabic("الْقُرْآن")).toBe("القران");
    expect(matchesQuery(husary, "الحصري")).toBe(true);
    expect(matchesQuery(husary, "حصرى")).toBe(true);
    expect(matchesQuery(husary, "محمود الحصري")).toBe(true);
  });

  it("searches English names too, in any letter case", () => {
    expect(matchesQuery(husary, "hussary")).toBe(true);
    expect(matchesQuery(husary, "MAHMOUD")).toBe(true);
  });

  it("requires every word and rejects other reciters", () => {
    expect(matchesQuery(husary, "محمود المنشاوي")).toBe(false);
    expect(matchesQuery(husary, "")).toBe(true);
  });
});

describe("profile helpers", () => {
  it("formats a lifespan only from documented years", () => {
    const base = { id: "x", in_registry: false, name_ar: "أ", name_en: "A" };
    expect(lifespan(base, toArabicDigits)).toBeNull();
    expect(
      lifespan(
        { ...base, born: { year: 1920 }, died: { year: 1969 } },
        toArabicDigits,
      ),
    ).toBe("١٩٢٠ – ١٩٦٩");
    expect(lifespan({ ...base, born: { year: 1960 } }, toArabicDigits)).toBe(
      "وُلد ١٩٦٠",
    );
  });

  it("relates reciters of the same category only", () => {
    const profile = getProfile("minshawi")!;
    const related = relatedProfiles(profile);
    expect(related.length).toBeGreaterThan(0);
    for (const other of related) {
      expect(other.category).toBe(profile.category);
      expect(other.id).not.toBe(profile.id);
    }
  });
});
