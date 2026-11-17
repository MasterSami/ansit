"""Synthetic audio for tests. No recitation audio is committed to the repository."""

import io
from typing import Any

import av
import numpy as np

from app.audio.decode import SAMPLE_RATE, Waveform


def tone(seconds: float, freq: float = 440.0, rate: int = SAMPLE_RATE) -> Waveform:
    t = np.arange(int(seconds * rate)) / rate
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def encode(
    waveform: Waveform,
    container_format: str,
    codec: str,
    *,
    source_rate: int = SAMPLE_RATE,
    channels: int = 1,
    bitrate: int = 32_000,
) -> bytes:
    """Encode float32 mono audio into a container, in memory, with PyAV."""
    pcm = (np.clip(waveform, -1, 1) * 32767).astype(np.int16)
    layout = "stereo" if channels == 2 else "mono"
    planes = np.tile(pcm, (channels, 1)) if channels == 2 else pcm.reshape(1, -1)
    packed = planes.T.reshape(1, -1)  # interleaved s16

    buffer = io.BytesIO()
    with av.open(buffer, mode="w", format=container_format) as container:
        rate = 48_000 if codec == "libopus" else source_rate
        stream: Any = container.add_stream(codec, rate=rate)
        stream.layout = layout
        if codec != "pcm_s16le":
            stream.bit_rate = bitrate
        resampler = av.AudioResampler(format=stream.format.name, layout=layout, rate=rate)
        frame = av.AudioFrame.from_ndarray(packed, format="s16", layout=layout)
        frame.sample_rate = source_rate

        fifo = av.AudioFifo()
        for out in [*resampler.resample(frame), *resampler.resample(None)]:
            fifo.write(out)
        size = stream.frame_size or 1024
        while fifo.samples >= size:
            container.mux(stream.encode(fifo.read(size)))
        if fifo.samples:
            container.mux(stream.encode(fifo.read(fifo.samples)))
        container.mux(stream.encode(None))
    return buffer.getvalue()


def dominant_frequency(waveform: Waveform) -> float:
    spectrum = np.abs(np.fft.rfft(waveform))
    return float(np.fft.rfftfreq(len(waveform), 1 / SAMPLE_RATE)[int(np.argmax(spectrum))])
