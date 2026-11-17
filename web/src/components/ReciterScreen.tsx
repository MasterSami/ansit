"use client";

import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import {
  ApiError,
  getReciter,
  type ReciterDetail,
  type Style,
} from "@/lib/api";
import { listEntries } from "@/lib/history";
import { ayahCount, toArabicDigits } from "@/lib/numerals";
import { STYLE_TAB } from "@/lib/text";
import { daysAgo } from "@/lib/time";

import { AlertIcon, BackIcon, HeartIcon, PlayIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { usePlayer, useSurahs } from "./Providers";
import {
  Avatar,
  IconButton,
  PrimaryButton,
  QuietLink,
  Screen,
  Skeleton,
  StateMessage,
} from "./ui";

const STYLE_ORDER: Style[] = ["murattal", "mujawwad", "muallim"];
const FAVOURITES_KEY = "ansit.favourites";

function readFavourites(): string[] {
  try {
    return JSON.parse(localStorage.getItem(FAVOURITES_KEY) ?? "[]") as string[];
  } catch {
    return [];
  }
}

export function ReciterScreen() {
  const t = useTranslations();
  const params = useSearchParams();
  const id = params.get("id");
  const fromSurah = Number(params.get("surah")) || null;
  const surahs = useSurahs();
  const player = usePlayer();
  const [loaded, setReciter] = useState<
    ReciterDetail | null | "missing" | "failed"
  >(null);
  const reciter = id ? loaded : "missing";
  const [style, setStyle] = useState<Style | null>(null);
  const [favourite, setFavourite] = useState(false);
  const [heardToday, setHeardToday] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!id) return;
    queueMicrotask(() => setFavourite(readFavourites().includes(id)));
    getReciter(id).then(
      (detail) => {
        setReciter(detail);
        setStyle(STYLE_ORDER.find((s) => detail.styles.includes(s)) ?? null);
      },
      (error) =>
        setReciter(
          error instanceof ApiError && error.status === 404
            ? "missing"
            : "failed",
        ),
    );
    // Surahs identified today with this reciter get highlighted.
    listEntries().then(
      (entries) =>
        setHeardToday(
          new Set(
            entries
              .filter(
                (e) =>
                  daysAgo(e.createdAt) === 0 &&
                  (e.userReciter?.id === id ||
                    (!e.userReciter && e.reciter?.id === id)),
              )
              .map((e) => e.ayah.surah),
          ),
        ),
      () => undefined,
    );
  }, [id]);

  const styles = useMemo(
    () =>
      typeof reciter === "object" && reciter
        ? STYLE_ORDER.filter((s) => reciter.styles.includes(s))
        : [],
    [reciter],
  );

  if (reciter === "missing" || reciter === "failed") {
    return (
      <Screen className="pb-10">
        <StateMessage
          icon={<AlertIcon size={40} />}
          title={t(
            reciter === "missing"
              ? "reciter.notFoundTitle"
              : "reciter.loadFailedTitle",
          )}
          body={t(
            reciter === "missing"
              ? "states.notFoundBody"
              : "states.offlineBody",
          )}
        />
        <div className="px-6">
          <QuietLink href="/">{t("common.home")}</QuietLink>
        </div>
      </Screen>
    );
  }
  if (reciter === null) {
    return (
      <Screen className="items-center gap-3 px-5 pt-[52px]">
        <Skeleton className="mt-14 h-24 w-24 rounded-full" />
        <Skeleton className="h-9 w-56" />
        <Skeleton className="mt-4 h-12 w-full" />
        <Skeleton className="h-[60px] w-full" />
        <Skeleton className="h-[60px] w-full" />
        <Skeleton className="h-[60px] w-full" />
      </Screen>
    );
  }

  const template = reciter.ayah_audio.find(
    (a) => a.style === style,
  )?.url_template;
  const play = (surah: number, stopAtSurahEnd: boolean) => {
    if (!template) return;
    player.play({
      reciterId: reciter.id,
      reciterName: reciter.name_ar,
      template,
      surah,
      ayah: 1,
      stopAtSurahEnd,
    });
  };

  const toggleFavourite = () => {
    const current = readFavourites();
    const next = favourite
      ? current.filter((x) => x !== reciter.id)
      : [...current, reciter.id];
    try {
      localStorage.setItem(FAVOURITES_KEY, JSON.stringify(next));
    } catch {
      // storage blocked: the heart still toggles for this visit
    }
    setFavourite(!favourite);
  };

  // The surah the user came from goes first, then mushaf order.
  const ordered = surahs
    ? [...surahs].sort(
        (a, b) =>
          Number(b.number === fromSurah) - Number(a.number === fromSurah) ||
          a.number - b.number,
      )
    : null;

  return (
    <Screen>
      <header className="flex items-center justify-between px-5 pt-[52px]">
        <IconButton
          label={t("common.back")}
          onClick={() => window.history.back()}
        >
          <BackIcon />
        </IconButton>
        <IconButton
          label={t(favourite ? "reciter.unfavourite" : "reciter.favourite")}
          aria-pressed={favourite}
          onClick={toggleFavourite}
          className={favourite ? "text-accent" : ""}
        >
          <HeartIcon size={19} filled={favourite} />
        </IconButton>
      </header>

      <section className="flex flex-col items-center gap-2.5 px-5 pt-3 text-center">
        <Avatar name={reciter.name_ar} size="lg" />
        <h1 className="font-display text-[28px] leading-[1.3] font-bold">
          {reciter.name_ar}
        </h1>
        {reciter.country && (
          <span className="text-sm text-muted">{reciter.country}</span>
        )}
      </section>

      {styles.length > 1 && (
        <div
          role="tablist"
          aria-label={t("reciter.styles")}
          className="mx-5 mt-5 grid gap-1.5 rounded-2xl border border-border bg-surface p-1"
          style={{
            gridTemplateColumns: `repeat(${styles.length}, minmax(0, 1fr))`,
          }}
        >
          {styles.map((s) => (
            <button
              key={s}
              type="button"
              role="tab"
              aria-selected={s === style}
              onClick={() => setStyle(s)}
              className={`h-11 rounded-xl text-sm font-semibold ${
                s === style ? "bg-accent text-on-accent" : "text-muted"
              }`}
            >
              {STYLE_TAB[s]}
            </button>
          ))}
        </div>
      )}

      <main className="flex grow flex-col gap-2 px-5 pt-4">
        {!template && (
          <p role="status" className="pb-1 text-center text-[13px] text-muted">
            {t("player.noAyahAudio")}
          </p>
        )}
        {ordered === null
          ? Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-[60px]" />
            ))
          : ordered.map((surah) => {
              const heard = heardToday.has(surah.number);
              return (
                <div
                  key={surah.number}
                  className={`flex items-center gap-3 rounded-2xl border bg-surface px-3 py-2.5 ${
                    heard ? "border-accent" : "border-border"
                  }`}
                >
                  <span className="flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-xl bg-surface-2 text-sm font-semibold text-muted">
                    {toArabicDigits(surah.number)}
                  </span>
                  <span className="flex min-w-0 grow flex-col gap-0.5">
                    <span className="text-[15px] font-semibold">
                      {surah.name_ar}
                    </span>
                    <span
                      className={`text-xs ${heard ? "text-accent" : "text-muted"}`}
                    >
                      {ayahCount(surah.ayah_count)}
                      {heard && ` · ${t("reciter.heardToday")}`}
                    </span>
                  </span>
                  <button
                    type="button"
                    aria-label={t("reciter.playSurah", { name: surah.name_ar })}
                    onClick={() => play(surah.number, true)}
                    disabled={!template}
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-2 disabled:text-track"
                  >
                    <PlayIcon size={14} />
                  </button>
                </div>
              );
            })}
      </main>

      <div className="sticky bottom-0 flex flex-col gap-2 bg-bg px-5 pt-3 pb-9">
        <PlayerBar />
        <PrimaryButton onClick={() => play(1, false)} disabled={!template}>
          <PlayIcon size={16} />
          {t("reciter.playAll")}
        </PrimaryButton>
      </div>
    </Screen>
  );
}
