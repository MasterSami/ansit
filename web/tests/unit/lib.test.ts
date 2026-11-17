import "fake-indexeddb/auto";

import { beforeEach, describe, expect, it } from "vitest";

import {
  ayahAudioUrl,
  errorKindForStatus,
  fileNameFor,
  type IdentifyResponse,
} from "@/lib/api";
import {
  clearHistory,
  entryFromResponse,
  filterEntries,
  getEntry,
  groupByDay,
  type HistoryEntry,
  latestEntry,
  listEntries,
  putEntry,
  reciterName,
  updateEntry,
} from "@/lib/history";
import {
  ayahCount,
  formatElapsed,
  formatPercent,
  otherPlaces,
  repeatedTimes,
  toArabicDigits,
} from "@/lib/numerals";
import { levelsFromSpectrum, micFailure, pickMimeType } from "@/lib/recorder";
import { initials } from "@/lib/text";
import { clockTime, dayLabel, daysAgo, relativeTime } from "@/lib/time";

// Placeholder text only: real Quran text always comes from the API.
const PLACEHOLDER = "نص تجريبي";

function response(overrides: Partial<IdentifyResponse> = {}): IdentifyResponse {
  return {
    id: "id-1",
    status: "match",
    reason: null,
    ayah: {
      surah: 67,
      surah_name_ar: "الملك",
      surah_name_en: "Al-Mulk",
      ayah: 1,
      text_uthmani: PLACEHOLDER,
      juz: 29,
      page: 562,
      revelation: "meccan",
      ayah_count: 30,
    },
    text_confidence: 0.96,
    candidates: [],
    repeated_count: null,
    reciter: {
      status: "identified",
      id: "alafasy",
      name_ar: "مشاري العفاسي",
      name_en: "Mishary Alafasy",
      style: "murattal",
      similarity: 0.82,
      alternatives: [],
    },
    ...overrides,
  };
}

function entry(
  id: string,
  createdAt: number,
  change: Partial<HistoryEntry> = {},
): HistoryEntry {
  return { ...entryFromResponse(response({ id }), createdAt)!, ...change };
}

describe("numerals", () => {
  it("converts digits and leaves other characters alone", () => {
    expect(toArabicDigits(562)).toBe("٥٦٢");
    expect(toArabicDigits("1:05")).toBe("١:٠٥");
  });

  it("formats percentages and clamps them", () => {
    expect(formatPercent(0.96)).toBe("٩٦٪");
    expect(formatPercent(1.4)).toBe("١٠٠٪");
    expect(formatPercent(-1)).toBe("٠٪");
  });

  it("formats elapsed seconds", () => {
    expect(formatElapsed(6.4)).toBe("٠:٠٦");
    expect(formatElapsed(75)).toBe("١:١٥");
  });

  it("uses the right Arabic noun form for each count", () => {
    expect(ayahCount(1)).toBe("آية واحدة");
    expect(ayahCount(2)).toBe("آيتان");
    expect(ayahCount(7)).toBe("٧ آيات");
    expect(ayahCount(30)).toBe("٣٠ آية");
    expect(otherPlaces(1)).toBe("موضع واحد آخر");
    expect(otherPlaces(5)).toBe("٥ مواضع أخرى");
    expect(otherPlaces(28)).toBe("٢٨ موضعًا آخر");
    expect(repeatedTimes(2)).toBe("تتكرر مرتين");
    expect(repeatedTimes(31)).toBe("تتكرر ٣١ مرة");
  });
});

describe("time", () => {
  const now = new Date(2026, 10, 17, 15, 0).getTime();

  it("describes elapsed time in Arabic", () => {
    expect(relativeTime(now - 10_000, now)).toBe("الآن");
    expect(relativeTime(now - 10 * 60_000, now)).toBe("منذ ١٠ دقائق");
    expect(relativeTime(now - 2 * 3_600_000, now)).toBe("منذ ساعتين");
    expect(relativeTime(now - 3 * 86_400_000, now)).toBe("منذ ٣ أيام");
  });

  it("formats 12-hour clock times", () => {
    expect(clockTime(new Date(2026, 10, 17, 14, 40).getTime())).toBe("٢:٤٠ م");
    expect(clockTime(new Date(2026, 10, 17, 0, 5).getTime())).toBe("١٢:٠٥ ص");
  });

  it("counts calendar days, not 24-hour spans", () => {
    const lateYesterday = new Date(2026, 10, 16, 23, 59).getTime();
    expect(daysAgo(lateYesterday, now)).toBe(1);
    expect(dayLabel(now, now)).toBe("اليوم");
    expect(dayLabel(lateYesterday, now)).toBe("أمس");
    expect(dayLabel(new Date(2026, 10, 14, 9).getTime(), now)).toBe(
      "١٤ نوفمبر",
    );
  });
});

