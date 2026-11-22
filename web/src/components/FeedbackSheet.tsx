"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import {
  type FeedbackBody,
  getReciters,
  type ReciterSummary,
  sendFeedback,
} from "@/lib/api";

import { CloseIcon } from "./icons";
import { IconButton, PrimaryButton } from "./ui";

type Kind = FeedbackBody["kind"];

/**
 * Bottom sheet for "wrong result?" and for naming an unknown reciter.
 * `onReciter` is called with the reciter the user picked, so the history entry
 * can show the name straight away.
 */
export function FeedbackSheet({
  identifyId,
  initialKind,
  onClose,
  onReciter,
}: {
  identifyId: string;
  initialKind: Kind;
  onClose: () => void;
  onReciter: (reciter: ReciterSummary) => void;
}) {
  const t = useTranslations("feedback");
  const tc = useTranslations("common");
  const dialog = useRef<HTMLDialogElement>(null);
  const [kind, setKind] = useState<Kind>(initialKind);
  const [reciters, setReciters] = useState<ReciterSummary[] | null>(null);
  const [reciterId, setReciterId] = useState("");
  const [surah, setSurah] = useState("");
  const [ayah, setAyah] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "failed">(
    "idle",
  );

  useEffect(() => {
    dialog.current?.showModal();
    getReciters().then(setReciters, () => setReciters([]));
  }, []);

  const submit = async () => {
    setState("sending");
    const body: FeedbackBody = { identify_id: identifyId, kind };
    const surahNumber = Number(surah);
    const ayahNumber = Number(ayah);
    if (
      kind === "wrong_ayah" &&
      surahNumber >= 1 &&
      surahNumber <= 114 &&
      ayahNumber >= 1
    ) {
      body.correct_surah = surahNumber;
      body.correct_ayah = ayahNumber;
    }
    const picked = (reciters ?? []).find((reciter) => reciter.id === reciterId);
    if (kind === "wrong_reciter" && picked) body.correct_reciter_id = picked.id;
    try {
      await sendFeedback(body);
      if (kind === "wrong_reciter" && picked) onReciter(picked);
      setState("sent");
    } catch {
      setState("failed");
    }
  };

  const kinds: [Kind, string][] = [
    ["wrong_ayah", t("wrongAyah")],
    ["wrong_reciter", t("wrongReciter")],
    ["other", t("other")],
  ];
  const field =
    "h-12 w-full rounded-lg border border-border bg-bg px-4 text-[15px] text-text placeholder:text-muted";

  return (
    <dialog
      ref={dialog}
      onClose={onClose}
      aria-labelledby="feedback-title"
      className="m-0 mx-auto mt-auto w-full max-w-[430px] rounded-t-3xl border border-border bg-surface p-5 pb-8 text-text backdrop:bg-black/50"
    >
      <div className="flex items-center justify-between gap-3">
        <h2 id="feedback-title" className="text-lg font-bold">
          {initialKind === "wrong_reciter" ? t("reciterTitle") : t("title")}
        </h2>
        <IconButton label={tc("close")} onClick={() => dialog.current?.close()}>
          <CloseIcon size={18} />
        </IconButton>
      </div>

      {state === "sent" ? (
        <p
          role="status"
          className="py-8 text-center text-base font-semibold text-accent"
        >
          {t("thanks")}
        </p>
      ) : (
        <div className="mt-4 flex flex-col gap-4">
          <div
            role="radiogroup"
            aria-labelledby="feedback-title"
            className="flex flex-wrap gap-2"
          >
            {kinds.map(([value, label]) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={kind === value}
                onClick={() => setKind(value)}
                className={`h-11 rounded-md border px-4 text-[13px] font-semibold ${
                  kind === value
                    ? "border-accent bg-accent text-on-accent"
                    : "border-border bg-bg text-text"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {kind === "wrong_ayah" && (
            <div className="grid grid-cols-2 gap-3">
              <label className="flex flex-col gap-1.5 text-[13px] text-muted">
                {t("surahNumber")} ({t("optional")})
                <input
                  className={field}
                  inputMode="numeric"
                  value={surah}
                  onChange={(event) =>
                    setSurah(event.target.value.replace(/\D/g, "").slice(0, 3))
                  }
                />
              </label>
              <label className="flex flex-col gap-1.5 text-[13px] text-muted">
                {t("ayahNumber")} ({t("optional")})
                <input
                  className={field}
                  inputMode="numeric"
                  value={ayah}
                  onChange={(event) =>
                    setAyah(event.target.value.replace(/\D/g, "").slice(0, 3))
                  }
                />
              </label>
            </div>
          )}

          {kind === "wrong_reciter" &&
            (reciters === null || reciters.length > 0 ? (
              <label className="flex flex-col gap-1.5 text-[13px] text-muted">
                {t("chooseReciter")} ({t("optional")})
                <select
                  className={field}
                  value={reciterId}
                  onChange={(event) => setReciterId(event.target.value)}
                >
                  <option value="">—</option>
                  {(reciters ?? []).map((reciter) => (
                    <option key={reciter.id} value={reciter.id}>
                      {reciter.name_ar}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              // The server has no reciter list (voice recognition is off there).
              <p role="status" className="text-[13px] text-warning">
                {t("noReciters")}
              </p>
            ))}

          <p className="text-xs text-muted">{t("note")}</p>
          {state === "failed" && (
            <p role="alert" className="text-[13px] text-warning">
              {t("failed")}
            </p>
          )}
          <PrimaryButton onClick={submit} disabled={state === "sending"}>
            {state === "sending" ? t("sending") : t("send")}
          </PrimaryButton>
        </div>
      )}
    </dialog>
  );
}
