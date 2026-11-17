/// Eastern Arabic numerals, counted nouns, and times for the interface.
library;

const _eastern = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];

/// 562 -> "٥٦٢". Non-digits pass through.
String toArabicDigits(Object value) => value.toString().replaceAllMapped(
  RegExp('[0-9]'),
  (m) => _eastern[int.parse(m[0]!)],
);

/// 0.96 -> "٩٦٪"
String formatPercent(double fraction) =>
    '${toArabicDigits((fraction.clamp(0, 1) * 100).round())}٪';

/// 6.4 -> "٠:٠٦"
String formatElapsed(double seconds) {
  final whole = seconds < 0 ? 0 : seconds.floor();
  final rest = (whole % 60).toString().padLeft(2, '0');
  return toArabicDigits('${whole ~/ 60}:$rest');
}

String _counted(int n, String one, String two, String few, String many) {
  if (n == 1) return one;
  if (n == 2) return two;
  return '${toArabicDigits(n)} ${n >= 3 && n <= 10 ? few : many}';
}

/// "آية واحدة", "آيتان", "٧ آيات", "٣٠ آية".
String ayahCount(int count) =>
    _counted(count, 'آية واحدة', 'آيتان', 'آيات', 'آية');

/// "٢٨ موضعًا آخر" with the right noun form.
String otherPlaces(int count) => _counted(
  count,
  'موضع واحد آخر',
  'موضعان آخران',
  'مواضع أخرى',
  'موضعًا آخر',
);

/// "تتكرر ٣١ مرة"
String repeatedTimes(int count) {
  if (count == 2) return 'تتكرر مرتين';
  return 'تتكرر ${toArabicDigits(count)} ${count >= 3 && count <= 10 ? 'مرات' : 'مرة'}';
}

/// "الآن", "منذ ١٠ دقائق", "منذ ساعتين", "منذ ٣ أيام".
String relativeTime(DateTime then, DateTime now) {
  final elapsed = now.difference(then);
  if (elapsed.inMinutes < 1) return 'الآن';
  if (elapsed.inHours < 1) {
    return 'منذ ${_counted(elapsed.inMinutes, 'دقيقة', 'دقيقتين', 'دقائق', 'دقيقة')}';
  }
  if (elapsed.inDays < 1) {
    return 'منذ ${_counted(elapsed.inHours, 'ساعة', 'ساعتين', 'ساعات', 'ساعة')}';
  }
  return 'منذ ${_counted(elapsed.inDays, 'يوم', 'يومين', 'أيام', 'يومًا')}';
}

/// "٢:٤٠ م"
String clockTime(DateTime t) {
  final hour12 = t.hour % 12 == 0 ? 12 : t.hour % 12;
  final minutes = t.minute.toString().padLeft(2, '0');
  return '${toArabicDigits('$hour12:$minutes')} ${t.hour < 12 ? 'ص' : 'م'}';
}

DateTime startOfDay(DateTime t) => DateTime(t.year, t.month, t.day);

/// Whole calendar days between two times (0 = same day).
int daysAgo(DateTime then, DateTime now) =>
    (startOfDay(now).difference(startOfDay(then)).inHours / 24).round();

const _months = [
  'يناير',
  'فبراير',
  'مارس',
  'أبريل',
  'مايو',
  'يونيو',
  'يوليو',
  'أغسطس',
  'سبتمبر',
  'أكتوبر',
  'نوفمبر',
  'ديسمبر',
];

/// "اليوم", "أمس", or "١٤ نوفمبر".
String dayLabel(DateTime t, DateTime now) {
  final ago = daysAgo(t, now);
  if (ago == 0) return 'اليوم';
  if (ago == 1) return 'أمس';
  return '${toArabicDigits(t.day)} ${_months[t.month - 1]}';
}

const _honorifics = {'شيخ', 'الشيخ', 'بن', 'ابن'};

/// Avatar initials (no reciter photos, by design): "محمد صديق المنشاوي" -> "م ص".
String initials(String name) {
  final words = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((w) => w.isNotEmpty && !_honorifics.contains(w))
      .take(2);
  return words
      .map((w) {
        final bare = w.startsWith('ال') ? w.substring(2) : w;
        return (bare.isEmpty ? w : bare).substring(0, 1);
      })
      .join(' ');
}

const styleTab = {
  'murattal': 'المرتّل',
  'mujawwad': 'المجوّد',
  'muallim': 'المعلّم',
};

const styleRecitation = {
  'murattal': 'تلاوة مرتّلة',
  'mujawwad': 'تلاوة مجوّدة',
  'muallim': 'المصحف المعلّم',
};

const revelationLabel = {'meccan': 'مكية', 'medinan': 'مدنية'};

/// Fill a per-ayah audio template: {sss} and {aaa} are zero-padded to 3 digits.
String ayahAudioUrl(String template, int surah, int ayah) => template
    .replaceFirst('{sss}', surah.toString().padLeft(3, '0'))
    .replaceFirst('{aaa}', ayah.toString().padLeft(3, '0'));
