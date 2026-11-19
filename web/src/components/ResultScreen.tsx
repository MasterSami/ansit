"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import {
  type Candidate,
  getAyah,
  getReciter,
  getTafsir,
  type ReciterSummary,
  type Tafsir,
} from "@/lib/api";
import { getEntry, type HistoryEntry, updateEntry } from "@/lib/history";
import {
  ayahCount,
  formatPercent,
  otherPlaces,
  repeatedTimes,
  toArabicDigits,
} from "@/lib/numerals";
import { REVELATION, STYLE_RECITATION } from "@/lib/text";

import { FeedbackSheet } from "./FeedbackSheet";
import {
  AlertIcon,
  BackIcon,
  BookIcon,
  BookmarkIcon,
  HelpIcon,
  PlayIcon,
  RefreshIcon,
  ShareIcon,
} from "./icons";
import { PlayerBar } from "./PlayerBar";
import { usePlayer } from "./Providers";
import {
  Avatar,
  Card,
  IconButton,
  IconLink,
  PrimaryButton,
  PrimaryLink,
  QuietButton,
  QuietLink,
  Screen,
  Skeleton,
  StateMessage,
} from "./ui";

/** Used for "continue listening" when the reciter could not be named. */
const FALLBACK_RECITER = "alafasy";

export function ResultScreen() {
  const t = useTranslations();
  const id = useSearchParams().get("id");
  const [loaded, setEntry] = useState<HistoryEntry | null | undefined>(
    undefined,
  );
  const entry = id ? loaded : null;

  useEffect(() => {
    if (!id) return;
    getEntry(id).then(
      (found) => setEntry(found ?? null),
      () => setEntry(null),
    );
  }, [id]);

  if (entry === undefined) return <ResultSkeleton />;
  if (entry === null) {
    return (
      <Screen wide className="pb-10">
        <StateMessage
          icon={<AlertIcon size={40} />}
          title={t("states.notFoundTitle")}
          body={t("states.notFoundBody")}
        />
        <div className="flex flex-col gap-2 px-6">
          <PrimaryLink href="/history">{t("states.openHistory")}</PrimaryLink>
          <QuietLink href="/">{t("common.home")}</QuietLink>
        </div>
      </Screen>
    );
  }
  return entry.status === "ambiguous" ? (
    <AmbiguousView entry={entry} onResolved={setEntry} />
  ) : (
    <MatchView entry={entry} onChange={setEntry} />
  );
}

function ResultSkeleton() {
  return (
    <Screen wide className="gap-3.5 px-5 pt-[52px]">
      <div className="flex justify-between">
        <Skeleton className="h-11 w-11 rounded-full" />
        <Skeleton className="h-11 w-11 rounded-full" />
      </div>
      <Skeleton className="mt-2 h-[300px] rounded-3xl" />
      <Skeleton className="h-[130px] rounded-3xl" />
      <Skeleton className="mt-auto mb-9 h-[54px] rounded-full" />
    </Screen>
  );
}

// -------------------------------------------------------------------- match

