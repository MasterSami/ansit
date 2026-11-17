"use client";

import { useTranslations } from "next-intl";

import { toArabicDigits } from "@/lib/numerals";

import { CloseIcon, PauseIcon, PlayIcon } from "./icons";
import { usePlayer, useSurahs } from "./Providers";

/** A slim bar for the recitation being played. Renders nothing when idle. */
export function PlayerBar() {
  const t = useTranslations("player");
  const { track, playing, failed, toggle, stop } = usePlayer();
  const surahs = useSurahs();
  if (!track) return null;
  const surahName =
    surahs?.[track.surah - 1]?.name_ar ?? toArabicDigits(track.surah);

  return (
    <div
      role="region"
      aria-label={t("label")}
      className="sticky bottom-0 z-10 mx-3 mb-2 flex items-center gap-3 rounded-2xl border border-border bg-surface-2 px-3 py-2"
    >
      <button
        type="button"
        onClick={toggle}
        aria-label={playing ? t("pause") : t("play")}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent text-on-accent"
      >
        {playing ? <PauseIcon size={16} /> : <PlayIcon size={16} />}
      </button>
      <div className="flex min-w-0 grow flex-col" aria-live="polite">
        <span className="truncate text-sm font-semibold">
          {t("nowPlaying", {
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
      <button
        type="button"
        onClick={stop}
        aria-label={t("stop")}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-muted"
      >
        <CloseIcon size={18} />
      </button>
    </div>
  );
}
