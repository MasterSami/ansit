// ignore: unused_import
import 'package:intl/intl.dart' as intl;

import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Arabic (`ar`).
class AppLocalizationsAr extends AppLocalizations {
  AppLocalizationsAr([String locale = 'ar']) : super(locale);

  @override
  String ambiguousAfter(String text) {
    return 'بعد ﴿$text﴾';
  }

  @override
  String ambiguousAyah(String ayah) {
    return 'الآية $ayah';
  }

  @override
  String get ambiguousConfirm => 'تأكيد الموضع المختار';

  @override
  String get ambiguousConfirmFailed =>
      'تعذّر التأكيد. تحقّق من الاتصال وحاول مرة أخرى.';

  @override
  String get ambiguousExplain =>
      'تعرّفنا على الآية بثقة، لكنها تتكرر. أنصت لثوانٍ أطول لنحدّد موضعها من الآيات المجاورة، أو اختر الموضع بنفسك.';

  @override
  String get ambiguousFirstOfSurah => 'أول السورة';

  @override
  String get ambiguousHeardSection => 'الآية المسموعة';

  @override
  String get ambiguousListenMore => 'أنصت ١٠ ثوانٍ إضافية';

  @override
  String ambiguousMore(String count) {
    return 'و$count';
  }

  @override
  String get ambiguousPlaces => 'المواضع المحتملة';

  @override
  String ambiguousSurahAyah(String ayah, String surah) {
    return '$surah · الآية $ayah';
  }

  @override
  String get ambiguousTitle => 'تحديد موضع الآية';

  @override
  String get appDescription =>
      'تعرّف على السورة والآية واسم القارئ من ثوانٍ من التلاوة';

  @override
  String get appName => 'أنصِت';

  @override
  String get appVerse => '﴿فَاسْتَمِعُوا لَهُ وَأَنصِتُوا﴾';

  @override
  String get commonBack => 'رجوع';

  @override
  String get commonCancel => 'إلغاء';

  @override
  String get commonClose => 'إغلاق';

  @override
  String get commonHome => 'العودة للرئيسية';

  @override
  String get commonRetry => 'حاول مرة أخرى';

  @override
  String get commonSoon => 'قريبًا';

  @override
  String get feedbackAyahNumber => 'رقم الآية';

  @override
  String get feedbackChooseReciter => 'اختر القارئ الصحيح';

  @override
  String get feedbackFailed => 'تعذّر الإرسال. حاول مرة أخرى.';

  @override
  String get feedbackNoReciters =>
      'قائمة القرّاء غير متاحة الآن. يمكنك إرسال الملاحظة بدون اختيار قارئ.';

  @override
  String get feedbackNote =>
      'نرسل الملاحظة فقط، ولا يوجد تسجيل محفوظ مرتبط بها.';

  @override
  String get feedbackOptional => 'اختياري';

  @override
  String get feedbackOther => 'شيء آخر';

  @override
  String get feedbackReciterTitle => 'من هو القارئ؟';

  @override
  String get feedbackSend => 'إرسال';

  @override
  String get feedbackSending => 'جارٍ الإرسال…';

  @override
  String get feedbackSurahNumber => 'رقم السورة';

  @override
  String get feedbackThanks => 'شكرًا، وصلتنا ملاحظتك';

  @override
  String get feedbackTitle => 'ما الخطأ في النتيجة؟';

  @override
  String get feedbackWrongAyah => 'الآية خاطئة';

  @override
  String get feedbackWrongReciter => 'القارئ خاطئ';

  @override
  String get historyAll => 'الكل';

  @override
  String get historyEmptyBody =>
      'كل تلاوة تتعرّف عليها تُحفظ هنا على جهازك فقط.';

  @override
  String get historyEmptySavedBody => 'اضغط «حفظ» في أي نتيجة لتجدها هنا.';

  @override
  String get historyEmptySavedTitle => 'لا محفوظات بعد';

  @override
  String get historyEmptyTitle => 'سجلّك فارغ';

  @override
  String get historyFilters => 'تصفية';

  @override
  String get historyNoResultsBody => 'جرّب كلمة أخرى أو غيّر التصفية.';

  @override
  String get historyNoResultsTitle => 'لا نتائج';

  @override
  String get historySaved => 'المحفوظة';

  @override
  String get historySavedTitle => 'المحفوظات';

  @override
  String get historySearchLabel => 'ابحث في السجل';