function MatchView({
  entry,
  onChange,
}: {
  entry: HistoryEntry;
  onChange: (entry: HistoryEntry) => void;
}) {
  const t = useTranslations();
  const player = usePlayer();
  const [feedback, setFeedback] = useState<
    "wrong_ayah" | "wrong_reciter" | null
  >(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [tafsirOpen, setTafsirOpen] = useState(false);
  const [tafsir, setTafsir] = useState<Tafsir | null>(null);
  const [tafsirLoading, setTafsirLoading] = useState(false);
  const [tafsirFailed, setTafsirFailed] = useState(false);
  const { ayah, reciter } = entry;

  const named: { id: string; name: string } | null = entry.userReciter
    ? { id: entry.userReciter.id, name: entry.userReciter.name_ar }
    : reciter?.status === "identified" && reciter.id && reciter.name_ar
      ? { id: reciter.id, name: reciter.name_ar }
      : null;
  const alternatives = reciter?.alternatives ?? [];

  const share = async () => {
    const text = `${t("result.shareText", {
      surah: ayah.surah_name_ar,
      ayah: toArabicDigits(ayah.ayah),
    })}\n${ayah.text_uthmani}`;
    try {
      if (navigator.share) await navigator.share({ text });
      else {
        await navigator.clipboard.writeText(text);
        setNotice(t("result.shared"));
      }
    } catch {
      // the user dismissed the share sheet: nothing to do
    }
  };

  const toggleSaved = async () => {
    const next = await updateEntry(entry.id, { saved: !entry.saved });
    if (next) onChange(next);
  };

  const continueListening = async () => {
    const reciterId = named?.id ?? alternatives[0]?.id ?? FALLBACK_RECITER;
    try {
      const detail = await getReciter(reciterId);
      const wanted = entry.userReciter ? undefined : reciter?.style;
      const audio =
        detail.ayah_audio.find((a) => a.style === wanted) ??
        detail.ayah_audio[0];
      if (!audio) {
        // Known voice, but no per-ayah recording to play (mp3quran-only reciters).
        setNotice(t("player.noAyahAudio"));
        return;
      }
      player.play({
        reciterId: detail.id,
        reciterName: detail.name_ar,
        template: audio.url_template,
        surah: ayah.surah,
        ayah: ayah.ayah,
        stopAtSurahEnd: true,
      });
    } catch {
      setNotice(t("player.failed"));
    }
  };

  const onReciter = async (picked: ReciterSummary) => {
    const next = await updateEntry(entry.id, {
      userReciter: { id: picked.id, name_ar: picked.name_ar },
    });
    if (next) onChange(next);
  };

  const toggleTafsir = () => {
    const opening = !tafsirOpen;
    setTafsirOpen(opening);
    if (opening) loadTafsir();
  };

  const loadTafsir = () => {
    if (tafsir || tafsirLoading) return;
    setTafsirFailed(false);
    setTafsirLoading(true);
    getTafsir(ayah.surah, ayah.ayah)
      .then(setTafsir, () => setTafsirFailed(true))
      .finally(() => setTafsirLoading(false));
  };

  return (
    <Screen wide>
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 pt-8 sm:px-8 lg:pt-10">
        <IconLink href="/" label={t("common.back")}>
          <BackIcon />
        </IconLink>
        <span className="text-base font-semibold">{t("result.title")}</span>
        <IconButton label={t("result.share")} onClick={share}>
          <ShareIcon size={19} />
        </IconButton>
      </header>

      <main className="mx-auto grid w-full max-w-6xl grow grid-cols-1 content-start items-start gap-5 px-5 pt-6 sm:px-8 lg:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.85fr)] lg:gap-6">
        <Card
          aria-label={t("result.ayahSection")}
          className="flex flex-col gap-4 p-5 lg:col-start-1 lg:row-span-3"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex flex-col gap-1">
              <h1 className="font-display text-[30px] leading-[1.2] font-bold text-accent">
                {t("result.surah", { name: ayah.surah_name_ar })}
              </h1>
              <span className="text-[13px] text-muted">
                {t("result.meta", {
                  revelation: REVELATION[ayah.revelation],
                  count: ayahCount(ayah.ayah_count),
                  juz: toArabicDigits(ayah.juz),
                  page: toArabicDigits(ayah.page),
                })}
              </span>
            </div>
            <span className="rounded-full bg-accent-soft px-3 py-1.5 text-sm font-bold whitespace-nowrap text-accent">
              {t("result.ayahBadge", { ayah: toArabicDigits(ayah.ayah) })}
            </span>
          </div>

          <p
            lang="ar"
            className="border-y border-divider px-2 py-[18px] text-center font-quran text-[25px] leading-[2.1]"
          >
            {ayah.text_uthmani}{" "}
            <span className="text-accent">﴿{toArabicDigits(ayah.ayah)}﴾</span>
          </p>

          <div className="flex items-center gap-2.5">
            <span className="shrink-0 text-[13px] text-muted">
              {t("result.textMatch")}
            </span>
            <div
              aria-hidden="true"
              className="h-1.5 grow overflow-hidden rounded-full bg-divider"
            >
              <div
                className="h-1.5 rounded-full bg-accent"
                style={{ width: `${Math.round(entry.textConfidence * 100)}%` }}
              />
            </div>
            <span className="shrink-0 text-[13px] font-bold">
              {formatPercent(entry.textConfidence)}
            </span>
          </div>
          <a
            href="https://tanzil.net"
            target="_blank"
            rel="noreferrer"
            className="self-center text-xs text-muted underline underline-offset-4"
          >
            {t("result.textCredit")}
          </a>
          {tafsirOpen && (
            <section
              aria-live="polite"
              className="flex flex-col gap-2 border-t border-divider pt-4"
            >
              {tafsirLoading && (
                <p className="text-sm text-muted">
                  {t("result.tafsirLoading")}
                </p>
              )}
              {tafsirFailed && (
                <div className="flex items-center justify-between gap-3 text-sm text-muted">
                  <span>{t("result.tafsirFailed")}</span>
                  <button
                    type="button"
                    className="font-semibold text-accent"
                    onClick={loadTafsir}
                  >
                    {t("common.retry")}
                  </button>
                </div>
              )}
              {tafsir && (
                <>
                  <h2 className="font-semibold">{tafsir.book}</h2>
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
                </>
              )}
            </section>
          )}
        </Card>

        <Card
          aria-label={t("result.reciterSection")}
          className="flex flex-col gap-3.5 px-5 py-4 lg:col-start-2"
        >
          {named ? (
            <div className="flex items-center gap-3.5">
              <Avatar name={named.name} size="md" />
              <div className="flex min-w-0 grow flex-col gap-0.5">
                <span className="text-xs text-muted">
                  {t("result.reciter")}
                </span>
                <span className="text-[17px] font-bold">{named.name}</span>
                <Link
                  href={`/reciter?id=${named.id}&surah=${ayah.surah}`}
                  className="flex min-h-6 items-center text-[13px] font-semibold text-accent"
                >
                  {reciter?.style && !entry.userReciter
                    ? `${STYLE_RECITATION[reciter.style]} · `
                    : ""}
                  {t("result.reciterPage")} ←
                </Link>
              </div>
              {reciter?.status === "identified" &&
                !entry.userReciter &&
                reciter.similarity !== null && (
                  <span className="flex shrink-0 flex-col items-center">
                    <span className="text-lg font-bold text-accent">
                      {formatPercent(reciter.similarity)}
                    </span>
                    <span className="text-[11px] text-muted">
                      {t("result.voiceSimilarity")}
                    </span>
                  </span>
                )}
            </div>
          ) : (
            <div className="flex items-center gap-3.5">
              <div
                aria-hidden="true"
                className="flex h-[52px] w-[52px] shrink-0 items-center justify-center rounded-full bg-warning-bg text-warning"
              >
                <HelpIcon size={22} />
              </div>
              <div className="flex min-w-0 grow flex-col gap-0.5">
                <span className="text-xs text-muted">
                  {t("result.reciter")}
                </span>
                <span className="text-[17px] font-bold">
                  {t("result.unknownReciter")}
                </span>
                <span className="text-[13px] text-muted">
                  {t(
                    reciter
                      ? "result.unknownHint"
                      : "result.reciterUnavailable",
                  )}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setFeedback("wrong_reciter")}
                className="min-h-11 shrink-0 px-1 text-[13px] font-semibold text-warning"
              >
                {t("result.addName")}
              </button>
            </div>
          )}
          {!entry.userReciter && alternatives.length > 0 && (
            <div className="flex items-center justify-between gap-3 border-t border-divider pt-3 text-[13px]">
              <span className="shrink-0 text-muted">
                {t("result.mayAlsoBe")}
              </span>
              <span className="flex min-w-0 flex-col items-end gap-1.5">
                {alternatives.slice(0, named ? 1 : 2).map((alt) => (
                  <Link
                    key={alt.id}
                    href={`/reciter?id=${alt.id}&surah=${ayah.surah}`}
                    className="flex min-h-6 items-center gap-2"
                  >
                    <span className="truncate">{alt.name_ar}</span>
                    <span className="rounded-full bg-divider px-2 py-0.5 text-xs text-muted">
                      {formatPercent(alt.similarity)}
                    </span>
                  </Link>
                ))}
              </span>
            </div>
          )}
        </Card>

        {notice && (
          <p
            role="status"
            className="text-center text-[13px] text-muted lg:col-start-2"
          >
            {notice}
          </p>
        )}

        <div className="mt-auto flex flex-col gap-2.5 pb-4 lg:col-start-2 lg:mt-0">
          <PrimaryButton onClick={continueListening}>
            <PlayIcon size={16} />
            {t("result.continueListening")}
          </PrimaryButton>
          <div className="grid grid-cols-3 gap-2.5">
            <ActionTile
              label={t("result.tafsir")}
              pressed={tafsirOpen}
              onClick={toggleTafsir}
            >
              <BookIcon />
            </ActionTile>
            <ActionTile
              label={entry.saved ? t("result.saved") : t("result.save")}
              pressed={entry.saved}
              onClick={toggleSaved}
            >
              <BookmarkIcon filled={entry.saved} />
            </ActionTile>
            <ActionTile
              label={t("result.wrong")}
              onClick={() => setFeedback("wrong_ayah")}
            >
              <HelpIcon />
            </ActionTile>
          </div>
        </div>
      </main>

      <PlayerBar />
      {feedback && (
        <FeedbackSheet
          identifyId={entry.id}
          initialKind={feedback}
          onClose={() => setFeedback(null)}
          onReciter={onReciter}
        />
      )}
    </Screen>
  );
}

