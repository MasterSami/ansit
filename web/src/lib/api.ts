/** Typed client for the Ansit backend (docs/API.md). */

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export type Style = "murattal" | "mujawwad" | "muallim";

export interface Ayah {
  surah: number;
  surah_name_ar: string;
  surah_name_en: string;
  ayah: number;
  text_uthmani: string;
  juz: number;
  page: number;
  revelation: "meccan" | "medinan";
  ayah_count: number;
}

export interface Tafsir {
  surah: number;
  ayah: number;
  text: string;
  source_key: string;
  book: string;
  author: string;
  publisher: string;
  version: string;
  source_url: string;
  attribution: string;
}

export interface Candidate {
  surah: number;
  surah_name_ar: string;
  ayah: number;
  score: number;
  context_before: string | null;
}

export interface ReciterAlternative {
  id: string;
  name_ar: string;
  name_en: string;
  style: Style;
  similarity: number;
}

export interface ReciterResult {
  status: "identified" | "unknown";
  id: string | null;
  name_ar: string | null;
  name_en: string | null;
  style: Style | null;
  similarity: number | null;
  alternatives: ReciterAlternative[];
}

export interface IdentifyResponse {
  id: string;
  status: "match" | "ambiguous" | "no_match";
  reason: "no_speech" | "too_short" | "low_confidence" | null;
  ayah: Ayah | null;
  text_confidence: number | null;
  candidates: Candidate[];
  repeated_count: number | null;
  reciter: ReciterResult | null;
}

export interface Surah {
  number: number;
  name_ar: string;
  name_en: string;
  ayah_count: number;
  revelation: "meccan" | "medinan";
}

export interface ReciterSummary {
  id: string;
  name_ar: string;
  name_en: string;
  country: string | null;
  styles: Style[];
  /** True when the voice gallery holds this reciter. Absent on older servers. */
  recognition_enabled?: boolean;
}

export interface ReciterDetail extends ReciterSummary {
  ayah_audio: { style: Style; url_template: string; url: string | null }[];
  /** Full-surah recordings; `{sss}` is the zero-padded surah number. */
  surah_audio?: { style: Style; url_template: string; surah_total: number }[];
}

export interface FeedbackBody {
  identify_id: string;
  kind: "wrong_ayah" | "wrong_reciter" | "other";
  correct_surah?: number;
  correct_ayah?: number;
  correct_reciter_id?: string;
}

/** What went wrong, in terms the UI can act on. */
export type ApiErrorKind =
  "offline" | "rate_limited" | "busy" | "bad_audio" | "server";

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    readonly status: number | null = null,
    /** Seconds to wait before retrying, when the server said so. */
    readonly retryAfter: number | null = null,
  ) {
    super(kind);
    this.name = "ApiError";
  }
}

/** Map an HTTP status to the kind of failure the UI should show. */
export function errorKindForStatus(status: number): ApiErrorKind {
  if (status === 429) return "rate_limited";
  if (status === 413 || status === 422) return "bad_audio";
  if (status === 503) return "busy";
  return "server";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, init);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    // fetch only rejects when no response arrived at all: no network, DNS, CORS.
    throw new ApiError("offline");
  }
  if (!response.ok) {
    const header = response.headers.get("Retry-After");
    const retryAfter = header && /^\d+$/.test(header) ? Number(header) : null;
    throw new ApiError(
      errorKindForStatus(response.status),
      response.status,
      retryAfter,
    );
  }
  return (await response.json()) as T;
}

const DEVICE_KEY = "ansit.device";

/** A random id kept in this browser, used by the server only for rate limiting. */
export function deviceId(): string | null {
  try {
    let id = localStorage.getItem(DEVICE_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(DEVICE_KEY, id);
    }
    return id;
  } catch {
    return null; // storage blocked: the server falls back to per-IP limits
  }
}

export function fileNameFor(mimeType: string): string {
  if (mimeType.includes("webm")) return "clip.webm";
  if (mimeType.includes("mp4") || mimeType.includes("aac")) return "clip.m4a";
  if (mimeType.includes("ogg")) return "clip.ogg";
  if (mimeType.includes("wav")) return "clip.wav";
  return "clip.bin";
}

export function identify(
  clip: Blob,
  options: { previousIdentifyId?: string | null; signal?: AbortSignal } = {},
): Promise<IdentifyResponse> {
  const form = new FormData();
  form.append("audio", clip, fileNameFor(clip.type));
  form.append("client", "web");
  if (options.previousIdentifyId) {
    form.append("previous_identify_id", options.previousIdentifyId);
  }
  const headers: Record<string, string> = {};
  const device = deviceId();
  if (device) headers["X-Device-ID"] = device;
  return request<IdentifyResponse>("/v1/identify", {
    method: "POST",
    body: form,
    headers,
    signal: options.signal,
  });
}

export async function getSurahs(): Promise<Surah[]> {
  return (await request<{ surahs: Surah[] }>("/v1/surahs")).surahs;
}

export async function getAyah(surah: number, ayah: number): Promise<Ayah> {
  return (await request<{ ayah: Ayah }>(`/v1/ayahs/${surah}/${ayah}`)).ayah;
}

export function getTafsir(
  surah: number,
  ayah: number,
  source = "arabic_moyassar",
): Promise<Tafsir> {
  return request<Tafsir>(
    `/v1/tafsir/${surah}/${ayah}?source=${encodeURIComponent(source)}`,
  );
}

export async function getReciters(): Promise<ReciterSummary[]> {
  return (await request<{ reciters: ReciterSummary[] }>("/v1/reciters"))
    .reciters;
}

export function getReciter(id: string): Promise<ReciterDetail> {
  return request<ReciterDetail>(`/v1/reciters/${encodeURIComponent(id)}`);
}

export async function sendFeedback(body: FeedbackBody): Promise<void> {
  await request<{ stored: boolean }>("/v1/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

/** Fill a per-ayah audio template: {sss} and {aaa} are zero-padded to 3 digits. */
export function ayahAudioUrl(
  template: string,
  surah: number,
  ayah: number,
): string {
  return template
    .replace("{sss}", String(surah).padStart(3, "0"))
    .replace("{aaa}", String(ayah).padStart(3, "0"));
}