  @override
  String get historySearchPlaceholder => 'ابحث بسورة أو قارئ';

  @override
  String get historyStartListening => 'ابدأ الإنصات';

  @override
  String get historyTitle => 'السجل';

  @override
  String get historyToday => 'اليوم';

  @override
  String get historyUnknown => 'قارئ غير معروف · أضِف الاسم';

  @override
  String get historyWeek => 'هذا الأسبوع';

  @override
  String get homeLastHeard => 'آخر ما سمعته';

  @override
  String get homeNothingYet => 'لا شيء بعد. اضغط الزر وقرّب الهاتف من التلاوة.';

  @override
  String get homeOpen => 'فتح النتيجة';

  @override
  String get homeSettings => 'الإعدادات';

  @override
  String get homeShowHistory => 'عرض السجل';

  @override
  String get homeSubtitle => 'نتعرّف على السورة والآية واسم القارئ في ثوانٍ';

  @override
  String homeSurahAyah(String ayah, String surah) {
    return 'سورة $surah · الآية $ayah';
  }

  @override
  String get homeTapToListen => 'اضغط لتنصت';

  @override
  String get listenContinuing => 'نكمل الإنصات لتحديد الموضع';

  @override
  String get listenDone => 'تم';

  @override
  String get listenElapsed => 'مدة التسجيل';

  @override
  String get listenHint =>
      'قرّب الهاتف من مصدر الصوت، ويكفي ٥ إلى ١٠ ثوانٍ من التلاوة';

  @override
  String get listenIdentifying => 'جارٍ التعرّف…';

  @override
  String get listenIdentifyingHint => 'لحظات ونخبرك بالسورة والآية والقارئ';

  @override
  String get listenInProgress => 'جارٍ';

  @override
  String get listenListening => 'جارٍ الإنصات…';

  @override
  String get listenStepCapture => 'التقاط الصوت وتنقيته';

  @override
  String get listenStepMatch => 'مطابقة النص بآيات المصحف';

  @override
  String get listenStepReciter => 'التعرّف على صوت القارئ';

  @override
  String get listenSteps => 'مراحل التعرّف';

  @override
  String get listenStop => 'إيقاف';

  @override
  String get listenWave => 'موجة الصوت';

  @override
  String get mushafAyah => 'الآية';

  @override
  String get mushafBody => 'اختر سورة ورقم آية لعرضها وفتح تفسيرها.';

  @override
  String get mushafHideTafsir => 'إخفاء التفسير';

  @override
  String get mushafLoadFailed =>
      'تعذّر تحميل الآية أو التفسير. تحقّق من الاتصال وحاول مجددًا.';

  @override
  String get mushafLoading => 'جارٍ التحميل…';

  @override
  String get mushafOpenAyah => 'عرض الآية';

  @override
  String get mushafShowTafsir => 'عرض التفسير';

  @override
  String get mushafSurah => 'السورة';

  @override
  String get mushafTitle => 'المصحف';

  @override
  String get navHistory => 'السجل';

  @override
  String get navLabel => 'التنقل الرئيسي';

  @override
  String get navListen => 'أنصِت';

  @override
  String get navMushaf => 'المصحف';

  @override
  String get navSaved => 'المحفوظات';

  @override
  String get offlineBanner =>
      'أنت غير متصل. السجل متاح، والتعرّف يحتاج اتصالًا.';

  @override
  String get permissionAllow => 'السماح بالمايكروفون';

  @override
  String get permissionAnySourceBody => 'راديو، مسجد، تلفاز، أو هاتف آخر';

  @override
  String get permissionAnySourceTitle => 'من أي مصدر';

  @override
  String get permissionDeletedBody =>
      'نحتفظ بالنتيجة في سجلّك فقط، لا بالتسجيل';

  @override
  String get permissionDeletedTitle => 'المقطع يُحذف بعد التعرّف';

  @override
  String get permissionNotNow => 'ليس الآن';

  @override
  String get permissionOnlyWhenBody =>
      'لا استماع في الخلفية، ويتوقف تلقائيًا بعد التعرّف';

  @override
  String get permissionOnlyWhenTitle => 'يعمل فقط حين تضغط «أنصِت»';

  @override
  String get permissionStep => 'الخطوة ٣ من ٣';

  @override
  String get permissionSubtitle => 'حتى نتعرّف على التلاوة التي تسمعها حولك';

