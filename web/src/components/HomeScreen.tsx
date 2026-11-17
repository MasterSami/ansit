"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useState, useSyncExternalStore } from "react";

import { type HistoryEntry, latestEntry, reciterName } from "@/lib/history";
import { toArabicDigits } from "@/lib/numerals";
import { relativeTime } from "@/lib/time";

import { BottomNav } from "./BottomNav";
import { MicIcon, PlayIcon, SettingsIcon, WifiOffIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { IconLink, Screen, Skeleton } from "./ui";

function subscribeOnline(callback: () => void): () => void {
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

/** True while the browser reports no network. */
export function useOffline(): boolean {
  return useSyncExternalStore(
    subscribeOnline,
    () => !navigator.onLine,
    () => false,
  );
}

export function HomeScreen() {
  const t = useTranslations();
  const offline = useOffline();
  const [latest, setLatest] = useState<HistoryEntry | null | undefined>(
    undefined,
  );

  useEffect(() => {
    latestEntry().then(
      (entry) => setLatest(entry ?? null),
      () => setLatest(null),
    );
  }, []);

  return (
    <Screen>
      <header className="flex items-center justify-between px-6 pt-14">
        <div className="flex flex-col gap-0.5">
          <span className="font-display text-[34px] leading-[1.1] font-bold text-accent">
            {t("app.name")}
          </span>
          <span className="text-[13px] text-muted">{t("app.verse")}</span>
        </div>
        <IconLink href="/settings" label={t("home.settings")}>
          <SettingsIcon />
        </IconLink>
      </header>

      {offline && (
        <p
          role="status"
          className="mx-6 mt-4 flex items-center gap-2 rounded-2xl bg-warning-bg px-4 py-2.5 text-[13px] text-warning"
        >
          <WifiOffIcon size={16} />
          {t("offline.banner")}
        </p>
      )}

      <main className="flex grow flex-col items-center justify-center gap-7 px-6 py-6">
        <div className="relative flex h-[272px] w-[272px] items-center justify-center">
          <div
            aria-hidden="true"
            className="ansit-ring-2 absolute inset-0 rounded-full border border-[rgb(var(--accent-rgb)/0.22)]"
          />
          <div
            aria-hidden="true"
            className="ansit-ring absolute inset-[30px] rounded-full border border-[rgb(var(--accent-rgb)/0.35)] bg-[rgb(var(--accent-rgb)/0.06)]"
          />
          <Link
            href="/listen"
            aria-label={t("home.tapToListen")}
            className="relative flex h-[168px] w-[168px] items-center justify-center rounded-full bg-accent text-on-accent shadow-[0_0_0_10px_rgb(var(--accent-rgb)/0.12)]"
          >
            <MicIcon size={64} strokeWidth={1.6} />
          </Link>
        </div>
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-bold">{t("home.tapToListen")}</h1>
          <p className="max-w-[280px] text-[15px] text-muted">
            {t("home.subtitle")}
          </p>
        </div>
      </main>

      <section
        aria-label={t("home.lastHeard")}
        className="flex flex-col gap-2.5 px-6 pb-5"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted">
            {t("home.lastHeard")}
          </h2>
          <Link
            href="/history"
            className="flex min-h-11 items-center text-[13px] font-medium text-accent"
          >
            {t("home.showHistory")}
          </Link>
        </div>
        {latest === undefined ? (
          <Skeleton className="h-[78px]" />
        ) : latest === null ? (
          <p className="rounded-[18px] border border-border bg-surface px-4 py-3.5 text-[13px] text-muted">
            {t("home.nothingYet")}
          </p>
        ) : (
          <Link
            href={`/result?id=${latest.id}`}
            className="flex items-center gap-3.5 rounded-[18px] border border-border bg-surface px-4 py-3.5"
          >
            <div
              aria-hidden="true"
              className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[14px] bg-accent-soft font-display text-xl font-bold text-accent"
            >
              {toArabicDigits(latest.ayah.surah)}
            </div>
            <div className="flex min-w-0 grow flex-col gap-0.5">
              <span className="truncate text-base font-semibold">
                {t("home.surahAyah", {
                  surah: latest.ayah.surah_name_ar,
                  ayah: toArabicDigits(latest.ayah.ayah),
                })}
              </span>
              <span className="truncate text-[13px] text-muted">
                {reciterName(latest) ?? t("result.unknownReciter")} ·{" "}
                {relativeTime(latest.createdAt)}
              </span>
            </div>
            <span
              aria-hidden="true"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-surface-2"
            >
              <PlayIcon size={16} />
            </span>
          </Link>
        )}
      </section>

      <PlayerBar />
      <BottomNav current="listen" />
    </Screen>
  );
}
