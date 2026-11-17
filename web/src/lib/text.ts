/** Small text helpers for names and labels. */

import type { Style } from "./api";

const HONORIFICS = new Set(["شيخ", "الشيخ", "بن", "ابن"]);

/**
 * Initials for the avatar (no reciter photos, by design): the first letters of
 * the first two name words, e.g. "محمد صديق المنشاوي" -> "م ص".
 */
export function initials(name: string): string {
  const words = name
    .trim()
    .split(/\s+/)
    .filter((word) => word && !HONORIFICS.has(word));
  const letters = words.slice(0, 2).map((word) => {
    const bare = word.replace(/^ال/, "");
    return (bare || word).charAt(0);
  });
  return letters.join(" ");
}

export const STYLE_TAB: Record<Style, string> = {
  murattal: "المرتّل",
  mujawwad: "المجوّد",
  muallim: "المعلّم",
};

export const STYLE_RECITATION: Record<Style, string> = {
  murattal: "تلاوة مرتّلة",
  mujawwad: "تلاوة مجوّدة",
  muallim: "المصحف المعلّم",
};

export const REVELATION: Record<"meccan" | "medinan", string> = {
  meccan: "مكية",
  medinan: "مدنية",
};