  @override
  String get permissionTitle => 'نحتاج إذن المايكروفون لنُنصت معك';

  @override
  String get playerFailed => 'تعذّر تشغيل التلاوة';

  @override
  String get playerLabel => 'مشغّل التلاوة';

  @override
  String get playerNoAyahAudio =>
      'لا تتوفر لهذا القارئ تلاوة مقسّمة بالآيات حتى الآن';

  @override
  String playerNowPlaying(String ayah, String surah) {
    return 'سورة $surah · الآية $ayah';
  }

  @override
  String playerNowPlayingSurah(String surah) {
    return 'سورة $surah';
  }

  @override
  String get playerPause => 'إيقاف مؤقت';

  @override
  String get playerPlay => 'تشغيل';

  @override
  String get playerStop => 'إيقاف التشغيل';

  @override
  String get playerWholeSurah =>
      'لا تتوفر لهذا القارئ تلاوة مقسّمة بالآيات، فبدأ التشغيل من أول السورة.';

  @override
  String get reciterFavourite => 'إضافة إلى القرّاء المفضّلين';

  @override
  String get reciterHeardToday => 'تعرّفت عليها اليوم';

  @override
  String get reciterLoadFailedTitle => 'تعذّر تحميل صفحة القارئ';

  @override
  String get reciterNotFoundTitle => 'القارئ غير موجود';

  @override
  String get reciterPlayAll => 'استمع للمصحف كاملًا';

  @override
  String reciterPlaySurah(String name) {
    return 'تشغيل سورة $name';
  }

  @override
  String get reciterStyles => 'نوع التلاوة';

  @override
  String get reciterUnfavourite => 'إزالة من القرّاء المفضّلين';

  @override
  String get resultAddName => 'أضِف الاسم';

  @override
  String resultAyahBadge(String ayah) {
    return 'الآية $ayah';
  }

  @override
  String get resultAyahSection => 'الآية';

  @override
  String get resultContinueListening => 'أكمل الاستماع من هذه الآية';

  @override
  String get resultMayAlsoBe => 'قد يكون أيضًا';

  @override
  String resultMeta(String count, String juz, String page, String revelation) {
    return '$revelation · $count · الجزء $juz · صفحة $page';
  }

  @override
  String get resultReciter => 'القارئ';

  @override
  String get resultReciterPage => 'صفحة القارئ';

  @override
  String get resultReciterSection => 'القارئ';

  @override
  String get resultReciterUnavailable => 'التعرّف على القارئ غير متاح حاليًا';

  @override
  String get resultSave => 'حفظ';

  @override
  String get resultSaved => 'محفوظة';

  @override
  String get resultShare => 'مشاركة';

  @override
  String resultShareText(String ayah, String surah) {
    return 'سورة $surah · الآية $ayah';
  }

  @override
  String get resultShared => 'تم نسخ النتيجة';

  @override
  String resultSurah(String name) {
    return 'سورة $name';
  }

  @override
  String get resultTafsir => 'التفسير';

  @override
  String resultTafsirAuthor(String author, String publisher, String version) {
    return '$author · $publisher · الإصدار $version';
  }

  @override
  String get resultTafsirFailed =>
      'تعذّر تحميل التفسير. تحقّق من الاتصال وحاول مجددًا.';

  @override
  String get resultTafsirLoading => 'جارٍ تحميل التفسير…';

  @override
  String get resultTextCredit => 'نص المصحف من مشروع تنزيل';

  @override
  String get resultTextMatch => 'تطابق النص';

  @override
  String get resultTitle => 'تم التعرّف';

  @override
  String get resultUnknownHint => 'لم نتأكد من صوت القارئ';

  @override
  String get resultUnknownReciter => 'قارئ غير معروف';

  @override
  String get resultVoiceSimilarity => 'تشابه الصوت';

  @override
  String get resultWrong => 'نتيجة خاطئة؟';

  @override
  String get settingsAbout => 'عن التطبيق والمصادر';

  @override
  String get settingsAppearance => 'المظهر';

  @override
  String get settingsClearConfirm => 'اضغط مرة أخرى للتأكيد';

  @override
  String get settingsClearHistory => 'مسح السجل';

  @override
  String get settingsCleared => 'تم مسح السجل';

  @override
  String get settingsCreditAsr =>
      'نموذج التعرّف على التلاوة: Tarteel AI، ترخيص Apache 2.0.';

