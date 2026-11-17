import 'dart:async';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:record/record.dart';

const sampleRate = 16000;

/// The server rejects clips under 3 s, so stopping earlier is not offered.
const minRecordSeconds = 3;
const maxRecordSeconds = 10;

/// Records one clip into memory. Faked in tests.
abstract class ClipRecorder {
  /// Begin capturing. Throws if the microphone cannot be opened.
  Future<void> start();

  /// Loudness of the most recent chunk, 0 to 1.
  Stream<double> get levels;

  /// Stop and return the clip as a WAV file held in memory.
  Future<Uint8List> stop();

  /// Stop and throw the audio away.
  Future<void> cancel();
}

/// Wrap 16-bit mono PCM in a WAV header.
Uint8List wavFromPcm(Uint8List pcm, {int rate = sampleRate}) {
  final header = ByteData(44);
  void ascii(int offset, String s) {
    for (var i = 0; i < s.length; i++) {
      header.setUint8(offset + i, s.codeUnitAt(i));
    }
  }

  ascii(0, 'RIFF');
  header.setUint32(4, 36 + pcm.length, Endian.little);
  ascii(8, 'WAVE');
  ascii(12, 'fmt ');
  header.setUint32(16, 16, Endian.little); // fmt chunk size
  header.setUint16(20, 1, Endian.little); // PCM
  header.setUint16(22, 1, Endian.little); // mono
  header.setUint32(24, rate, Endian.little);
  header.setUint32(28, rate * 2, Endian.little); // bytes per second
  header.setUint16(32, 2, Endian.little); // block align
  header.setUint16(34, 16, Endian.little); // bits per sample
  ascii(36, 'data');
  header.setUint32(40, pcm.length, Endian.little);
  return (BytesBuilder(copy: false)
        ..add(header.buffer.asUint8List())
        ..add(pcm))
      .toBytes();
}

/// Loudness of a chunk of 16-bit little-endian PCM, mapped to 0-1.
double levelFromPcm(Uint8List chunk) {
  final samples = chunk.length ~/ 2;
  if (samples == 0) return 0;
  final data = ByteData.sublistView(chunk);
  var sum = 0.0;
  for (var i = 0; i < samples; i++) {
    final s = data.getInt16(i * 2, Endian.little) / 32768;
    sum += s * s;
  }
  final rms = math.sqrt(sum / samples);
  // Speech at arm's length sits around 0.02-0.2 RMS; stretch that to the bar.
  return (rms * 6).clamp(0.0, 1.0);
}

/// Captures raw PCM as a stream and keeps it in memory only: no audio file is
/// ever created on the device.
class StreamClipRecorder implements ClipRecorder {
  AudioRecorder? _recorder;
  StreamSubscription<Uint8List>? _subscription;
  BytesBuilder _pcm = BytesBuilder(copy: false);
  final _levels = StreamController<double>.broadcast();

  @override
  Stream<double> get levels => _levels.stream;

  @override
  Future<void> start() async {
    await _release();
    _pcm = BytesBuilder(copy: false);
    final recorder = _recorder = AudioRecorder();
    final stream = await recorder.startStream(
      const RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: sampleRate,
        numChannels: 1,
        // Keep the recitation as it sounds: no voice-call processing.
        echoCancel: false,
        noiseSuppress: false,
        autoGain: false,
      ),
    );
    _subscription = stream.listen((chunk) {
      _pcm.add(chunk);
      _levels.add(levelFromPcm(chunk));
    });
  }

  @override
  Future<Uint8List> stop() async {
    await _release();
    final wav = wavFromPcm(_pcm.takeBytes());
    return wav;
  }

  @override
  Future<void> cancel() async {
    await _release();
    _pcm.clear();
  }

  Future<void> _release() async {
    final recorder = _recorder;
    _recorder = null;
    if (recorder != null) {
      try {
        await recorder.stop();
      } finally {
        await _subscription?.cancel();
        _subscription = null;
        await recorder.dispose();
      }
    }
  }
}