function ActionTile({
  label,
  hint,
  pressed,
  disabled,
  onClick,
  children,
}: {
  label: string;
  hint?: string;
  pressed?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={pressed}
      className={`flex h-16 flex-col items-center justify-center gap-1 rounded-[18px] border border-border bg-surface text-[13px] font-medium disabled:text-muted ${
        pressed ? "text-accent" : ""
      }`}
    >
      {children}
      <span>
        {label}
        {hint && <span className="ms-1 text-[11px] text-muted">({hint})</span>}
      </span>
    </button>
  );
}

// ---------------------------------------------------------------- ambiguous

function AmbiguousView({
  entry,
  onResolved,
}: {
  entry: HistoryEntry;
  onResolved: (entry: HistoryEntry) => void;
}) {
  const t = useTranslations();
  const [picked, setPicked] = useState(0);
  const [state, setState] = useState<"idle" | "confirming" | "failed">("idle");
  const { ayah, candidates, reciter } = entry;
  const total = entry.repeatedCount ?? candidates.length;
  const sameSurah = candidates.every((c) => c.surah === candidates[0]?.surah);
  const reciterLabel =
    reciter?.status === "identified" ? reciter.name_ar : null;

  const confirm = async () => {
    const choice: Candidate | undefined = candidates[picked];
    if (!choice) return;
    setState("confirming");
    try {
      const chosen = await getAyah(choice.surah, choice.ayah);
      const next = await updateEntry(entry.id, {
        status: "match",
        ayah: chosen,
        textConfidence: choice.score,
      });
      if (next) onResolved(next);
    } catch {
      setState("failed");
    }
  };

  return (
    <Screen wide>
      <header className="mx-auto flex w-full max-w-6xl items-center gap-3 px-5 pt-8 sm:px-8 lg:pt-10">
        <IconLink href="/" label={t("common.back")}>
          <BackIcon />
        </IconLink>
        <span className="text-base font-semibold">{t("ambiguous.title")}</span>
      </header>

      <main className="mx-auto grid w-full max-w-6xl grow grid-cols-1 content-start items-start gap-5 px-5 pt-6 sm:px-8 lg:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.85fr)] lg:gap-6">
        <Card
          aria-label={t("ambiguous.heardSection")}
          className="flex flex-col gap-3.5 p-5 lg:col-start-1 lg:row-span-3"
        >
          <div className="flex items-center justify-between gap-3">
            <h1 className="font-display text-[28px] font-bold text-accent">
              {sameSurah
                ? t("result.surah", { name: ayah.surah_name_ar })
                : t("app.name")}
            </h1>
            <span className="rounded-full bg-warning-bg px-3 py-1.5 text-[13px] font-semibold whitespace-nowrap text-warning">
              {repeatedTimes(total)}
            </span>
          </div>
          <p
            lang="ar"
            className="border-y border-divider px-2 py-3.5 text-center font-quran text-[26px] leading-[2]"
          >
            {ayah.text_uthmani}
          </p>
          <p className="text-sm leading-[1.8] text-muted">
            {t("ambiguous.explain")}
          </p>
        </Card>

        <div
          role="radiogroup"
          aria-label={t("ambiguous.places")}
          className="flex flex-col gap-2 lg:col-start-2 lg:row-start-1"
        >
          {candidates.map((candidate, i) => {
            const on = i === picked;
            return (
              <button
                key={`${candidate.surah}:${candidate.ayah}`}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setPicked(i)}
                className={`flex min-h-[60px] items-center justify-between gap-3 rounded-2xl border px-4 py-2.5 text-start ${
                  on
                    ? "border-accent bg-[rgb(var(--accent-rgb)/0.1)]"
                    : "border-border bg-surface"
                }`}
              >
                <span className="flex min-w-0 flex-col items-start gap-0.5">
                  <span className="text-[15px] font-semibold">
                    {sameSurah
                      ? t("ambiguous.ayah", {
                          ayah: toArabicDigits(candidate.ayah),
                        })
                      : t("ambiguous.surahAyah", {
                          surah: candidate.surah_name_ar,
                          ayah: toArabicDigits(candidate.ayah),
                        })}
                  </span>
                  <span className="line-clamp-1 text-xs text-muted">
                    {candidate.context_before
                      ? t("ambiguous.after", { text: candidate.context_before })
                      : t("ambiguous.firstOfSurah")}
                  </span>
                </span>
                <span
                  aria-hidden="true"
                  className={`h-5 w-5 shrink-0 rounded-full ${
                    on ? "border-[6px] border-accent" : "border-2 border-track"
                  }`}
                />
              </button>
            );
          })}
          {total > candidates.length && (
            <span className="pt-0.5 text-center text-[13px] text-muted">
              {t("ambiguous.more", {
                count: otherPlaces(total - candidates.length),
              })}
            </span>
          )}
        </div>

        {reciterLabel && reciter && (
          <div className="flex items-center gap-3 rounded-[18px] border border-border bg-surface px-4 py-3 lg:col-start-2">
            <Avatar name={reciterLabel} size="sm" />
            <span className="grow text-sm font-semibold">{reciterLabel}</span>
            {reciter.similarity !== null && (
              <span className="text-sm font-bold text-accent">
                {formatPercent(reciter.similarity)}
              </span>
            )}
          </div>
        )}

        <div className="mt-auto flex flex-col gap-2 pb-9 lg:col-start-2 lg:mt-0">
          {state === "failed" && (
            <p role="alert" className="text-center text-[13px] text-warning">
              {t("ambiguous.confirmFailed")}
            </p>
          )}
          <PrimaryLink href={`/listen?prev=${entry.id}`}>
            <RefreshIcon size={18} strokeWidth={2} />
            {t("ambiguous.listenMore")}
          </PrimaryLink>
          <QuietButton
            tone="accent"
            onClick={confirm}
            disabled={state === "confirming"}
          >
            {t("ambiguous.confirm")}
          </QuietButton>
        </div>
      </main>
    </Screen>
  );
}
