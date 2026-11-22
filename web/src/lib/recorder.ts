/** Microphone capture with MediaRecorder, plus a live level meter. */

export const MAX_RECORD_SEC = 10;
/** Short clips are more likely to miss the words needed for ayah matching. */
export const MIN_RECORD_SEC = 5;
export const LEVEL_BARS = 8;

const PREFERRED_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4", // Safari
  "audio/ogg;codecs=opus",
];

/** The first container/codec this browser can record, or "" to use its default. */
export function pickMimeType(
  isSupported: (type: string) => boolean = (type) =>
    typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type),
): string {
  return PREFERRED_TYPES.find(isSupported) ?? "";
}

export type MicFailure = "denied" | "unavailable";

/** Classify a getUserMedia error. */
export function micFailure(error: unknown): MicFailure {
  const name =
    error instanceof DOMException || error instanceof Error ? error.name : "";
  return name === "NotAllowedError" || name === "SecurityError"
    ? "denied"
    : "unavailable";
}

export function recordingSupported(): boolean {
  return (
    typeof navigator !== "undefined" &&
    !!navigator.mediaDevices?.getUserMedia &&
    typeof MediaRecorder !== "undefined"
  );
}

/** "granted" | "denied" | "prompt"; "prompt" when the browser cannot say. */
export async function micPermission(): Promise<PermissionState> {
  try {
    const status = await navigator.permissions.query({
      name: "microphone" as PermissionName,
    });
    return status.state;
  } catch {
    return "prompt";
  }
}

/**
 * Turn frequency-bin magnitudes (0-255) into `bars` levels between 0 and 1,
 * weighted towards the voice range so the bars move with recitation.
 */
export function levelsFromSpectrum(
  spectrum: Uint8Array,
  bars: number = LEVEL_BARS,
): number[] {
  const usable = Math.max(bars, Math.floor(spectrum.length * 0.6));
  const size = Math.floor(usable / bars);
  return Array.from({ length: bars }, (_, bar) => {
    let sum = 0;
    for (let i = bar * size; i < (bar + 1) * size; i += 1)
      sum += spectrum[i] ?? 0;
    return Math.min(1, sum / size / 160);
  });
}

export interface Recording {
  /** Stop and get the clip. */
  stop(): Promise<Blob>;
  /** Stop and throw the audio away. */
  cancel(): void;
  /** Current bar levels, 0-1. */
  levels(): number[];
}

export async function startRecording(): Promise<Recording> {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: false,
      noiseSuppression: false,
    },
  });
  const mimeType = pickMimeType();
  const recorder = new MediaRecorder(
    stream,
    mimeType ? { mimeType } : undefined,
  );
  const chunks: Blob[] = [];
  recorder.addEventListener("dataavailable", (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  });

  // Level meter. If Web Audio is unavailable the bars simply stay still.
  let context: AudioContext | null = null;
  let analyser: AnalyserNode | null = null;
  try {
    context = new AudioContext();
    analyser = context.createAnalyser();
    analyser.fftSize = 256;
    context.createMediaStreamSource(stream).connect(analyser);
  } catch {
    analyser = null;
  }
  const spectrum = new Uint8Array(analyser?.frequencyBinCount ?? 0);

  const release = () => {
    stream.getTracks().forEach((track) => track.stop()); // the mic indicator goes off
    void context?.close().catch(() => undefined);
  };

  recorder.start();
  return {
    stop: () =>
      new Promise<Blob>((resolve) => {
        recorder.addEventListener(
          "stop",
          () => {
            release();
            resolve(new Blob(chunks, { type: recorder.mimeType || mimeType }));
          },
          { once: true },
        );
        if (recorder.state === "inactive") {
          release();
          resolve(new Blob(chunks, { type: recorder.mimeType || mimeType }));
        } else {
          recorder.stop();
        }
      }),
    cancel: () => {
      if (recorder.state !== "inactive") recorder.stop();
      release();
    },
    levels: () => {
      if (!analyser) return Array<number>(LEVEL_BARS).fill(0);
      analyser.getByteFrequencyData(spectrum);
      return levelsFromSpectrum(spectrum);
    },
  };
}
