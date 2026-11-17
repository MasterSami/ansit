"""Pipeline tests with a scripted ASR engine and speech detector (no models needed)."""

from pathlib import Path

import pytest

from app.asr.engine import ASRResult
from app.audio.decode import SAMPLE_RATE, AudioError, Waveform
from app.audio.vad import SpeechActivity
from app.matcher.index import QuranIndex
from app.matcher.search import AyahMatcher
from app.pipeline import AudioLimits, AyahIdentifier
from tests.audio.helpers import encode, tone


class ScriptedASR:
    def __init__(self, text: str, logprob: float = -0.05, no_speech: float = 0.0) -> None:
        self.result = ASRResult(text, logprob, no_speech, 12.0, 1.1)
        self.received: list[Waveform] = []

    def transcribe(self, waveform_16k: Waveform) -> ASRResult:
        self.received.append(waveform_16k)
        return self.result


class ScriptedVAD:
    """Reports `speech_sec` of speech in the middle of whatever it is given."""

    def __init__(self, speech_sec: float, trim: int = 0) -> None:
        self.speech_sec, self.trim = speech_sec, trim

    def detect(self, waveform: Waveform) -> SpeechActivity:
        return SpeechActivity(self.speech_sec, self.trim, len(waveform) - self.trim)


def clip(seconds: float, container: str = "webm", codec: str = "libopus") -> bytes:
    return encode(tone(seconds), container, codec)


def build(
    matcher: AyahMatcher,
    asr: ScriptedASR,
    speech_sec: float = 6.0,
    trim: int = 0,
    limits: AudioLimits | None = None,
) -> AyahIdentifier:
    vad = ScriptedVAD(speech_sec, trim)
    return AyahIdentifier(asr, matcher, vad, limits or AudioLimits())  # type: ignore[arg-type]


def ayah_text(index: QuranIndex, surah: int, ayah: int) -> str:
    return " ".join(index.ayahs[index.ayah_index(surah, ayah)].words)


def test_match(index: QuranIndex, matcher: AyahMatcher) -> None:
    asr = ScriptedASR(ayah_text(index, 67, 1))
    out = build(matcher, asr).identify(clip(8.0))

    assert out.status == "match"
    assert out.reason is None
    assert out.match is not None and out.match.best is not None
    assert (out.match.best.start.surah, out.match.best.start.ayah) == (67, 1)
    assert abs(out.clip_sec - 8.0) < 0.2
    assert out.speech_sec == 6.0
    assert set(out.timings_ms) == {"decode", "vad", "asr", "match", "total"}
    assert out.timings_ms["total"] >= out.timings_ms["decode"]


def test_ambiguous(index: QuranIndex, matcher: AyahMatcher) -> None:
    out = build(matcher, ScriptedASR(ayah_text(index, 55, 13))).identify(clip(6.0))
    assert out.status == "ambiguous"
    assert out.match is not None and out.match.repeated_count == 31


def test_whole_clip_goes_to_asr_by_default(index: QuranIndex, matcher: AyahMatcher) -> None:
    """Regression: trimming to the detected speech region cut real recitation."""
    asr = ScriptedASR(ayah_text(index, 67, 1))
    build(matcher, asr, trim=SAMPLE_RATE).identify(clip(8.0, "wav", "pcm_s16le"))
    assert len(asr.received) == 1
    assert len(asr.received[0]) == 8 * SAMPLE_RATE


def test_trimming_can_be_enabled(index: QuranIndex, matcher: AyahMatcher) -> None:
    asr = ScriptedASR(ayah_text(index, 67, 1))
    limits = AudioLimits(trim_silence=True)
    build(matcher, asr, trim=SAMPLE_RATE, limits=limits).identify(clip(8.0, "wav", "pcm_s16le"))
    assert len(asr.received[0]) == 6 * SAMPLE_RATE  # one second trimmed from each end


def test_clip_shorter_than_minimum(index: QuranIndex, matcher: AyahMatcher) -> None:
    asr = ScriptedASR(ayah_text(index, 67, 1))
    out = build(matcher, asr).identify(clip(2.0, "wav", "pcm_s16le"))
    assert (out.status, out.reason) == ("no_match", "too_short")
    assert asr.received == []  # rejected before any model ran
    assert "asr" not in out.timings_ms


