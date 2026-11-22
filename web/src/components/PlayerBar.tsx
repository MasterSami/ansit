"use client";

import { useTranslations } from "next-intl";

import { formatElapsed, toArabicDigits } from "@/lib/numerals";

import { CloseIcon, PauseIcon, PlayIcon } from "./icons";
import { usePlayer, useSurahs } from "./Providers";

/** A slim bar for the recitation being played. Renders nothing when idle. */
export function PlayerBar() {
  const t = useTranslations("player");
  const { track, playing, failed, position, duration, toggle, stop } =
    usePlayer();
  const surahs = useSurahs();
  if (!track) return null;
  const surahName =
    surahs?.[track.surah - 1]?.name_ar ?? toArabicDigits(track.surah);
  const wholeSurah = track.kind === "surah";
  const progress = duration > 0 ? Math.min(1, position / duration) : 0;

  return (
    <div
      role="region"
      aria-label={t("label")}
      className="player-bar sticky bottom-0 z-10 mx-3 mb-2 overflow-hidden rounded-lg border border-border bg-surface md:mx-0"
    >
      {/* Progress through the current file: a hairline, not a slider. */}
      <div aria-hidden="true" className="h-[2px] bg-divider">
        <div
          className="h-full bg-rubric transition-[width] duration-300"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
      <div className="flex items-center gap-3 px-3 py-2">
        <button
          type="button"
          onClick={toggle}
          aria-label={playing ? t("pause") : t("play")}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-accent text-on-accent"
        >
          {playing ? <PauseIcon size={16} /> : <PlayIcon size={16} />}
        </button>
        <div className="flex min-w-0 grow flex-col" aria-live="polite">
          <span className="truncate text-sm font-semibold">
            {wholeSurah
              ? t("nowPlayingSurah", { surah: surahName })
              : t("nowPlaying", {
                  surah: surahName,
                  ayah: toArabicDigits(track.ayah),
                })}
          </span>
          <span
            className={`truncate text-xs ${failed ? "text-warning" : "text-muted"}`}
          >
            {failed ? t("failed") : track.reciterName}
          </span>
        </div>
        {wholeSurah && duration > 0 && (
          <span dir="ltr" className="shrink-0 text-xs text-muted tabular-nums">
            {formatElapsed(position)} / {formatElapsed(duration)}
          </span>
        )}
        <button
          type="button"
          onClick={stop}
          aria-label={t("stop")}
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-muted hover:text-text"
        >
          <CloseIcon size={18} />
        </button>
      </div>
    </div>
  );
}