describe("api helpers", () => {
  it("maps HTTP statuses to UI failures", () => {
    expect(errorKindForStatus(429)).toBe("rate_limited");
    expect(errorKindForStatus(413)).toBe("bad_audio");
    expect(errorKindForStatus(422)).toBe("bad_audio");
    expect(errorKindForStatus(503)).toBe("busy");
    expect(errorKindForStatus(500)).toBe("server");
  });

  it("fills per-ayah audio templates", () => {
    expect(ayahAudioUrl("https://x/{sss}{aaa}.mp3", 2, 255)).toBe(
      "https://x/002255.mp3",
    );
  });

  it("names the upload after its container", () => {
    expect(fileNameFor("audio/webm;codecs=opus")).toBe("clip.webm");
    expect(fileNameFor("audio/mp4")).toBe("clip.m4a");
    expect(fileNameFor("")).toBe("clip.bin");
  });
});

describe("recorder helpers", () => {
  it("picks the first supported container", () => {
    expect(pickMimeType((type) => type === "audio/mp4")).toBe("audio/mp4");
    expect(pickMimeType(() => false)).toBe("");
  });

  it("classifies microphone errors", () => {
    expect(micFailure(new DOMException("no", "NotAllowedError"))).toBe(
      "denied",
    );
    expect(micFailure(new DOMException("no", "NotFoundError"))).toBe(
      "unavailable",
    );
    expect(micFailure("weird")).toBe("unavailable");
  });

  it("turns a spectrum into bounded bar levels", () => {
    const silent = levelsFromSpectrum(new Uint8Array(128), 8);
    const loud = levelsFromSpectrum(new Uint8Array(128).fill(255), 8);
    expect(silent).toEqual(Array(8).fill(0));
    expect(loud).toEqual(Array(8).fill(1));
  });
});

describe("text", () => {
  it("builds initials without honorifics or the definite article", () => {
    expect(initials("محمد صديق المنشاوي")).toBe("م ص");
    expect(initials("الشيخ عبد الباسط")).toBe("ع ب");
    expect(initials("الحصري")).toBe("ح");
  });
});

describe("history", () => {
  beforeEach(async () => {
    await clearHistory();
  });

  it("does not create entries for no_match", () => {
    expect(
      entryFromResponse(response({ status: "no_match", ayah: null })),
    ).toBeNull();
  });

  it("stores, lists newest first, updates and clears", async () => {
    await putEntry(entry("a", 1_000));
    await putEntry(entry("b", 2_000));
    expect((await listEntries()).map((e) => e.id)).toEqual(["b", "a"]);
    expect((await latestEntry())?.id).toBe("b");

    const updated = await updateEntry("a", { saved: true });
    expect(updated?.saved).toBe(true);
    expect((await getEntry("a"))?.saved).toBe(true);
    expect(await updateEntry("missing", { saved: true })).toBeUndefined();

    await clearHistory();
    expect(await listEntries()).toEqual([]);
  });

  it("stores no audio and no transcript", async () => {
    await putEntry(entry("a", 1_000));
    const stored = (await getEntry("a")) as unknown as Record<string, unknown>;
    expect(Object.keys(stored).sort()).toEqual(
      [
        "ayah",
        "candidates",
        "createdAt",
        "id",
        "reciter",
        "repeatedCount",
        "saved",
        "status",
        "textConfidence",
      ].sort(),
    );
  });

  it("prefers the name the user supplied", () => {
    const unknown = entry("a", 1, {
      reciter: { ...response().reciter!, status: "unknown", name_ar: null },
    });
    expect(reciterName(unknown)).toBeNull();
    expect(
      reciterName({ ...unknown, userReciter: { id: "x", name_ar: "الحصري" } }),
    ).toBe("الحصري");
    expect(reciterName(entry("b", 1))).toBe("مشاري العفاسي");
  });

  it("filters by day, saved state and search text", () => {
    const now = new Date(2026, 10, 17, 15, 0).getTime();
    const today = entry("today", now - 3_600_000);
    const lastWeek = entry("week", now - 3 * 86_400_000, { saved: true });
    const old = entry("old", now - 20 * 86_400_000);
    const all = [today, lastWeek, old];

    expect(filterEntries(all, "all", "", now)).toHaveLength(3);
    expect(filterEntries(all, "today", "", now).map((e) => e.id)).toEqual([
      "today",
    ]);
    expect(filterEntries(all, "week", "", now).map((e) => e.id)).toEqual([
      "today",
      "week",
    ]);
    expect(filterEntries(all, "saved", "", now).map((e) => e.id)).toEqual([
      "week",
    ]);
    expect(filterEntries(all, "all", "الملك", now)).toHaveLength(3);
    expect(filterEntries(all, "all", "MULK", now)).toHaveLength(3);
    expect(filterEntries(all, "all", "العفاسي", now)).toHaveLength(3);
    expect(filterEntries(all, "all", "البقرة", now)).toHaveLength(0);
  });

  it("groups consecutive entries by calendar day", () => {
    const day1 = new Date(2026, 10, 17, 15).getTime();
    const day0 = new Date(2026, 10, 16, 9).getTime();
    const groups = groupByDay([
      entry("a", day1),
      entry("b", day1 - 60_000),
      entry("c", day0),
    ]);
    expect(groups.map((g) => g.entries.map((e) => e.id))).toEqual([
      ["a", "b"],
      ["c"],
    ]);
  });
});
