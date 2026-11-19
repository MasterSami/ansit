"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";

import { getAyah, getTafsir, type Ayah, type Tafsir } from "@/lib/api";
import { toArabicDigits } from "@/lib/numerals";

import { BottomNav } from "./BottomNav";
import { BookIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { useSurahs } from "./Providers";
import { PrimaryButton, Screen } from "./ui";

export function MushafScreen() {
  const t = useTranslations();
  const surahs = useSurahs();
  const [surahNumber, setSurahNumber] = useState(1);
  const [ayahNumber, setAyahNumber] = useState(1);
  const [ayah, setAyah] = useState<Ayah | null>(null);
  const [tafsir, setTafsir] = useState<Tafsir | null>(null);
  const [tafsirOpen, setTafsirOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  const openAyah = async () => {
    setLoading(true);
    setFailed(false);
    setTafsir(null);
    setTafsirOpen(false);
    try {
      setAyah(await getAyah(surahNumber, ayahNumber));
    } catch {
      setFailed(true);
      setAyah(null);
    } finally {
      setLoading(false);
    }
  };

  const openTafsir = async () => {
    const opening = !tafsirOpen;
    setTafsirOpen(opening);
    if (!opening || tafsir || !ayah) return;
    setLoading(true);
    setFailed(false);
    try {
      setTafsir(await getTafsir(ayah.surah, ayah.ayah));
    } catch {
      setFailed(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Screen>
      <header className="flex items-center gap-3 px-5 pt-8">
        <BookIcon size={22} />
        <h1 className="text-lg font-bold">{t("mushaf.title")}</h1>
      </header>

      <main className="flex grow flex-col gap-4 px-5 pt-6 pb-6">
        <p className="text-sm leading-7 text-muted">{t("mushaf.body")}</p>
        <div className="grid grid-cols-[minmax(0,1fr)_6rem] gap-3">
          <label className="flex flex-col gap-2 text-sm font-semibold">
            {t("mushaf.surah")}
            <select
              value={surahNumber}
              onChange={(event) => {
                setSurahNumber(Number(event.target.value));
                setAyahNumber(1);
              }}
              className="h-12 rounded-xl border border-border bg-surface px-3"
            >
              {(surahs ?? []).map((surah) => (
                <option key={surah.number} value={surah.number}>
                  {toArabicDigits(surah.number)}. {surah.name_ar}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold">
            {t("mushaf.ayah")}
            <input
              type="number"
              min={1}
              max={surahs?.[surahNumber - 1]?.ayah_count ?? 286}
              value={ayahNumber}
              onChange={(event) => setAyahNumber(Number(event.target.value))}
              className="h-12 rounded-xl border border-border bg-surface px-3"
            />
          </label>
        </div>
        <PrimaryButton onClick={openAyah} disabled={loading || !surahs}>
          {loading ? t("mushaf.loading") : t("mushaf.openAyah")}
        </PrimaryButton>

        {failed && (
          <p role="alert" className="text-sm text-warning">
            {t("mushaf.loadFailed")}
          </p>
        )}
        {ayah && (
          <article className="flex flex-col gap-4 rounded-3xl border border-border bg-surface p-5">
            <h2 className="font-semibold text-accent">
              {t("result.surah", { name: ayah.surah_name_ar })} ·{" "}
              {t("result.ayahBadge", { ayah: toArabicDigits(ayah.ayah) })}
            </h2>
            <p
              lang="ar"
              dir="rtl"
              className="text-center font-quran text-2xl leading-[2.2]"
            >
              {ayah.text_uthmani}{" "}
              <span className="text-accent">﴿{toArabicDigits(ayah.ayah)}﴾</span>
            </p>
            <a
              href="https://tanzil.net"
              target="_blank"
              rel="noreferrer"
              className="self-center text-xs text-muted underline underline-offset-4"
            >
              {t("result.textCredit")}
            </a>
            <button
              type="button"
              aria-expanded={tafsirOpen}
              onClick={openTafsir}
              className="min-h-11 rounded-xl bg-surface-2 px-4 text-sm font-semibold text-accent"
            >
              {tafsirOpen ? t("mushaf.hideTafsir") : t("mushaf.showTafsir")}
            </button>
            {tafsirOpen && tafsir && (
              <section
                aria-live="polite"
                className="flex flex-col gap-2 border-t border-divider pt-4"
              >
                <h3 className="font-semibold">{tafsir.book}</h3>
                <p dir="rtl" lang="ar" className="text-[15px] leading-8">
                  {tafsir.text}
                </p>
                <p className="text-xs text-muted">
                  {t("result.tafsirAuthor", {
                    author: tafsir.author,
                    publisher: tafsir.publisher,
                    version: tafsir.version,
                  })}
                </p>
                <a
                  href={tafsir.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="self-start text-xs text-accent underline underline-offset-4"
                >
                  {tafsir.attribution}
                </a>
              </section>
            )}
            {tafsirOpen && loading && (
              <p role="status" className="text-sm text-muted">
                {t("result.tafsirLoading")}
              </p>
            )}
            {tafsirOpen && failed && (
              <p role="alert" className="text-sm text-warning">
                {t("result.tafsirFailed")}
              </p>
            )}
          </article>
        )}
      </main>

      <PlayerBar />
      <BottomNav current="mushaf" />
    </Screen>
  );
}
