"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  ApiError,
  type ApiErrorKind,
  identify,
  type IdentifyResponse,
} from "@/lib/api";
import { entryFromResponse, putEntry } from "@/lib/history";
import { formatElapsed, toArabicDigits } from "@/lib/numerals";
import {
  LEVEL_BARS,
  MAX_RECORD_SEC,
  micFailure,
  micPermission,
  MIN_RECORD_SEC,
  type Recording,
  recordingSupported,
  startRecording,
} from "@/lib/recorder";

import {
  AlertIcon,
  BroadcastIcon,
  CheckIcon,
  ClockIcon,
  MicIcon,
  MicOffIcon,
  PauseCircleIcon,
  ShieldIcon,
  StopIcon,
  WifiOffIcon,
} from "./icons";
import {
  PrimaryButton,
  QuietButton,
  QuietLink,
  Screen,
  StateMessage,
} from "./ui";

type Phase =
  | { name: "checking" }
  | { name: "explain" }
  | { name: "recording" }
  | { name: "identifying" }
  | { name: "mic"; failure: "denied" | "unavailable" }
  | { name: "no_match"; reason: NonNullable<IdentifyResponse["reason"]> }
  | { name: "error"; kind: ApiErrorKind; retryAfter: number | null };

/** Resting bar heights from the mockup; live levels scale them. */
const BAR_HEIGHTS = [34, 58, 80, 46, 70, 40, 62, 30];

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);
  return reduced;
}

export function ListenScreen() {
  const t = useTranslations();
  const router = useRouter();
  const previousId = useSearchParams().get("prev");
  const [phase, setPhase] = useState<Phase>({ name: "checking" });
  const [elapsed, setElapsed] = useState(0);
  const [levels, setLevels] = useState<number[]>(() =>
    Array<number>(LEVEL_BARS).fill(0),
  );
  const recording = useRef<Recording | null>(null);
  const startedAt = useRef(0);
  const upload = useRef<AbortController | null>(null);
  const finishing = useRef(false);

  const finish = useCallback(async () => {
    const active = recording.current;
    if (!active || finishing.current) return;
    finishing.current = true;
    recording.current = null;
    setPhase({ name: "identifying" });
    try {
      const clip = await active.stop(); // the microphone is released here
      upload.current = new AbortController();
      const response = await identify(clip, {
        previousIdentifyId: previousId,
        signal: upload.current.signal,
      });
      const entry = entryFromResponse(response);
      if (!entry) {
        setPhase({
          name: "no_match",
          reason: response.reason ?? "low_confidence",
        });
        return;
      }
      await putEntry(entry).catch(() => undefined); // history is best-effort
      router.replace(`/result?id=${entry.id}`);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      const api = error instanceof ApiError ? error : new ApiError("server");
      setPhase({ name: "error", kind: api.kind, retryAfter: api.retryAfter });
    } finally {
      finishing.current = false;
    }
  }, [previousId, router]);

  const begin = useCallback(async () => {
    setElapsed(0);
    try {
      recording.current = await startRecording();
      startedAt.current = performance.now();
      setPhase({ name: "recording" });
    } catch (error) {
      setPhase({ name: "mic", failure: micFailure(error) });
    }
  }, []);

  // Decide what to show first: record straight away, explain, or report a problem.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!recordingSupported()) {
        setPhase({ name: "mic", failure: "unavailable" });
        return;
      }
      const permission = await micPermission();
      if (cancelled) return;
      if (permission === "granted") await begin();
      else if (permission === "denied")
        setPhase({ name: "mic", failure: "denied" });
      else setPhase({ name: "explain" });
    })();
    return () => {
      cancelled = true;
      recording.current?.cancel();
      recording.current = null;
      upload.current?.abort();
    };
  }, [begin]);

  // Timer, live levels and the automatic stop at 10 s.
  useEffect(() => {
    if (phase.name !== "recording") return;
    const timer = window.setInterval(() => {
      const seconds = (performance.now() - startedAt.current) / 1000;
      setElapsed(seconds);
      if (recording.current) setLevels(recording.current.levels());
      if (seconds >= MAX_RECORD_SEC) void finish();
    }, 100);
    return () => window.clearInterval(timer);
  }, [phase.name, finish]);

  const stop = () => {
    if (elapsed < MIN_RECORD_SEC) {
      // Too little to identify anything: treat it as a cancel.
      recording.current?.cancel();
      recording.current = null;
      router.push("/");
    } else {
      void finish();
    }
  };

  const cancelUpload = () => {
    upload.current?.abort();
    router.push("/");
  };

  if (phase.name === "explain") {
    return <PermissionExplainer onAllow={begin} />;
  }
  if (phase.name === "mic") {
    const denied = phase.failure === "denied";
    return (
      <Problem
        icon={<MicOffIcon size={40} />}
        title={t(denied ? "states.deniedTitle" : "states.unavailableTitle")}
        body={t(denied ? "states.deniedBody" : "states.unavailableBody")}
        onRetry={denied ? begin : undefined}
      />
    );
  }
  if (phase.name === "no_match") {
    const key = {
      no_speech: "noSpeech",
      too_short: "tooShort",
      low_confidence: "lowConfidence",
    }[phase.reason];
    return (
      <Problem
        tone="neutral"
        icon={<MicIcon size={40} />}
        title={t(`states.${key}Title`)}
        body={t(`states.${key}Body`)}
        onRetry={begin}
      />
    );
  }
  if (phase.name === "error") {
    return (
      <ErrorState
        kind={phase.kind}
        retryAfter={phase.retryAfter}
        onRetry={begin}
      />
    );
  }

  const identifying = phase.name === "identifying";
  return (
    <Screen>
      <header className="flex items-center justify-between px-6 pt-14">
        <span className="font-display text-[26px] font-bold text-accent">
          {t("app.name")}
        </span>
        <span
          className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-[13px] font-medium"
          role="timer"
          aria-label={t("listen.elapsed")}
        >
          <span
            aria-hidden="true"
            className="h-2 w-2 rounded-full bg-recording"
          />
          <span dir="ltr">{formatElapsed(elapsed)}</span>
        </span>
      </header>

      <main className="flex grow flex-col items-center justify-center gap-9 px-6 py-6">
        <SoundWave
          levels={levels}
          live={phase.name === "recording"}
          label={t("listen.wave")}
        />

        <div
          className="flex flex-col items-center gap-2 text-center"
          aria-live="polite"
        >
          <h1 className="text-2xl font-bold">
            {t(identifying ? "listen.identifying" : "listen.listening")}
          </h1>
          <p className="max-w-[290px] text-[15px] text-muted">
            {identifying
              ? t("listen.identifyingHint")
              : previousId
                ? t("listen.continuing")
                : t("listen.hint")}
          </p>
        </div>

        <ol
          aria-label={t("listen.steps")}
          className="flex w-full flex-col gap-3.5 rounded-[18px] border border-border bg-surface p-4"
        >
          <Step
            label={t("listen.stepCapture")}
            state={identifying ? "done" : "active"}
          />
          <Step
            label={t("listen.stepMatch")}
            state={identifying ? "active" : "waiting"}
          />
          <Step
            label={t("listen.stepReciter")}
            state={identifying ? "active" : "waiting"}
          />
        </ol>
      </main>

      <footer className="flex flex-col items-center px-6 pb-10">
        {identifying ? (
          <QuietButton onClick={cancelUpload}>{t("common.cancel")}</QuietButton>
        ) : (
          <QuietButton onClick={stop} disabled={phase.name !== "recording"}>
            <StopIcon size={16} />
            {t("listen.stop")}
          </QuietButton>
        )}
      </footer>
    </Screen>
  );
}

