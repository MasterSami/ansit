"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import {
  filterEntries,
  groupByDay,
  type HistoryEntry,
  type HistoryFilter,
  listEntries,
  reciterName,
} from "@/lib/history";
import { toArabicDigits } from "@/lib/numerals";
import { clockTime, dayLabel } from "@/lib/time";

import { BottomNav } from "./BottomNav";
import { BookmarkIcon, HistoryIcon, SearchIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { PrimaryLink, Screen, Skeleton, StateMessage } from "./ui";

const FILTERS: HistoryFilter[] = ["all", "today", "week", "saved"];

function isFilter(value: string | null): value is HistoryFilter {
  return FILTERS.includes(value as HistoryFilter);
}

export function HistoryScreen() {
  const t = useTranslations();
  const router = useRouter();
  const param = useSearchParams().get("filter");
  const filter: HistoryFilter = isFilter(param) ? param : "all";
  const [entries, setEntries] = useState<HistoryEntry[] | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    listEntries().then(setEntries, () => setEntries([]));
  }, []);

  const groups = useMemo(
    () => groupByDay(filterEntries(entries ?? [], filter, query)),
    [entries, filter, query],
  );
  const savedTab = filter === "saved";

  return (
    <Screen>
      <header className="flex flex-col gap-4 px-5 pt-14">
        <h1 className="text-[28px] font-bold">
          {savedTab ? t("history.savedTitle") : t("history.title")}
        </h1>
        <label className="flex h-12 items-center gap-2.5 rounded-full border border-border bg-surface px-4 text-muted focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-accent">
          <SearchIcon size={18} />
          <span className="sr-only">{t("history.searchLabel")}</span>
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t("history.searchPlaceholder")}
            className="min-w-0 grow bg-transparent text-[15px] text-text outline-none placeholder:text-muted"
          />
        </label>
        <div
          role="tablist"
          aria-label={t("history.filters")}
          className="flex gap-2 overflow-x-auto"
        >
          {FILTERS.map((id) => {
            const on = id === filter;
            return (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={on}
                onClick={() =>
                  router.replace(
                    id === "all" ? "/history" : `/history?filter=${id}`,
                  )
                }
                className={`h-11 shrink-0 rounded-full border px-3.5 text-[13px] font-semibold whitespace-nowrap ${
                  on
                    ? "border-accent bg-accent text-on-accent"
                    : "border-border bg-surface text-text"
                }`}
              >
                {t(`history.${id}`)}
              </button>
            );
          })}
        </div>
      </header>

      <main className="flex grow flex-col gap-2 px-5 pt-[18px] pb-3">
        {entries === null ? (
          <>
            <Skeleton className="h-[72px]" />
            <Skeleton className="h-[72px]" />
            <Skeleton className="h-[72px]" />
          </>
        ) : groups.length === 0 ? (
          <EmptyState
            hasAny={entries.length > 0}
            saved={savedTab}
            searching={query.trim() !== ""}
          />
        ) : (
          groups.map((group) => (
            <section
              key={group.day}
              className="flex flex-col gap-2 pt-1 first:pt-0"
            >
              <h2 className="text-[13px] font-semibold text-muted">
                {dayLabel(group.day)}
              </h2>
              {group.entries.map((entry) => (
                <HistoryRow key={entry.id} entry={entry} />
              ))}
            </section>
          ))
        )}
      </main>

      <PlayerBar />
      <BottomNav current={savedTab ? "saved" : "history"} />
    </Screen>
  );
}

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const t = useTranslations();
  const name = reciterName(entry);
  return (
    <Link
      href={`/result?id=${entry.id}`}
      className="flex items-center gap-3.5 rounded-[18px] border border-border bg-surface px-3.5 py-3"
    >
      <div
        aria-hidden="true"
        className="flex h-[46px] w-[46px] shrink-0 items-center justify-center rounded-[14px] bg-accent-soft font-display text-lg font-bold text-accent"
      >
        {toArabicDigits(entry.ayah.surah)}
      </div>
      <div className="flex min-w-0 grow flex-col gap-0.5">
        <span className="truncate text-[15px] font-semibold">
          {t("home.surahAyah", {
            surah: entry.ayah.surah_name_ar,
            ayah: toArabicDigits(entry.ayah.ayah),
          })}
        </span>
        <span
          className={`truncate text-[13px] ${name ? "text-muted" : "text-warning"}`}
        >
          {name ?? t("history.unknown")}
        </span>
      </div>
      <span className="flex shrink-0 items-center gap-1.5 text-xs text-muted">
        {entry.saved && (
          <BookmarkIcon size={14} filled className="text-accent" />
        )}
        {clockTime(entry.createdAt)}
      </span>
    </Link>
  );
}

function EmptyState({
  hasAny,
  saved,
  searching,
}: {
  hasAny: boolean;
  saved: boolean;
  searching: boolean;
}) {
  const t = useTranslations("history");
  // Something exists but the search or the date filter hides it.
  if (hasAny && (searching || !saved)) {
    return (
      <StateMessage
        icon={<SearchIcon size={38} />}
        title={t("noResultsTitle")}
        body={t("noResultsBody")}
      />
    );
  }
  return (
    <StateMessage
      icon={saved ? <BookmarkIcon size={38} /> : <HistoryIcon size={38} />}
      title={saved ? t("emptySavedTitle") : t("emptyTitle")}
      body={saved ? t("emptySavedBody") : t("emptyBody")}
    >
      {!saved && (
        <div className="w-full max-w-[260px]">
          <PrimaryLink href="/listen">{t("startListening")}</PrimaryLink>
        </div>
      )}
    </StateMessage>
  );
}
