import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[Locale('ar')];

  /// No description provided for @ambiguousAfter.
  ///
  /// In ar, this message translates to:
  /// **'بعد ﴿{text}﴾'**
  String ambiguousAfter(String text);

  /// No description provided for @ambiguousAyah.
  ///
  /// In ar, this message translates to:
  /// **'الآية {ayah}'**
  String ambiguousAyah(String ayah);

  /// No description provided for @ambiguousConfirm.
  ///
  /// In ar, this message translates to:
  /// **'تأكيد الموضع المختار'**
  String get ambiguousConfirm;

  /// No description provided for @ambiguousConfirmFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر التأكيد. تحقّق من الاتصال وحاول مرة أخرى.'**
  String get ambiguousConfirmFailed;

  /// No description provided for @ambiguousExplain.
  ///
  /// In ar, this message translates to:
  /// **'تعرّفنا على الآية بثقة، لكنها تتكرر. أنصت لثوانٍ أطول لنحدّد موضعها من الآيات المجاورة، أو اختر الموضع بنفسك.'**
  String get ambiguousExplain;

  /// No description provided for @ambiguousFirstOfSurah.
  ///
  /// In ar, this message translates to:
  /// **'أول السورة'**
  String get ambiguousFirstOfSurah;

  /// No description provided for @ambiguousHeardSection.
  ///
  /// In ar, this message translates to:
  /// **'الآية المسموعة'**
  String get ambiguousHeardSection;

  /// No description provided for @ambiguousListenMore.
  ///
  /// In ar, this message translates to:
  /// **'أنصت ١٠ ثوانٍ إضافية'**
  String get ambiguousListenMore;

  /// No description provided for @ambiguousMore.
  ///
  /// In ar, this message translates to:
  /// **'و{count}'**
  String ambiguousMore(String count);

  /// No description provided for @ambiguousPlaces.
  ///
  /// In ar, this message translates to:
  /// **'المواضع المحتملة'**
  String get ambiguousPlaces;

  /// No description provided for @ambiguousSurahAyah.
  ///
  /// In ar, this message translates to:
  /// **'{surah} · الآية {ayah}'**
  String ambiguousSurahAyah(String ayah, String surah);

  /// No description provided for @ambiguousTitle.
  ///
  /// In ar, this message translates to:
  /// **'تحديد موضع الآية'**
  String get ambiguousTitle;

  /// No description provided for @appDescription.
  ///
  /// In ar, this message translates to:
  /// **'تعرّف على السورة والآية واسم القارئ من ثوانٍ من التلاوة'**
  String get appDescription;

  /// No description provided for @appName.
  ///
  /// In ar, this message translates to:
  /// **'أنصِت'**
  String get appName;

  /// No description provided for @appVerse.
  ///
  /// In ar, this message translates to:
  /// **'﴿فَاسْتَمِعُوا لَهُ وَأَنصِتُوا﴾'**
  String get appVerse;

  /// No description provided for @commonBack.
  ///
  /// In ar, this message translates to:
  /// **'رجوع'**
  String get commonBack;

  /// No description provided for @commonCancel.
  ///
  /// In ar, this message translates to:
  /// **'إلغاء'**
  String get commonCancel;

  /// No description provided for @commonClose.
  ///
  /// In ar, this message translates to:
  /// **'إغلاق'**
  String get commonClose;

  /// No description provided for @commonHome.
  ///
  /// In ar, this message translates to:
  /// **'العودة للرئيسية'**
  String get commonHome;

  /// No description provided for @commonRetry.
  ///
  /// In ar, this message translates to:
  /// **'حاول مرة أخرى'**
  String get commonRetry;

  /// No description provided for @commonSoon.
  ///
  /// In ar, this message translates to:
  /// **'قريبًا'**
  String get commonSoon;

  /// No description provided for @feedbackAyahNumber.
  ///
  /// In ar, this message translates to:
  /// **'رقم الآية'**
  String get feedbackAyahNumber;

  /// No description provided for @feedbackChooseReciter.
  ///
  /// In ar, this message translates to:
  /// **'اختر القارئ الصحيح'**
  String get feedbackChooseReciter;

  /// No description provided for @feedbackFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر الإرسال. حاول مرة أخرى.'**
  String get feedbackFailed;

  /// No description provided for @feedbackNoReciters.
  ///
  /// In ar, this message translates to:
  /// **'قائمة القرّاء غير متاحة الآن. يمكنك إرسال الملاحظة بدون اختيار قارئ.'**
  String get feedbackNoReciters;

  /// No description provided for @feedbackNote.
  ///
  /// In ar, this message translates to:
  /// **'نرسل الملاحظة فقط، ولا يوجد تسجيل محفوظ مرتبط بها.'**
  String get feedbackNote;

  /// No description provided for @feedbackOptional.
  ///
  /// In ar, this message translates to:
  /// **'اختياري'**
  String get feedbackOptional;

  /// No description provided for @feedbackOther.
  ///
  /// In ar, this message translates to:
  /// **'شيء آخر'**
  String get feedbackOther;

  /// No description provided for @feedbackReciterTitle.
  ///
  /// In ar, this message translates to:
  /// **'من هو القارئ؟'**
  String get feedbackReciterTitle;

  /// No description provided for @feedbackSend.
  ///
  /// In ar, this message translates to:
  /// **'إرسال'**
  String get feedbackSend;

  /// No description provided for @feedbackSending.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ الإرسال…'**
  String get feedbackSending;

  /// No description provided for @feedbackSurahNumber.
  ///
  /// In ar, this message translates to:
  /// **'رقم السورة'**
  String get feedbackSurahNumber;

  /// No description provided for @feedbackThanks.
  ///
  /// In ar, this message translates to:
  /// **'شكرًا، وصلتنا ملاحظتك'**
  String get feedbackThanks;

  /// No description provided for @feedbackTitle.
  ///
  /// In ar, this message translates to:
  /// **'ما الخطأ في النتيجة؟'**
  String get feedbackTitle;

  /// No description provided for @feedbackWrongAyah.
  ///
  /// In ar, this message translates to:
  /// **'الآية خاطئة'**
  String get feedbackWrongAyah;

  /// No description provided for @feedbackWrongReciter.
  ///
  /// In ar, this message translates to:
  /// **'القارئ خاطئ'**
  String get feedbackWrongReciter;

  /// No description provided for @historyAll.
  ///
  /// In ar, this message translates to:
  /// **'الكل'**
  String get historyAll;

  /// No description provided for @historyEmptyBody.
  ///
  /// In ar, this message translates to:
  /// **'كل تلاوة تتعرّف عليها تُحفظ هنا على جهازك فقط.'**
  String get historyEmptyBody;

  /// No description provided for @historyEmptySavedBody.
  ///
  /// In ar, this message translates to:
  /// **'اضغط «حفظ» في أي نتيجة لتجدها هنا.'**
  String get historyEmptySavedBody;

  /// No description provided for @historyEmptySavedTitle.
  ///
  /// In ar, this message translates to:
  /// **'لا محفوظات بعد'**
  String get historyEmptySavedTitle;

  /// No description provided for @historyEmptyTitle.
  ///
  /// In ar, this message translates to:
  /// **'سجلّك فارغ'**
  String get historyEmptyTitle;

  /// No description provided for @historyFilters.
  ///
  /// In ar, this message translates to:
  /// **'تصفية'**
  String get historyFilters;

  /// No description provided for @historyNoResultsBody.
  ///
  /// In ar, this message translates to:
  /// **'جرّب كلمة أخرى أو غيّر التصفية.'**
  String get historyNoResultsBody;

  /// No description provided for @historyNoResultsTitle.
  ///
  /// In ar, this message translates to:
  /// **'لا نتائج'**
  String get historyNoResultsTitle;

  /// No description provided for @historySaved.
  ///
  /// In ar, this message translates to:
  /// **'المحفوظة'**
  String get historySaved;

  /// No description provided for @historySavedTitle.
  ///
  /// In ar, this message translates to:
  /// **'المحفوظات'**
  String get historySavedTitle;

  /// No description provided for @historySearchLabel.
  ///
  /// In ar, this message translates to:
  /// **'ابحث في السجل'**
  String get historySearchLabel;

  /// No description provided for @historySearchPlaceholder.
  ///
  /// In ar, this message translates to:
  /// **'ابحث بسورة أو قارئ'**
  String get historySearchPlaceholder;

  /// No description provided for @historyStartListening.
  ///
  /// In ar, this message translates to:
  /// **'ابدأ الإنصات'**
  String get historyStartListening;

  /// No description provided for @historyTitle.
  ///
  /// In ar, this message translates to:
  /// **'السجل'**
  String get historyTitle;

  /// No description provided for @historyToday.
  ///
  /// In ar, this message translates to:
  /// **'اليوم'**
  String get historyToday;

  /// No description provided for @historyUnknown.
  ///
  /// In ar, this message translates to:
  /// **'قارئ غير معروف · أضِف الاسم'**
  String get historyUnknown;

  /// No description provided for @historyWeek.
  ///
  /// In ar, this message translates to:
  /// **'هذا الأسبوع'**
  String get historyWeek;

  /// No description provided for @homeLastHeard.
  ///
  /// In ar, this message translates to:
  /// **'آخر ما سمعته'**
  String get homeLastHeard;

  /// No description provided for @homeNothingYet.
  ///
  /// In ar, this message translates to:
  /// **'لا شيء بعد. اضغط الزر وقرّب الهاتف من التلاوة.'**
  String get homeNothingYet;

  /// No description provided for @homeOpen.
  ///
  /// In ar, this message translates to:
  /// **'فتح النتيجة'**
  String get homeOpen;

  /// No description provided for @homeSettings.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get homeSettings;

  /// No description provided for @homeShowHistory.
  ///
  /// In ar, this message translates to:
  /// **'عرض السجل'**
  String get homeShowHistory;

  /// No description provided for @homeSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'نتعرّف على السورة والآية واسم القارئ في ثوانٍ'**
  String get homeSubtitle;

  /// No description provided for @homeSurahAyah.
  ///
  /// In ar, this message translates to:
  /// **'سورة {surah} · الآية {ayah}'**
  String homeSurahAyah(String ayah, String surah);

  /// No description provided for @homeTapToListen.
  ///
  /// In ar, this message translates to:
  /// **'اضغط لتنصت'**
  String get homeTapToListen;

  /// No description provided for @listenContinuing.
  ///
  /// In ar, this message translates to:
  /// **'نكمل الإنصات لتحديد الموضع'**
  String get listenContinuing;

  /// No description provided for @listenDone.
  ///
  /// In ar, this message translates to:
  /// **'تم'**
  String get listenDone;

  /// No description provided for @listenElapsed.
  ///
  /// In ar, this message translates to:
  /// **'مدة التسجيل'**
  String get listenElapsed;

  /// No description provided for @listenHint.
  ///
  /// In ar, this message translates to:
  /// **'قرّب الهاتف من مصدر الصوت، ويكفي ٥ إلى ١٠ ثوانٍ من التلاوة'**
  String get listenHint;

  /// No description provided for @listenIdentifying.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ التعرّف…'**
  String get listenIdentifying;

  /// No description provided for @listenIdentifyingHint.
  ///
  /// In ar, this message translates to:
  /// **'لحظات ونخبرك بالسورة والآية والقارئ'**
  String get listenIdentifyingHint;

  /// No description provided for @listenInProgress.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ'**
  String get listenInProgress;

  /// No description provided for @listenListening.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ الإنصات…'**
  String get listenListening;

  /// No description provided for @listenStepCapture.
  ///
  /// In ar, this message translates to:
  /// **'التقاط الصوت وتنقيته'**
  String get listenStepCapture;

  /// No description provided for @listenStepMatch.
  ///
  /// In ar, this message translates to:
  /// **'مطابقة النص بآيات المصحف'**
  String get listenStepMatch;

  /// No description provided for @listenStepReciter.
  ///
  /// In ar, this message translates to:
  /// **'التعرّف على صوت القارئ'**
  String get listenStepReciter;

  /// No description provided for @listenSteps.
  ///
  /// In ar, this message translates to:
  /// **'مراحل التعرّف'**
  String get listenSteps;

  /// No description provided for @listenStop.
  ///
  /// In ar, this message translates to:
  /// **'إيقاف'**
  String get listenStop;

  /// No description provided for @listenWave.
  ///
  /// In ar, this message translates to:
  /// **'موجة الصوت'**
  String get listenWave;

  /// No description provided for @mushafAyah.
  ///
  /// In ar, this message translates to:
  /// **'الآية'**
  String get mushafAyah;

  /// No description provided for @mushafBody.
  ///
  /// In ar, this message translates to:
  /// **'اختر سورة ورقم آية لعرضها وفتح تفسيرها.'**
  String get mushafBody;

  /// No description provided for @mushafHideTafsir.
  ///
  /// In ar, this message translates to:
  /// **'إخفاء التفسير'**
  String get mushafHideTafsir;

  /// No description provided for @mushafLoadFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر تحميل الآية أو التفسير. تحقّق من الاتصال وحاول مجددًا.'**
  String get mushafLoadFailed;

  /// No description provided for @mushafLoading.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ التحميل…'**
  String get mushafLoading;

  /// No description provided for @mushafOpenAyah.
  ///
  /// In ar, this message translates to:
  /// **'عرض الآية'**
  String get mushafOpenAyah;

  /// No description provided for @mushafShowTafsir.
  ///
  /// In ar, this message translates to:
  /// **'عرض التفسير'**
  String get mushafShowTafsir;

  /// No description provided for @mushafSurah.
  ///
  /// In ar, this message translates to:
  /// **'السورة'**
  String get mushafSurah;

  /// No description provided for @mushafTitle.
  ///
  /// In ar, this message translates to:
  /// **'المصحف'**
  String get mushafTitle;

  /// No description provided for @navHistory.
  ///
  /// In ar, this message translates to:
  /// **'السجل'**
  String get navHistory;

  /// No description provided for @navLabel.
  ///
  /// In ar, this message translates to:
  /// **'التنقل الرئيسي'**
  String get navLabel;

  /// No description provided for @navListen.
  ///
  /// In ar, this message translates to:
  /// **'أنصِت'**
  String get navListen;

  /// No description provided for @navMushaf.
  ///
  /// In ar, this message translates to:
  /// **'المصحف'**
  String get navMushaf;

  /// No description provided for @navReciters.
  ///
  /// In ar, this message translates to:
  /// **'القرّاء'**
  String get navReciters;

  /// No description provided for @navSaved.
  ///
  /// In ar, this message translates to:
  /// **'المحفوظات'**
  String get navSaved;

  /// No description provided for @offlineBanner.
  ///
  /// In ar, this message translates to:
  /// **'أنت غير متصل. السجل متاح، والتعرّف يحتاج اتصالًا.'**
  String get offlineBanner;

  /// No description provided for @permissionAllow.
  ///
  /// In ar, this message translates to:
  /// **'السماح بالمايكروفون'**
  String get permissionAllow;

  /// No description provided for @permissionAnySourceBody.
  ///
  /// In ar, this message translates to:
  /// **'راديو، مسجد، تلفاز، أو هاتف آخر'**
  String get permissionAnySourceBody;

  /// No description provided for @permissionAnySourceTitle.
  ///
  /// In ar, this message translates to:
  /// **'من أي مصدر'**
  String get permissionAnySourceTitle;

  /// No description provided for @permissionDeletedBody.
  ///
  /// In ar, this message translates to:
  /// **'نحتفظ بالنتيجة في سجلّك فقط، لا بالتسجيل'**
  String get permissionDeletedBody;

  /// No description provided for @permissionDeletedTitle.
  ///
  /// In ar, this message translates to:
  /// **'المقطع يُحذف بعد التعرّف'**
  String get permissionDeletedTitle;

  /// No description provided for @permissionNotNow.
  ///
  /// In ar, this message translates to:
  /// **'ليس الآن'**
  String get permissionNotNow;

  /// No description provided for @permissionOnlyWhenBody.
  ///
  /// In ar, this message translates to:
  /// **'لا استماع في الخلفية، ويتوقف تلقائيًا بعد التعرّف'**
  String get permissionOnlyWhenBody;

  /// No description provided for @permissionOnlyWhenTitle.
  ///
  /// In ar, this message translates to:
  /// **'يعمل فقط حين تضغط «أنصِت»'**
  String get permissionOnlyWhenTitle;

  /// No description provided for @permissionStep.
  ///
  /// In ar, this message translates to:
  /// **'الخطوة ٣ من ٣'**
  String get permissionStep;

  /// No description provided for @permissionSubtitle.
  ///
  /// In ar, this message translates to:
  /// **'حتى نتعرّف على التلاوة التي تسمعها حولك'**
  String get permissionSubtitle;

  /// No description provided for @permissionTitle.
  ///
  /// In ar, this message translates to:
  /// **'نحتاج إذن المايكروفون لنُنصت معك'**
  String get permissionTitle;

  /// No description provided for @playerFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر تشغيل التلاوة'**
  String get playerFailed;

  /// No description provided for @playerLabel.
  ///
  /// In ar, this message translates to:
  /// **'مشغّل التلاوة'**
  String get playerLabel;

  /// No description provided for @playerNoAyahAudio.
  ///
  /// In ar, this message translates to:
  /// **'لا تتوفر لهذا القارئ تلاوة مقسّمة بالآيات حتى الآن'**
  String get playerNoAyahAudio;

  /// No description provided for @playerNowPlaying.
  ///
  /// In ar, this message translates to:
  /// **'سورة {surah} · الآية {ayah}'**
  String playerNowPlaying(String ayah, String surah);

  /// No description provided for @playerNowPlayingSurah.
  ///
  /// In ar, this message translates to:
  /// **'سورة {surah}'**
  String playerNowPlayingSurah(String surah);

  /// No description provided for @playerPause.
  ///
  /// In ar, this message translates to:
  /// **'إيقاف مؤقت'**
  String get playerPause;

  /// No description provided for @playerPlay.
  ///
  /// In ar, this message translates to:
  /// **'تشغيل'**
  String get playerPlay;

  /// No description provided for @playerStop.
  ///
  /// In ar, this message translates to:
  /// **'إيقاف التشغيل'**
  String get playerStop;

  /// No description provided for @reciterFavourite.
  ///
  /// In ar, this message translates to:
  /// **'إضافة إلى القرّاء المفضّلين'**
  String get reciterFavourite;

  /// No description provided for @reciterHeardToday.
  ///
  /// In ar, this message translates to:
  /// **'تعرّفت عليها اليوم'**
  String get reciterHeardToday;

  /// No description provided for @reciterLoadFailedTitle.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر تحميل صفحة القارئ'**
  String get reciterLoadFailedTitle;

  /// No description provided for @reciterNotFoundTitle.
  ///
  /// In ar, this message translates to:
  /// **'القارئ غير موجود'**
  String get reciterNotFoundTitle;

  /// No description provided for @reciterPlayAll.
  ///
  /// In ar, this message translates to:
  /// **'استمع للمصحف كاملًا'**
  String get reciterPlayAll;

  /// No description provided for @reciterPlaySurah.
  ///
  /// In ar, this message translates to:
  /// **'تشغيل سورة {name}'**
  String reciterPlaySurah(String name);

  /// No description provided for @reciterStyles.
  ///
  /// In ar, this message translates to:
  /// **'نوع التلاوة'**
  String get reciterStyles;

  /// No description provided for @reciterUnfavourite.
  ///
  /// In ar, this message translates to:
  /// **'إزالة من القرّاء المفضّلين'**
  String get reciterUnfavourite;

  /// No description provided for @resultAddName.
  ///
  /// In ar, this message translates to:
  /// **'أضِف الاسم'**
  String get resultAddName;

  /// No description provided for @resultAyahBadge.
  ///
  /// In ar, this message translates to:
  /// **'الآية {ayah}'**
  String resultAyahBadge(String ayah);

  /// No description provided for @resultAyahSection.
  ///
  /// In ar, this message translates to:
  /// **'الآية'**
  String get resultAyahSection;

  /// No description provided for @resultContinueListening.
  ///
  /// In ar, this message translates to:
  /// **'أكمل الاستماع من هذه الآية'**
  String get resultContinueListening;

  /// No description provided for @resultMayAlsoBe.
  ///
  /// In ar, this message translates to:
  /// **'قد يكون أيضًا'**
  String get resultMayAlsoBe;

  /// No description provided for @resultMeta.
  ///
  /// In ar, this message translates to:
  /// **'{revelation} · {count} · الجزء {juz} · صفحة {page}'**
  String resultMeta(String count, String juz, String page, String revelation);

  /// No description provided for @resultReciter.
  ///
  /// In ar, this message translates to:
  /// **'القارئ'**
  String get resultReciter;

  /// No description provided for @resultReciterPage.
  ///
  /// In ar, this message translates to:
  /// **'صفحة القارئ'**
  String get resultReciterPage;

  /// No description provided for @resultReciterSection.
  ///
  /// In ar, this message translates to:
  /// **'القارئ'**
  String get resultReciterSection;

  /// No description provided for @resultReciterUnavailable.
  ///
  /// In ar, this message translates to:
  /// **'التعرّف على القارئ غير متاح حاليًا'**
  String get resultReciterUnavailable;

  /// No description provided for @resultSave.
  ///
  /// In ar, this message translates to:
  /// **'حفظ'**
  String get resultSave;

  /// No description provided for @resultSaved.
  ///
  /// In ar, this message translates to:
  /// **'محفوظة'**
  String get resultSaved;

  /// No description provided for @resultShare.
  ///
  /// In ar, this message translates to:
  /// **'مشاركة'**
  String get resultShare;

  /// No description provided for @resultShareText.
  ///
  /// In ar, this message translates to:
  /// **'سورة {surah} · الآية {ayah}'**
  String resultShareText(String ayah, String surah);

  /// No description provided for @resultShared.
  ///
  /// In ar, this message translates to:
  /// **'تم نسخ النتيجة'**
  String get resultShared;

  /// No description provided for @resultSurah.
  ///
  /// In ar, this message translates to:
  /// **'سورة {name}'**
  String resultSurah(String name);

  /// No description provided for @resultTafsir.
  ///
  /// In ar, this message translates to:
  /// **'التفسير'**
  String get resultTafsir;

  /// No description provided for @resultTafsirAuthor.
  ///
  /// In ar, this message translates to:
  /// **'{author} · {publisher} · الإصدار {version}'**
  String resultTafsirAuthor(String author, String publisher, String version);

  /// No description provided for @resultTafsirFailed.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر تحميل التفسير. تحقّق من الاتصال وحاول مجددًا.'**
  String get resultTafsirFailed;

  /// No description provided for @resultTafsirLoading.
  ///
  /// In ar, this message translates to:
  /// **'جارٍ تحميل التفسير…'**
  String get resultTafsirLoading;

  /// No description provided for @resultTextCredit.
  ///
  /// In ar, this message translates to:
  /// **'نص المصحف من مشروع تنزيل'**
  String get resultTextCredit;

  /// No description provided for @resultTextMatch.
  ///
  /// In ar, this message translates to:
  /// **'تطابق النص'**
  String get resultTextMatch;

  /// No description provided for @resultTitle.
  ///
  /// In ar, this message translates to:
  /// **'تم التعرّف'**
  String get resultTitle;

  /// No description provided for @resultUnknownHint.
  ///
  /// In ar, this message translates to:
  /// **'لم نتأكد من صوت القارئ'**
  String get resultUnknownHint;

  /// No description provided for @resultUnknownReciter.
  ///
  /// In ar, this message translates to:
  /// **'قارئ غير معروف'**
  String get resultUnknownReciter;

  /// No description provided for @resultVoiceSimilarity.
  ///
  /// In ar, this message translates to:
  /// **'تشابه الصوت'**
  String get resultVoiceSimilarity;

  /// No description provided for @resultWrong.
  ///
  /// In ar, this message translates to:
  /// **'نتيجة خاطئة؟'**
  String get resultWrong;

  /// No description provided for @settingsAbout.
  ///
  /// In ar, this message translates to:
  /// **'عن التطبيق والمصادر'**
  String get settingsAbout;

  /// No description provided for @settingsAppearance.
  ///
  /// In ar, this message translates to:
  /// **'المظهر'**
  String get settingsAppearance;

  /// No description provided for @settingsClearConfirm.
  ///
  /// In ar, this message translates to:
  /// **'اضغط مرة أخرى للتأكيد'**
  String get settingsClearConfirm;

  /// No description provided for @settingsClearHistory.
  ///
  /// In ar, this message translates to:
  /// **'مسح السجل'**
  String get settingsClearHistory;

  /// No description provided for @settingsCleared.
  ///
  /// In ar, this message translates to:
  /// **'تم مسح السجل'**
  String get settingsCleared;

  /// No description provided for @settingsCreditAsr.
  ///
  /// In ar, this message translates to:
  /// **'نموذج التعرّف على التلاوة: Tarteel AI، ترخيص Apache 2.0.'**
  String get settingsCreditAsr;

  /// No description provided for @settingsCreditAudio.
  ///
  /// In ar, this message translates to:
  /// **'التلاوات المسموعة: EveryAyah.'**
  String get settingsCreditAudio;

  /// No description provided for @settingsCreditTanzil.
  ///
  /// In ar, this message translates to:
  /// **'نص المصحف: مشروع تنزيل (Tanzil Project)، معروض دون أي تعديل.'**
  String get settingsCreditTanzil;

  /// No description provided for @settingsCreditWespeaker.
  ///
  /// In ar, this message translates to:
  /// **'نموذج بصمة الصوت: مشروع WeSpeaker، ترخيص CC BY 4.0.'**
  String get settingsCreditWespeaker;

  /// No description provided for @settingsDark.
  ///
  /// In ar, this message translates to:
  /// **'داكن'**
  String get settingsDark;

  /// No description provided for @settingsData.
  ///
  /// In ar, this message translates to:
  /// **'البيانات'**
  String get settingsData;

  /// No description provided for @settingsLight.
  ///
  /// In ar, this message translates to:
  /// **'فاتح'**
  String get settingsLight;

  /// No description provided for @settingsPrivacy.
  ///
  /// In ar, this message translates to:
  /// **'الخصوصية'**
  String get settingsPrivacy;

  /// No description provided for @settingsPrivacyClip.
  ///
  /// In ar, this message translates to:
  /// **'المقطع الصوتي يُحذف بعد التعرّف ولا يُحفظ في أي مكان.'**
  String get settingsPrivacyClip;

  /// No description provided for @settingsPrivacyHistory.
  ///
  /// In ar, this message translates to:
  /// **'السجل محفوظ على هذا الجهاز فقط.'**
  String get settingsPrivacyHistory;

  /// No description provided for @settingsPrivacyMic.
  ///
  /// In ar, this message translates to:
  /// **'المايكروفون يعمل فقط حين تضغط «أنصِت».'**
  String get settingsPrivacyMic;

  /// No description provided for @settingsServer.
  ///
  /// In ar, this message translates to:
  /// **'الخادم'**
  String get settingsServer;

  /// No description provided for @settingsServerHint.
  ///
  /// In ar, this message translates to:
  /// **'للتجربة فقط: عنوان خدمة أنصِت على شبكتك'**
  String get settingsServerHint;

  /// No description provided for @settingsServerLabel.
  ///
  /// In ar, this message translates to:
  /// **'عنوان الخادم'**
  String get settingsServerLabel;

  /// No description provided for @settingsServerSave.
  ///
  /// In ar, this message translates to:
  /// **'حفظ العنوان'**
  String get settingsServerSave;

  /// No description provided for @settingsServerSaved.
  ///
  /// In ar, this message translates to:
  /// **'تم حفظ العنوان'**
  String get settingsServerSaved;

  /// No description provided for @settingsSystem.
  ///
  /// In ar, this message translates to:
  /// **'حسب النظام'**
  String get settingsSystem;

  /// No description provided for @settingsTitle.
  ///
  /// In ar, this message translates to:
  /// **'الإعدادات'**
  String get settingsTitle;

  /// No description provided for @settingsVersion.
  ///
  /// In ar, this message translates to:
  /// **'الإصدار {version}'**
  String settingsVersion(String version);

  /// No description provided for @statesBadAudioBody.
  ///
  /// In ar, this message translates to:
  /// **'لم نستطع معالجة هذا التسجيل. حاول مرة أخرى.'**
  String get statesBadAudioBody;

  /// No description provided for @statesBadAudioTitle.
  ///
  /// In ar, this message translates to:
  /// **'تعذّر قراءة المقطع'**
  String get statesBadAudioTitle;

  /// No description provided for @statesBusyBody.
  ///
  /// In ar, this message translates to:
  /// **'عدد الطلبات كبير الآن. حاول بعد لحظات.'**
  String get statesBusyBody;

  /// No description provided for @statesBusyTitle.
  ///
  /// In ar, this message translates to:
  /// **'الخدمة مشغولة'**
  String get statesBusyTitle;

  /// No description provided for @statesDeniedBody.
  ///
  /// In ar, this message translates to:
  /// **'لا نستطيع الإنصات بدون إذن المايكروفون. اسمح به من إعدادات التطبيق، ثم حاول مرة أخرى.'**
  String get statesDeniedBody;

  /// No description provided for @statesDeniedTitle.
  ///
  /// In ar, this message translates to:
  /// **'المايكروفون غير مسموح'**
  String get statesDeniedTitle;

  /// No description provided for @statesLowConfidenceBody.
  ///
  /// In ar, this message translates to:
  /// **'قد يكون الصوت غير واضح. حاول من مكان أهدأ أو أنصت لمدة أطول.'**
  String get statesLowConfidenceBody;

  /// No description provided for @statesLowConfidenceTitle.
  ///
  /// In ar, this message translates to:
  /// **'لم نتعرّف على الآية'**
  String get statesLowConfidenceTitle;

  /// No description provided for @statesNoSpeechBody.
  ///
  /// In ar, this message translates to:
  /// **'قرّب الهاتف من مصدر الصوت وتأكد أن التلاوة مسموعة، ثم حاول مرة أخرى.'**
  String get statesNoSpeechBody;

  /// No description provided for @statesNoSpeechTitle.
  ///
  /// In ar, this message translates to:
  /// **'لم نسمع تلاوة'**
  String get statesNoSpeechTitle;

  /// No description provided for @statesNotFoundBody.
  ///
  /// In ar, this message translates to:
  /// **'ربما حُذفت من سجلّ هذا الجهاز.'**
  String get statesNotFoundBody;

  /// No description provided for @statesNotFoundTitle.
  ///
  /// In ar, this message translates to:
  /// **'النتيجة غير موجودة'**
  String get statesNotFoundTitle;

  /// No description provided for @statesOfflineBody.
  ///
  /// In ar, this message translates to:
  /// **'تحقّق من اتصالك بالإنترنت ثم حاول مرة أخرى. سجلّك متاح بدون اتصال.'**
  String get statesOfflineBody;

  /// No description provided for @statesOfflineTitle.
  ///
  /// In ar, this message translates to:
  /// **'لا يوجد اتصال'**
  String get statesOfflineTitle;

  /// No description provided for @statesOpenHistory.
  ///
  /// In ar, this message translates to:
  /// **'فتح السجل'**
  String get statesOpenHistory;

  /// No description provided for @statesOpenSettings.
  ///
  /// In ar, this message translates to:
  /// **'فتح إعدادات التطبيق'**
  String get statesOpenSettings;

  /// No description provided for @statesRateBody.
  ///
  /// In ar, this message translates to:
  /// **'وصلت للحد المسموح من المحاولات. حاول مرة أخرى بعد قليل.'**
  String get statesRateBody;

  /// No description provided for @statesRateTitle.
  ///
  /// In ar, this message translates to:
  /// **'تمهّل قليلًا'**
  String get statesRateTitle;

  /// No description provided for @statesRateWait.
  ///
  /// In ar, this message translates to:
  /// **'يمكنك المحاولة بعد {seconds} ثانية'**
  String statesRateWait(String seconds);

  /// No description provided for @statesServerBody.
  ///
  /// In ar, this message translates to:
  /// **'لم نتمكن من إتمام التعرّف. حاول بعد قليل.'**
  String get statesServerBody;

  /// No description provided for @statesServerTitle.
  ///
  /// In ar, this message translates to:
  /// **'حدث خطأ من جهتنا'**
  String get statesServerTitle;

  /// No description provided for @statesTooShortBody.
  ///
  /// In ar, this message translates to:
  /// **'أنصت خمس ثوانٍ على الأقل حتى نتعرّف على الآية.'**
  String get statesTooShortBody;

  /// No description provided for @statesTooShortTitle.
  ///
  /// In ar, this message translates to:
  /// **'المقطع قصير'**
  String get statesTooShortTitle;

  /// No description provided for @statesUnavailableBody.
  ///
  /// In ar, this message translates to:
  /// **'لم نجد مايكروفونًا يعمل على هذا الجهاز.'**
  String get statesUnavailableBody;

  /// No description provided for @statesUnavailableTitle.
  ///
  /// In ar, this message translates to:
  /// **'لا يوجد مايكروفون'**
  String get statesUnavailableTitle;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
