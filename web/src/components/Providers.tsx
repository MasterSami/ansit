"use client";

import { NextIntlClientProvider } from "next-intl";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ayahAudioUrl, getSurahs, type Surah } from "@/lib/api";
import messages from "../../messages/ar.json";

// --------------------------------------------------------------- surah list

const SURAHS_KEY = "ansit.surahs.v1";
const SurahsContext = createContext<Surah[] | null>(null);

/** The 114 surahs (names, ayah counts). Fetched once and kept for offline use. */
export function useSurahs(): Surah[] | null {
  return useContext(SurahsContext);
}

function useLoadSurahs(): Surah[] | null {
  const [surahs, setSurahs] = useState<Surah[] | null>(null);
  useEffect(() => {
    let cancelled = false;
    // Browser storage is only readable after hydration, hence the microtask.
    queueMicrotask(() => {
      try {
        const cached = localStorage.getItem(SURAHS_KEY);
        if (cached && !cancelled)
          setSurahs((current) => current ?? (JSON.parse(cached) as Surah[]));
      } catch {
        // no cache: the network answer below is enough
      }
    });
    getSurahs()
      .then((fresh) => {
        if (cancelled) return;
        setSurahs(fresh);
        try {
          localStorage.setItem(SURAHS_KEY, JSON.stringify(fresh));
        } catch {
          // storage blocked: fine, it is only a cache
        }
      })
      .catch(() => undefined); // offline: the cached copy, if any, stays
    return () => {
      cancelled = true;
    };
  }, []);
  return surahs;
}

// ------------------------------------------------------------------- player

export interface Track {
  reciterId: string;
  reciterName: string;
  /** Per-ayah URL template from /v1/reciters/{id}. */
  template: string;
  surah: number;
  ayah: number;
  /** Stop at the end of this surah instead of going on to the next one. */
  stopAtSurahEnd: boolean;
}

interface Player {
  track: Track | null;
  playing: boolean;
  failed: boolean;
  play(track: Track): void;
  toggle(): void;
  stop(): void;
}

const PlayerContext = createContext<Player | null>(null);

export function usePlayer(): Player {
  const player = useContext(PlayerContext);
  if (!player) throw new Error("usePlayer must be used inside <Providers>");
  return player;
}

function usePlayerState(surahs: Surah[] | null): Player {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [track, setTrack] = useState<Track | null>(null);
  const [playing, setPlaying] = useState(false);
  const [failed, setFailed] = useState(false);
  const trackRef = useRef<Track | null>(null);
  const surahsRef = useRef(surahs);

  useEffect(() => {
    surahsRef.current = surahs;
  }, [surahs]);

  const start = useCallback((next: Track) => {
    const audio = (audioRef.current ??= new Audio());
    trackRef.current = next;
    setTrack(next);
    setFailed(false);
    audio.src = ayahAudioUrl(next.template, next.surah, next.ayah);
    audio.play().then(
      () => setPlaying(true),
      () => {
        setPlaying(false);
        setFailed(true);
      },
    );
  }, []);

  const stop = useCallback(() => {
    audioRef.current?.pause();
    trackRef.current = null;
    setTrack(null);
    setPlaying(false);
    setFailed(false);
  }, []);

  // One audio element for the app; move to the next ayah when one ends.
  useEffect(() => {
    const audio = (audioRef.current ??= new Audio());
    const onEnded = () => {
      const current = trackRef.current;
      if (!current) return;
      const count = surahsRef.current?.[current.surah - 1]?.ayah_count;
      if (count === undefined) return stop();
      if (current.ayah < count)
        return start({ ...current, ayah: current.ayah + 1 });
      if (current.stopAtSurahEnd || current.surah >= 114) return stop();
      start({ ...current, surah: current.surah + 1, ayah: 1 });
    };
    const onError = () => {
      setPlaying(false);
      setFailed(true);
    };
    const onPause = () => setPlaying(false);
    const onPlay = () => setPlaying(true);
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("error", onError);
    audio.addEventListener("pause", onPause);
    audio.addEventListener("play", onPlay);
    return () => {
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("error", onError);
      audio.removeEventListener("pause", onPause);
      audio.removeEventListener("play", onPlay);
      audio.pause();
    };
  }, [start, stop]);

  const toggle = useCallback(() => {
    const audio = audioRef.current;
    if (!audio || !trackRef.current) return;
    if (audio.paused) void audio.play().catch(() => setFailed(true));
    else audio.pause();
  }, []);

  return useMemo(
    () => ({ track, playing, failed, play: start, toggle, stop }),
    [track, playing, failed, start, toggle, stop],
  );
}

// ---------------------------------------------------------------- providers

/** Registers the service worker that makes the app shell work offline. */
function useServiceWorker(): void {
  useEffect(() => {
    if (
      process.env.NODE_ENV !== "production" ||
      !("serviceWorker" in navigator)
    )
      return;
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  }, []);
}

export function Providers({ children }: { children: ReactNode }) {
  const surahs = useLoadSurahs();
  const player = usePlayerState(surahs);
  useServiceWorker();
  return (
    <NextIntlClientProvider locale="ar" messages={messages} timeZone="UTC">
      <SurahsContext.Provider value={surahs}>
        <PlayerContext.Provider value={player}>
          {children}
        </PlayerContext.Provider>
      </SurahsContext.Provider>
    </NextIntlClientProvider>
  );
}
