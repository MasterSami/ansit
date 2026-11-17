/// Plain data classes for the Ansit API (see docs/API.md).
library;

typedef Json = Map<String, dynamic>;

class Ayah {
  const Ayah({
    required this.surah,
    required this.surahNameAr,
    required this.surahNameEn,
    required this.ayah,
    required this.textUthmani,
    required this.juz,
    required this.page,
    required this.revelation,
    required this.ayahCount,
  });

  factory Ayah.fromJson(Json j) => Ayah(
    surah: j['surah'] as int,
    surahNameAr: j['surah_name_ar'] as String,
    surahNameEn: j['surah_name_en'] as String,
    ayah: j['ayah'] as int,
    textUthmani: j['text_uthmani'] as String,
    juz: j['juz'] as int,
    page: j['page'] as int,
    revelation: j['revelation'] as String,
    ayahCount: j['ayah_count'] as int,
  );

  final int surah;
  final String surahNameAr;
  final String surahNameEn;
  final int ayah;

  /// Verbatim from the server (Tanzil Uthmani text). Never edited in the app.
  final String textUthmani;
  final int juz;
  final int page;
  final String revelation;
  final int ayahCount;

  Json toJson() => {
    'surah': surah,
    'surah_name_ar': surahNameAr,
    'surah_name_en': surahNameEn,
    'ayah': ayah,
    'text_uthmani': textUthmani,
    'juz': juz,
    'page': page,
    'revelation': revelation,
    'ayah_count': ayahCount,
  };
}

class Candidate {
  const Candidate({
    required this.surah,
    required this.surahNameAr,
    required this.ayah,
    required this.score,
    this.contextBefore,
  });

  factory Candidate.fromJson(Json j) => Candidate(
    surah: j['surah'] as int,
    surahNameAr: j['surah_name_ar'] as String,
    ayah: j['ayah'] as int,
    score: (j['score'] as num).toDouble(),
    contextBefore: j['context_before'] as String?,
  );

  final int surah;
  final String surahNameAr;
  final int ayah;
  final double score;
  final String? contextBefore;

  Json toJson() => {
    'surah': surah,
    'surah_name_ar': surahNameAr,
    'ayah': ayah,
    'score': score,
    'context_before': contextBefore,
  };
}

class ReciterAlternative {
  const ReciterAlternative({
    required this.id,
    required this.nameAr,
    required this.style,
    required this.similarity,
  });

  factory ReciterAlternative.fromJson(Json j) => ReciterAlternative(
    id: j['id'] as String,
    nameAr: j['name_ar'] as String,
    style: j['style'] as String,
    similarity: (j['similarity'] as num).toDouble(),
  );

  final String id;
  final String nameAr;
  final String style;
  final double similarity;

  Json toJson() => {
    'id': id,
    'name_ar': nameAr,
    'style': style,
    'similarity': similarity,
  };
}

class ReciterResult {
  const ReciterResult({
    required this.identified,
    this.id,
    this.nameAr,
    this.style,
    this.similarity,
    this.alternatives = const [],
  });

  factory ReciterResult.fromJson(Json j) => ReciterResult(
    identified: j['status'] == 'identified',
    id: j['id'] as String?,
    nameAr: j['name_ar'] as String?,
    style: j['style'] as String?,
    similarity: (j['similarity'] as num?)?.toDouble(),
    alternatives: [
      for (final a in (j['alternatives'] as List? ?? const []))
        ReciterAlternative.fromJson(a as Json),
    ],
  );

  final bool identified;
  final String? id;
  final String? nameAr;
  final String? style;
  final double? similarity;
  final List<ReciterAlternative> alternatives;

  Json toJson() => {
    'status': identified ? 'identified' : 'unknown',
    'id': id,
    'name_ar': nameAr,
    'style': style,
    'similarity': similarity,
    'alternatives': [for (final a in alternatives) a.toJson()],
  };
}

class IdentifyResponse {
  const IdentifyResponse({
    required this.id,
    required this.status,
    this.reason,
    this.ayah,
    this.textConfidence,
    this.candidates = const [],
    this.repeatedCount,
    this.reciter,
  });

  factory IdentifyResponse.fromJson(Json j) => IdentifyResponse(
    id: j['id'] as String,
    status: j['status'] as String,
    reason: j['reason'] as String?,
    ayah: j['ayah'] == null ? null : Ayah.fromJson(j['ayah'] as Json),
    textConfidence: (j['text_confidence'] as num?)?.toDouble(),
    candidates: [
      for (final c in (j['candidates'] as List? ?? const []))
        Candidate.fromJson(c as Json),
    ],
    repeatedCount: j['repeated_count'] as int?,
    reciter: j['reciter'] == null
        ? null
        : ReciterResult.fromJson(j['reciter'] as Json),
  );

  final String id;

  /// "match" | "ambiguous" | "no_match"
  final String status;

  /// "no_speech" | "too_short" | "low_confidence" when there is no match.
  final String? reason;
  final Ayah? ayah;
  final double? textConfidence;
  final List<Candidate> candidates;
  final int? repeatedCount;
  final ReciterResult? reciter;
}

class Surah {
  const Surah({
    required this.number,
    required this.nameAr,
    required this.ayahCount,
  });

  factory Surah.fromJson(Json j) => Surah(
    number: j['number'] as int,
    nameAr: j['name_ar'] as String,
    ayahCount: j['ayah_count'] as int,
  );

  final int number;
  final String nameAr;
  final int ayahCount;
}

class ReciterSummary {
  const ReciterSummary({
    required this.id,
    required this.nameAr,
    this.country,
    this.styles = const [],
  });

  factory ReciterSummary.fromJson(Json j) => ReciterSummary(
    id: j['id'] as String,
    nameAr: j['name_ar'] as String,
    country: j['country'] as String?,
    styles: [for (final s in (j['styles'] as List? ?? const [])) s as String],
  );

  final String id;
  final String nameAr;
  final String? country;
  final List<String> styles;
}

class ReciterDetail extends ReciterSummary {
  const ReciterDetail({
    required super.id,
    required super.nameAr,
    super.country,
    super.styles,
    this.audioTemplates = const {},
  });

  factory ReciterDetail.fromJson(Json j) {
    final summary = ReciterSummary.fromJson(j);
    return ReciterDetail(
      id: summary.id,
      nameAr: summary.nameAr,
      country: summary.country,
      styles: summary.styles,
      audioTemplates: {
        for (final a in (j['ayah_audio'] as List? ?? const []))
          (a as Json)['style'] as String: a['url_template'] as String,
      },
    );
  }

  /// Per-ayah audio URL template for each style.
  final Map<String, String> audioTemplates;
}

class FeedbackReport {
  const FeedbackReport({
    required this.identifyId,
    required this.kind,
    this.correctSurah,
    this.correctAyah,
    this.correctReciterId,
  });

  final String identifyId;

  /// "wrong_ayah" | "wrong_reciter" | "other"
  final String kind;
  final int? correctSurah;
  final int? correctAyah;
  final String? correctReciterId;

  Json toJson() => {
    'identify_id': identifyId,
    'kind': kind,
    'correct_surah': ?correctSurah,
    'correct_ayah': ?correctAyah,
    'correct_reciter_id': ?correctReciterId,
  };
}
