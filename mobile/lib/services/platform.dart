import 'dart:async';

import 'package:flutter/services.dart';
import 'package:just_audio/just_audio.dart';
import 'package:permission_handler/permission_handler.dart';

enum MicStatus {
  granted,

  /// Not asked yet, or refused once: the OS dialog can still be shown.
  askable,

  /// The OS will not show its dialog again; only app settings can change it.
  blocked,
}

/// Microphone permission. Faked in tests.
abstract class MicPermission {
  Future<MicStatus> status();
  Future<MicStatus> request();
  Future<void> openSettings();
}

class DeviceMicPermission implements MicPermission {
  MicStatus _map(PermissionStatus s) {
    if (s.isGranted) return MicStatus.granted;
    if (s.isPermanentlyDenied || s.isRestricted) return MicStatus.blocked;
    return MicStatus.askable;
  }

  @override
  Future<MicStatus> status() async => _map(await Permission.microphone.status);

  @override
  Future<MicStatus> request() async {
    final result = _map(await Permission.microphone.request());
    // iOS never re-prompts: a refusal there is final until settings change.
    return result;
  }

  @override
  Future<void> openSettings() => openAppSettings();
}

/// Short vibrations on start, stop and result. Faked in tests.
class Haptics {
  const Haptics();
  Future<void> start() => HapticFeedback.mediumImpact();
  Future<void> stop() => HapticFeedback.lightImpact();
  Future<void> result() => HapticFeedback.heavyImpact();
}

/// Plays one audio URL at a time. Faked in tests.
abstract class AudioSink {
  Future<void> playUrl(String url);
  Future<void> pause();
  Future<void> resume();
  Future<void> stop();

  /// Fires each time the current URL finishes playing.
  Stream<void> get completed;
}

class JustAudioSink implements AudioSink {
  JustAudioSink() {
    _player.playerStateStream.listen((state) {
      if (state.processingState == ProcessingState.completed) {
        _completed.add(null);
      }
    });
  }

  final _player = AudioPlayer();
  final _completed = StreamController<void>.broadcast();

  @override
  Stream<void> get completed => _completed.stream;

  @override
  Future<void> playUrl(String url) async {
    await _player.setUrl(url);
    unawaited(_player.play());
  }

  @override
  Future<void> pause() => _player.pause();

  @override
  Future<void> resume() async => unawaited(_player.play());

  @override
  Future<void> stop() => _player.stop();
}
