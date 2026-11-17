from pathlib import Path

import numpy as np
import pytest

from app.audio.decode import SAMPLE_RATE, decode_audio
from app.audio.vad import SpeechDetector

REPO = Path(__file__).resolve().parents[3]
EVAL_CLIPS = REPO / "ml" / "data" / "eval_audio" / "clips"


@pytest.fixture(scope="module")
def detector() -> SpeechDetector:
    return SpeechDetector()


def test_silence_has_no_speech(detector: SpeechDetector) -> None:
    activity = detector.detect(np.zeros(5 * SAMPLE_RATE, dtype=np.float32))
    assert activity.speech_sec == 0.0
    assert (activity.start, activity.end) == (0, 0)


def test_noise_is_mostly_not_speech(detector: SpeechDetector) -> None:
    """The threshold is deliberately permissive (recitation is under-detected), so
    noise is not rejected outright here; the ASR guards are the second line."""
    rng = np.random.default_rng(1)
    noise = (rng.standard_normal(5 * SAMPLE_RATE) * 0.05).astype(np.float32)
    assert detector.detect(noise).speech_sec < 2.5
    assert SpeechDetector(threshold=0.5).detect(noise).speech_sec == 0.0


def test_warm_up_runs(detector: SpeechDetector) -> None:
    detector.warm_up()


def test_recitation_is_detected_and_silence_around_it_is_trimmed(
    detector: SpeechDetector,
) -> None:
    """Needs the locally built eval set (recitation audio is not committed)."""
    clips = sorted(EVAL_CLIPS.glob("*/00_random_08s_clean.wav"))
    if not clips:
        pytest.skip("eval audio not built; run ml/eval/build_audio_eval.py")
    speech = decode_audio(clips[0].read_bytes(), max_bytes=10**7, max_seconds=30)
    pad = np.zeros(2 * SAMPLE_RATE, dtype=np.float32)
    activity = detector.detect(np.concatenate([pad, speech, pad]))

    assert activity.speech_sec > 3.0
    assert 1.0 * SAMPLE_RATE < activity.start < 3.5 * SAMPLE_RATE
    assert 8.5 * SAMPLE_RATE < activity.end <= 12 * SAMPLE_RATE
