import numpy as np
import pytest

from app.audio.decode import SAMPLE_RATE, AudioError, Waveform, decode_audio
from tests.audio.helpers import dominant_frequency, encode, tone


def decode(data: bytes) -> Waveform:
    return decode_audio(data, max_bytes=2 * 1024 * 1024, max_seconds=15.0)


# What the clients upload: web (Opus in WebM), Safari/iOS (AAC in MP4), plus MP3 and WAV.
FORMATS = [
    ("wav", "pcm_s16le"),
    ("mp3", "libmp3lame"),
    ("webm", "libopus"),
    ("mp4", "aac"),
]


@pytest.mark.parametrize(("container", "codec"), FORMATS)
def test_decodes_every_supported_format(container: str, codec: str) -> None:
    data = encode(tone(4.0), container, codec)
    waveform = decode(data)

    assert waveform.dtype == np.float32
    assert waveform.ndim == 1
    assert abs(len(waveform) / SAMPLE_RATE - 4.0) < 0.15  # codecs add a little padding
    assert float(np.max(np.abs(waveform))) <= 1.0
    assert abs(dominant_frequency(waveform) - 440.0) < 5.0


def test_resamples_48k_stereo_to_16k_mono() -> None:
    data = encode(tone(3.0, rate=48_000), "wav", "pcm_s16le", source_rate=48_000, channels=2)
    waveform = decode(data)
    assert abs(len(waveform) - 3 * SAMPLE_RATE) <= 64
    assert abs(dominant_frequency(waveform) - 440.0) < 2.0
    assert 0.4 < float(np.max(np.abs(waveform))) < 0.6  # stereo was averaged, not summed


def test_mp4_with_index_at_the_end_decodes_from_memory() -> None:
    """iOS writes the MP4 index after the audio; this needs a seekable input."""
    data = encode(tone(3.0), "mp4", "aac")
    assert data.rfind(b"moov") > data.find(b"mdat") > 0
    assert len(decode(data)) > 2.8 * SAMPLE_RATE


@pytest.mark.parametrize(
    "junk", [b"", b"not audio at all", b"\x00" * 4096, b"RIFF\x00\x00\x00\x00WAVE"]
)
def test_undecodable_input(junk: bytes) -> None:
    with pytest.raises(AudioError) as caught:
        decode(junk)
    assert caught.value.reason in ("decode_failed", "no_audio")


def test_truncated_file_does_not_crash() -> None:
    data = encode(tone(4.0), "webm", "libopus")
    try:
        waveform = decode(data[: len(data) // 2])
    except AudioError as exc:
        assert exc.reason in ("decode_failed", "no_audio")
    else:
        assert 0 < len(waveform) < 4 * SAMPLE_RATE


def test_too_large_is_rejected_before_decoding() -> None:
    with pytest.raises(AudioError) as caught:
        decode_audio(b"x" * 1001, max_bytes=1000, max_seconds=15)
    assert caught.value.reason == "too_large"


def test_too_long_is_rejected() -> None:
    data = encode(tone(16.5), "mp3", "libmp3lame")
    with pytest.raises(AudioError) as caught:
        decode(data)
    assert caught.value.reason == "too_long"


def test_exactly_at_the_limit_is_accepted() -> None:
    data = encode(tone(15.0), "wav", "pcm_s16le")
    assert len(decode(data)) == 15 * SAMPLE_RATE
