/**
 * Reciter profiles: everything about a reciter that the recognition registry
 * does not hold. The content lives in `src/data/reciter-profiles.json`, so
 * biographies and portraits can be edited without touching any component.
 *
 * Every fact in a profile must come from a listed source. A field with no
 * source is left out, and the interface simply does not show it.
 */

import data from "@/data/reciter-profiles.json";

export type ReciterCategory =
  | "egyptian-classical"
  | "egyptian-contemporary"
  | "haram-makkah"
  | "haram-madinah"
  | "international";

export interface LifeEvent {
  year: number;
  /** ISO date, only when the full date is documented. */
  date?: string | null;
  place_ar?: string | null;
}

export interface ReciterProfile {
  /** The registry id for recognised reciters; a slug for directory entries. */
  id: string;
  /** False for reciters that are listed but not in the recognition registry. */
  in_registry: boolean;
  name_ar: string;
  name_en: string;
  /** A fuller form of the name than the registry's, when one is established. */
  full_name_ar?: string;
  country_ar?: string;
  country_en?: string;
  category?: ReciterCategory;
  portrait?: {
    src: string;
    credit: string | null;
    source_url: string | null;
    license?: string | null;
  };
  short_bio_ar?: string;
  /** Paragraphs of the full biography. */
  bio_ar?: string[];
  born?: LifeEvent;
  died?: LifeEvent;
  milestones_ar?: string[];
  sources?: { title: string; url: string }[];
  /** For directory entries: a published recording outside the app. */
  external_audio?: string;
}

export const PROFILES = data as ReciterProfile[];

const BY_ID = new Map(PROFILES.map((profile) => [profile.id, profile]));

export function getProfile(id: string): ReciterProfile | undefined {
  return BY_ID.get(id);
}

export const CATEGORIES: { id: ReciterCategory; label: string }[] = [
  { id: "egyptian-classical", label: "أعلام التلاوة المصرية" },
  { id: "egyptian-contemporary", label: "قرّاء مصر المعاصرون" },
  { id: "haram-makkah", label: "أئمة المسجد الحرام" },
  { id: "haram-madinah", label: "أئمة المسجد النبوي" },
  { id: "international", label: "قرّاء من العالم" },
];

export function categoryLabel(category?: ReciterCategory): string | null {
  return CATEGORIES.find((c) => c.id === category)?.label ?? null;
}

export function displayName(profile: ReciterProfile): string {
  return profile.full_name_ar ?? profile.name_ar;
}

/** Fold the spelling differences that should not matter when searching. */
export function normalizeArabic(text: string): string {
  return text
    .replace(/[ً-ٰٟـ]/g, "") // diacritics and tatweel
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

/** True when every word of the query appears in the Arabic or English name. */
export function matchesQuery(profile: ReciterProfile, query: string): boolean {
  const words = normalizeArabic(query).split(" ").filter(Boolean);
  if (words.length === 0) return true;
  const haystack = normalizeArabic(
    [
      profile.name_ar,
      profile.full_name_ar ?? "",
      profile.name_en,
      profile.country_ar ?? "",
      profile.country_en ?? "",
    ].join(" "),
  ).replace(/\bال/g, "");
  return words.every((word) => haystack.includes(word.replace(/^ال/, "")));
}

/** "١٩٢٧ – ١٩٨٨", "وُلد ١٩٦٠", or null when neither year is documented. */
export function lifespan(
  profile: ReciterProfile,
  digits: (n: number) => string,
): string | null {
  const born = profile.born?.year;
  const died = profile.died?.year;
  if (born && died) return `${digits(born)} – ${digits(died)}`;
  if (born) return `وُلد ${digits(born)}`;
  if (died) return `توفي ${digits(died)}`;
  return null;
}

/** Other reciters of the same category, most documented first. */
export function relatedProfiles(
  profile: ReciterProfile,
  limit = 4,
): ReciterProfile[] {
  if (!profile.category) return [];
  return PROFILES.filter(
    (other) => other.id !== profile.id && other.category === profile.category,
  )
    .sort(
      (a, b) =>
        Number(Boolean(b.portrait)) - Number(Boolean(a.portrait)) ||
        Number(Boolean(b.short_bio_ar)) - Number(Boolean(a.short_bio_ar)),
    )
    .slice(0, limit);
}
