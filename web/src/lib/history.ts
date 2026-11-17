/**
 * Local-first history: results are stored in this browser's IndexedDB only.
 * No audio is ever stored, here or on the server.
 */

import { type DBSchema, type IDBPDatabase, openDB } from "idb";

import type { Ayah, Candidate, IdentifyResponse, ReciterResult } from "./api";
import { daysAgo } from "./time";

export interface HistoryEntry {
  id: string;
  createdAt: number;
  status: "match" | "ambiguous";
  ayah: Ayah;
  textConfidence: number;
  candidates: Candidate[];
  repeatedCount: number | null;
  reciter: ReciterResult | null;
  saved: boolean;
  /** Set when the user corrected or supplied the reciter's name. */
  userReciter?: { id: string; name_ar: string };
}

interface AnsitDB extends DBSchema {
  history: { key: string; value: HistoryEntry; indexes: { createdAt: number } };
}

const DB_NAME = "ansit";
let dbPromise: Promise<IDBPDatabase<AnsitDB>> | null = null;

function db(): Promise<IDBPDatabase<AnsitDB>> {
  dbPromise ??= openDB<AnsitDB>(DB_NAME, 1, {
    upgrade(database) {
      const store = database.createObjectStore("history", { keyPath: "id" });
      store.createIndex("createdAt", "createdAt");
    },
  });
  return dbPromise;
}

/** For tests: forget the cached connection. */
export function resetHistoryConnection(): void {
  dbPromise = null;
}

/** Turn a successful identify response into a history entry. Null for no_match. */
export function entryFromResponse(
  response: IdentifyResponse,
  now: number = Date.now(),
): HistoryEntry | null {
  if (response.status === "no_match" || !response.ayah) return null;
  return {
    id: response.id,
    createdAt: now,
    status: response.status,
    ayah: response.ayah,
    textConfidence: response.text_confidence ?? 0,
    candidates: response.candidates,
    repeatedCount: response.repeated_count,
    reciter: response.reciter,
    saved: false,
  };
}

export async function putEntry(entry: HistoryEntry): Promise<void> {
  await (await db()).put("history", entry);
}

export async function getEntry(id: string): Promise<HistoryEntry | undefined> {
  return (await db()).get("history", id);
}

/** Newest first. */
export async function listEntries(): Promise<HistoryEntry[]> {
  const all = await (await db()).getAllFromIndex("history", "createdAt");
  return all.reverse();
}

export async function latestEntry(): Promise<HistoryEntry | undefined> {
  const cursor = await (
    await db()
  )
    .transaction("history")
    .store.index("createdAt")
    .openCursor(null, "prev");
  return cursor?.value;
}

export async function updateEntry(
  id: string,
  change: Partial<HistoryEntry>,
): Promise<HistoryEntry | undefined> {
  const database = await db();
  const current = await database.get("history", id);
  if (!current) return undefined;
  const next = { ...current, ...change, id };
  await database.put("history", next);
  return next;
}

export async function clearHistory(): Promise<void> {
  await (await db()).clear("history");
}

export type HistoryFilter = "all" | "today" | "week" | "saved";

/** The reciter name shown for an entry, or null when unknown. */
export function reciterName(entry: HistoryEntry): string | null {
  if (entry.userReciter) return entry.userReciter.name_ar;
  if (entry.reciter?.status === "identified") return entry.reciter.name_ar;
  return null;
}

export function filterEntries(
  entries: HistoryEntry[],
  filter: HistoryFilter,
  query: string,
  now: number = Date.now(),
): HistoryEntry[] {
  const needle = query.trim();
  return entries.filter((entry) => {
    if (filter === "saved" && !entry.saved) return false;
    if (filter === "today" && daysAgo(entry.createdAt, now) !== 0) return false;
    if (filter === "week" && daysAgo(entry.createdAt, now) > 6) return false;
    if (!needle) return true;
    const haystack = [
      entry.ayah.surah_name_ar,
      entry.ayah.surah_name_en.toLowerCase(),
      reciterName(entry) ?? "",
    ].join(" ");
    return haystack.includes(needle) || haystack.includes(needle.toLowerCase());
  });
}

/** Group newest-first entries by calendar day, keeping the order. */
export function groupByDay(
  entries: HistoryEntry[],
): { day: number; entries: HistoryEntry[] }[] {
  const groups: { day: number; entries: HistoryEntry[] }[] = [];
  for (const entry of entries) {
    const date = new Date(entry.createdAt);
    date.setHours(0, 0, 0, 0);
    const day = date.getTime();
    const last = groups[groups.length - 1];
    if (last && last.day === day) last.entries.push(entry);
    else groups.push({ day, entries: [entry] });
  }
  return groups;
}