  @override
  String get settingsCreditAudio => 'التلاوات المسموعة: EveryAyah.';

  @override
  String get settingsCreditTanzil =>
      'نص المصحف: مشروع تنزيل (Tanzil Project)، معروض دون أي تعديل.';

  @override
  String get settingsCreditWespeaker =>
      'نموذج بصمة الصوت: مشروع WeSpeaker، ترخيص CC BY 4.0.';

  @override
  String get settingsDark => 'داكن';

  @override
  String get settingsData => 'البيانات';

  @override
  String get settingsInstall => 'التطبيق';

  @override
  String get settingsLight => 'فاتح';

  @override
  String get settingsPrivacy => 'الخصوصية';

  @override
  String get settingsPrivacyClip =>
      'المقطع الصوتي يُحذف بعد التعرّف ولا يُحفظ في أي مكان.';

  @override
  String get settingsPrivacyHistory => 'السجل محفوظ على هذا الجهاز فقط.';

  @override
  String get settingsPrivacyMic => 'المايكروفون يعمل فقط حين تضغط «أنصِت».';

  @override
  String get settingsServer => 'الخادم';

  @override
  String get settingsServerHint => 'للتجربة فقط: عنوان خدمة أنصِت على شبكتك';

  @override
  String get settingsServerLabel => 'عنوان الخادم';

  @override
  String get settingsServerSave => 'حفظ العنوان';

  @override
  String get settingsServerSaved => 'تم حفظ العنوان';

  @override
  String get settingsSystem => 'حسب النظام';

  @override
  String get settingsTitle => 'الإعدادات';

  @override
  String settingsVersion(String version) {
    return 'الإصدار $version';
  }

  @override
  String get statesBadAudioBody =>
      'لم نستطع معالجة هذا التسجيل. حاول مرة أخرى.';

  @override
  String get statesBadAudioTitle => 'تعذّر قراءة المقطع';

  @override
  String get statesBusyBody => 'عدد الطلبات كبير الآن. حاول بعد لحظات.';

  @override
  String get statesBusyTitle => 'الخدمة مشغولة';

  @override
  String get statesDeniedBody =>
      'لا نستطيع الإنصات بدون إذن المايكروفون. اسمح به من إعدادات التطبيق، ثم حاول مرة أخرى.';

  @override
  String get statesDeniedTitle => 'المايكروفون غير مسموح';

  @override
  String get statesLowConfidenceBody =>
      'قد يكون الصوت غير واضح. حاول من مكان أهدأ أو أنصت لمدة أطول.';

  @override
  String get statesLowConfidenceTitle => 'لم نتعرّف على الآية';

  @override
  String get statesNoSpeechBody =>
      'قرّب الهاتف من مصدر الصوت وتأكد أن التلاوة مسموعة، ثم حاول مرة أخرى.';

  @override
  String get statesNoSpeechTitle => 'لم نسمع تلاوة';

  @override
  String get statesNotFoundBody => 'ربما حُذفت من سجلّ هذا الجهاز.';

  @override
  String get statesNotFoundTitle => 'النتيجة غير موجودة';

  @override
  String get statesOfflineBody =>
      'تحقّق من اتصالك بالإنترنت ثم حاول مرة أخرى. سجلّك متاح بدون اتصال.';

  @override
  String get statesOfflineTitle => 'لا يوجد اتصال';

  @override
  String get statesOpenHistory => 'فتح السجل';

  @override
  String get statesOpenSettings => 'فتح إعدادات التطبيق';

  @override
  String get statesRateBody =>
      'وصلت للحد المسموح من المحاولات. حاول مرة أخرى بعد قليل.';

  @override
  String get statesRateTitle => 'تمهّل قليلًا';

  @override
  String statesRateWait(String seconds) {
    return 'يمكنك المحاولة بعد $seconds ثانية';
  }

  @override
  String get statesServerBody => 'لم نتمكن من إتمام التعرّف. حاول بعد قليل.';

  @override
  String get statesServerTitle => 'حدث خطأ من جهتنا';

  @override
  String get statesTooShortBody =>
      'أنصت خمس ثوانٍ على الأقل حتى نتعرّف على الآية.';

  @override
  String get statesTooShortTitle => 'المقطع قصير';

  @override
  String get statesUnavailableBody => 'لم نجد مايكروفونًا يعمل على هذا الجهاز.';

  @override
  String get statesUnavailableTitle => 'لا يوجد مايكروفون';
}