function SoundWave({
  levels,
  live,
  label,
}: {
  levels: number[];
  live: boolean;
  label: string;
}) {
  const reducedMotion = usePrefersReducedMotion();
  const ring =
    "absolute inset-0 rounded-full border-2 border-[rgb(var(--accent-rgb)/0.5)]";
  return (
    <div className="relative flex h-[300px] w-[300px] items-center justify-center">
      <div aria-hidden="true" className={`ansit-pulse ${ring}`} />
      <div aria-hidden="true" className={`ansit-pulse-2 ${ring}`} />
      <div aria-hidden="true" className={`ansit-pulse-3 ${ring}`} />
      <div
        role="img"
        aria-label={label}
        className="relative flex h-44 w-44 items-center justify-center gap-[5px] rounded-full border border-[rgb(var(--accent-rgb)/0.45)] bg-surface"
      >
        {BAR_HEIGHTS.map((height, i) => {
          // While recording the bars follow the microphone; otherwise they idle.
          const followMic = live && !reducedMotion;
          return (
            <span
              key={i}
              className={`w-[5px] rounded-[3px] bg-accent ${followMic || reducedMotion ? "" : "ansit-bar"}`}
              style={{
                height,
                animationDelay: `${i * 0.15}s`,
                transform: followMic
                  ? `scaleY(${0.3 + 0.7 * (levels[i] ?? 0)})`
                  : undefined,
                transition: followMic ? "transform 100ms linear" : undefined,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

function Step({
  label,
  state,
}: {
  label: string;
  state: "done" | "active" | "waiting";
}) {
  const t = useTranslations("listen");
  return (
    <li
      className={`flex items-center gap-3 text-sm ${state === "waiting" ? "text-muted" : ""}`}
      aria-current={state === "active" ? "step" : undefined}
    >
      {state === "done" && (
        <span
          aria-hidden="true"
          className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full bg-accent text-on-accent"
        >
          <CheckIcon size={14} strokeWidth={2.6} />
        </span>
      )}
      {state === "active" && (
        <span
          aria-hidden="true"
          className="flex h-[26px] w-[26px] shrink-0 items-center justify-center rounded-full border-2 border-accent"
        >
          <span className="h-2 w-2 rounded-full bg-accent" />
        </span>
      )}
      {state === "waiting" && (
        <span
          aria-hidden="true"
          className="h-[26px] w-[26px] shrink-0 rounded-full border-2 border-track"
        />
      )}
      <span className={`grow ${state === "active" ? "font-semibold" : ""}`}>
        {label}
      </span>
      {state === "done" && (
        <span className="text-xs text-muted">{t("done")}</span>
      )}
      {state === "active" && (
        <span className="text-xs text-accent">{t("inProgress")}</span>
      )}
    </li>
  );
}

/** Shown before the browser's own prompt, so the request never comes as a surprise. */
function PermissionExplainer({ onAllow }: { onAllow: () => void }) {
  const t = useTranslations();
  const promises: [ReactNode, string, string][] = [
    [
      <PauseCircleIcon key="a" size={17} strokeWidth={1.9} />,
      "onlyWhen",
      "onlyWhen",
    ],
    [<ShieldIcon key="b" size={17} strokeWidth={1.9} />, "deleted", "deleted"],
    [
      <BroadcastIcon key="c" size={17} strokeWidth={1.9} />,
      "anySource",
      "anySource",
    ],
  ];
  return (
    <Screen className="px-6 pt-14 pb-9">
      <div className="flex items-center justify-between">
        <span className="font-display text-[26px] font-bold text-accent">
          {t("app.name")}
        </span>
      </div>

      <div className="flex grow flex-col justify-center gap-8 py-6">
        <div className="relative flex h-[200px] w-[200px] items-center justify-center self-center">
          <div
            aria-hidden="true"
            className="absolute inset-0 rounded-full border border-dashed border-[rgb(var(--accent-rgb)/0.35)]"
          />
          <div
            aria-hidden="true"
            className="absolute inset-7 rounded-full border border-[rgb(var(--accent-rgb)/0.3)] bg-[rgb(var(--accent-rgb)/0.08)]"
          />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-full bg-accent text-on-accent">
            <MicIcon size={44} strokeWidth={1.7} />
          </div>
        </div>

        <div className="flex flex-col gap-2.5 text-center">
          <h1 className="text-[26px] leading-[1.4] font-bold">
            {t("permission.title")}
          </h1>
          <p className="text-[15px] leading-[1.8] text-muted">
            {t("permission.subtitle")}
          </p>
        </div>

        <ul className="flex flex-col gap-4 rounded-[20px] border border-border bg-surface p-[18px]">
          {promises.map(([icon, key]) => (
            <li key={key} className="flex items-start gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[10px] bg-accent-soft text-accent">
                {icon}
              </span>
              <span className="flex flex-col gap-0.5">
                <span className="text-[15px] font-semibold">
                  {t(`permission.${key}Title`)}
                </span>
                <span className="text-[13px] leading-[1.6] text-muted">
                  {t(`permission.${key}Body`)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-col gap-2">
        <PrimaryButton onClick={onAllow}>{t("permission.allow")}</PrimaryButton>
        <QuietLink href="/">{t("permission.notNow")}</QuietLink>
      </div>
    </Screen>
  );
}

function Problem({
  icon,
  title,
  body,
  tone = "warning",
  onRetry,
  children,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  tone?: "neutral" | "warning";
  onRetry?: () => void;
  children?: ReactNode;
}) {
  const t = useTranslations("common");
  return (
    <Screen className="pb-10">
      <StateMessage icon={icon} title={title} body={body} tone={tone}>
        {children}
      </StateMessage>
      <div className="flex flex-col gap-2 px-6">
        {onRetry && (
          <PrimaryButton onClick={onRetry}>{t("retry")}</PrimaryButton>
        )}
        <QuietLink href="/">{t("home")}</QuietLink>
      </div>
    </Screen>
  );
}

function ErrorState({
  kind,
  retryAfter,
  onRetry,
}: {
  kind: ApiErrorKind;
  retryAfter: number | null;
  onRetry: () => void;
}) {
  const t = useTranslations("states");
  const [wait, setWait] = useState(
    kind === "rate_limited" ? (retryAfter ?? 0) : 0,
  );
  useEffect(() => {
    if (wait <= 0) return;
    const timer = window.setTimeout(
      () => setWait((seconds) => seconds - 1),
      1000,
    );
    return () => window.clearTimeout(timer);
  }, [wait]);

  const copy = {
    offline: ["offline", <WifiOffIcon key="i" size={40} />],
    rate_limited: ["rate", <ClockIcon key="i" size={40} />],
    busy: ["busy", <ClockIcon key="i" size={40} />],
    bad_audio: ["badAudio", <AlertIcon key="i" size={40} />],
    server: ["server", <AlertIcon key="i" size={40} />],
  } as const;
  const [key, icon] = copy[kind];
  return (
    <Problem
      icon={icon}
      title={t(`${key}Title`)}
      body={t(`${key}Body`)}
      onRetry={wait > 0 ? undefined : onRetry}
    >
      {wait > 0 && (
        <p className="text-sm text-muted" aria-live="polite">
          {t("rateWait", { seconds: toArabicDigits(wait) })}
        </p>
      )}
    </Problem>
  );
}