def test_too_little_speech(index: QuranIndex, matcher: AyahMatcher) -> None:
    asr = ScriptedASR(ayah_text(index, 67, 1))
    out = build(matcher, asr, speech_sec=1.2).identify(clip(8.0))
    assert (out.status, out.reason) == ("no_match", "no_speech")
    assert asr.received == []
    assert out.speech_sec == 1.2


@pytest.mark.parametrize(
    ("asr", "reason", "flag"),
    [
        (ScriptedASR(""), "no_speech", "empty"),
        (ScriptedASR("placeholder", no_speech=0.95), "no_speech", "empty"),
        (ScriptedASR("PLACEHOLDER_AYAH", no_speech=0.95), "no_speech", "no_speech"),
        (ScriptedASR("PLACEHOLDER_AYAH", logprob=-1.8), "low_confidence", "low_logprob"),
    ],
)
def test_guarded_asr_output_is_not_matched(
    index: QuranIndex, matcher: AyahMatcher, asr: ScriptedASR, reason: str, flag: str
) -> None:
    if asr.result.text == "PLACEHOLDER_AYAH":  # a real ayah the matcher WOULD find
        asr.result = ASRResult(
            ayah_text(index, 67, 1), asr.result.avg_logprob, asr.result.no_speech_prob, 12.0, 1.1
        )
    out = build(matcher, asr).identify(clip(8.0))
    assert (out.status, out.reason) == ("no_match", reason)
    assert flag in out.guard_flags
    assert out.match is None
    assert "match" not in out.timings_ms


def test_transcript_that_is_not_quran(matcher: AyahMatcher, index: QuranIndex) -> None:
    shuffled = " ".join(index.words[i] for i in range(100, 60_000, 4_700))
    out = build(matcher, ScriptedASR(shuffled)).identify(clip(8.0))
    assert (out.status, out.reason) == ("no_match", "low_confidence")
    assert out.guard_flags == []


def test_unusable_uploads_raise(index: QuranIndex, matcher: AyahMatcher) -> None:
    identifier = build(matcher, ScriptedASR(ayah_text(index, 67, 1)))
    with pytest.raises(AudioError, match="decode_failed"):
        identifier.identify(b"definitely not audio")
    with pytest.raises(AudioError, match="too_long"):
        identifier.identify(clip(16.5, "mp3", "libmp3lame"))
    small = AyahIdentifier(
        identifier.asr, matcher, identifier.vad, AudioLimits(max_upload_bytes=1000)
    )
    with pytest.raises(AudioError, match="too_large"):
        small.identify(clip(5.0, "wav", "pcm_s16le"))


def test_identify_writes_nothing_to_disk(
    index: QuranIndex, matcher: AyahMatcher, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Privacy: the clip is processed in memory; no temp file is ever created."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    build(matcher, ScriptedASR(ayah_text(index, 67, 1))).identify(clip(8.0, "mp4", "aac"))
    assert list(tmp_path.iterdir()) == []


# --- the real models, only where they have been built locally ---

REPO = Path(__file__).resolve().parents[2]
MODEL = REPO / "ml" / "artifacts" / "asr" / "tarteel-base"
CLIPS = REPO / "ml" / "data" / "eval_audio" / "clips" / "Alafasy_64kbps"


def test_real_models_identify_a_recitation(matcher: AyahMatcher, index: QuranIndex) -> None:
    import json

    from app.asr.faster_whisper_engine import FasterWhisperEngine
    from app.audio.vad import SpeechDetector

    manifest = REPO / "ml" / "data" / "eval_audio" / "manifest.jsonl"
    if not (MODEL / "model.bin").is_file() or not manifest.is_file():
        pytest.skip("ASR model or eval audio not built locally")
    rows = [json.loads(line) for line in manifest.read_text().splitlines()]
    row = next(
        r
        for r in rows
        if r["reciter"] == "Alafasy_64kbps" and r["condition"] == "phone" and r["duration"] == 12.0
    )
    identifier = AyahIdentifier(
        FasterWhisperEngine(MODEL, cpu_threads=2), matcher, SpeechDetector()
    )
    out = identifier.identify((manifest.parent / row["path"]).read_bytes())

    assert out.status in ("match", "ambiguous")
    assert out.match is not None and out.match.best is not None
    best = index.ayahs[out.match.best.ayah_idx]
    assert f"{best.surah}:{best.ayah}" in row["overlaps"]
