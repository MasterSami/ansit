import 'dart:io' show Platform;
import 'dart:typed_data';

import 'package:dio/dio.dart';

import 'models.dart';

/// What went wrong, in terms the UI can act on.
enum ApiFailure { offline, rateLimited, busy, badAudio, server }

class ApiException implements Exception {
  const ApiException(this.kind, {this.status, this.retryAfter});

  final ApiFailure kind;
  final int? status;

  /// Seconds to wait before retrying, when the server said so.
  final int? retryAfter;

  @override
  String toString() => 'ApiException($kind, status: $status)';
}

ApiFailure failureForStatus(int status) => switch (status) {
  429 => ApiFailure.rateLimited,
  413 || 422 => ApiFailure.badAudio,
  503 => ApiFailure.busy,
  _ => ApiFailure.server,
};

/// The interface the app needs from the server. Faked in tests.
abstract class AnsitApi {
  Future<IdentifyResponse> identify(
    Uint8List wav, {
    String? previousIdentifyId,
    CancelToken? cancel,
  });
  Future<List<Surah>> surahs();
  Future<Ayah> ayah(int surah, int ayah);
  Future<List<ReciterSummary>> reciters();
  Future<ReciterDetail> reciter(String id);
  Future<void> sendFeedback(FeedbackReport feedback);
}

class HttpAnsitApi implements AnsitApi {
  HttpAnsitApi({required String baseUrl, required this.deviceId, Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: baseUrl,
              connectTimeout: const Duration(seconds: 10),
              sendTimeout: const Duration(seconds: 30),
              receiveTimeout: const Duration(seconds: 30),
            ),
          );

  final Dio _dio;

  /// A random id kept on this device; the server uses it only to rate-limit.
  final String deviceId;

  Future<T> _guard<T>(Future<T> Function() call) async {
    try {
      return await call();
    } on DioException catch (e) {
      if (CancelToken.isCancel(e)) rethrow;
      final response = e.response;
      if (response == null) throw const ApiException(ApiFailure.offline);
      final status = response.statusCode ?? 500;
      final header = response.headers.value('retry-after');
      throw ApiException(
        failureForStatus(status),
        status: status,
        retryAfter: header == null ? null : int.tryParse(header),
      );
    }
  }

  @override
  Future<IdentifyResponse> identify(
    Uint8List wav, {
    String? previousIdentifyId,
    CancelToken? cancel,
  }) => _guard(() async {
    final form = FormData.fromMap({
      // Built from memory: the clip is never written to disk on the device.
      'audio': MultipartFile.fromBytes(wav, filename: 'clip.wav'),
      'client': Platform.isIOS ? 'ios' : 'android',
      'previous_identify_id': ?previousIdentifyId,
    });
    final response = await _dio.post<Json>(
      '/v1/identify',
      data: form,
      options: Options(headers: {'X-Device-ID': deviceId}),
      cancelToken: cancel,
    );
    return IdentifyResponse.fromJson(response.data!);
  });

  @override
  Future<List<Surah>> surahs() => _guard(() async {
    final response = await _dio.get<Json>('/v1/surahs');
    return [
      for (final s in response.data!['surahs'] as List)
        Surah.fromJson(s as Json),
    ];
  });

  @override
  Future<Ayah> ayah(int surah, int ayah) => _guard(() async {
    final response = await _dio.get<Json>('/v1/ayahs/$surah/$ayah');
    return Ayah.fromJson(response.data!['ayah'] as Json);
  });

  @override
  Future<List<ReciterSummary>> reciters() => _guard(() async {
    final response = await _dio.get<Json>('/v1/reciters');
    return [
      for (final r in response.data!['reciters'] as List)
        ReciterSummary.fromJson(r as Json),
    ];
  });

  @override
  Future<ReciterDetail> reciter(String id) => _guard(() async {
    final response = await _dio.get<Json>(
      '/v1/reciters/${Uri.encodeComponent(id)}',
    );
    return ReciterDetail.fromJson(response.data!);
  });

  @override
  Future<void> sendFeedback(FeedbackReport feedback) => _guard(() async {
    await _dio.post<Json>('/v1/feedback', data: feedback.toJson());
  });
}
