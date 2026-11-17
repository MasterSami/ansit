import 'package:material_ui/material_ui.dart';

/// Design tokens from the approved mockups (build brief §8).
@immutable
class AnsitColors extends ThemeExtension<AnsitColors> {
  const AnsitColors({
    required this.bg,
    required this.surface,
    required this.surface2,
    required this.border,
    required this.divider,
    required this.navBg,
    required this.navBorder,
    required this.text,
    required this.muted,
    required this.accent,
    required this.onAccent,
    required this.accentSoft,
    required this.warningBg,
    required this.warning,
    required this.recording,
    required this.track,
  });

  final Color bg;
  final Color surface;
  final Color surface2;
  final Color border;
  final Color divider;
  final Color navBg;
  final Color navBorder;
  final Color text;
  final Color muted;
  final Color accent;
  final Color onAccent;
  final Color accentSoft;
  final Color warningBg;
  final Color warning;
  final Color recording;
  final Color track;

  static const dark = AnsitColors(
    bg: Color(0xFF0E1512),
    surface: Color(0xFF16201B),
    surface2: Color(0xFF1E2A24),
    border: Color(0xFF2A3731),
    divider: Color(0xFF24302A),
    navBg: Color(0xFF101814),
    navBorder: Color(0xFF1F2A25),
    text: Color(0xFFF2EDE3),
    muted: Color(0xFFA3AFA8),
    accent: Color(0xFFD9B36C),
    onAccent: Color(0xFF0E1512),
    accentSoft: Color(0x24D9B36C),
    warningBg: Color(0x29E07A5F),
    warning: Color(0xFFF0A48F),
    recording: Color(0xFFE07A5F),
    track: Color(0xFF3A4842),
  );

  static const light = AnsitColors(
    bg: Color(0xFFF7F4EC),
    surface: Color(0xFFFFFFFF),
    surface2: Color(0xFFF1ECDF),
    border: Color(0xFFE4DED0),
    divider: Color(0xFFEBE5D8),
    navBg: Color(0xFFFFFFFF),
    navBorder: Color(0xFFE4DED0),
    text: Color(0xFF1A211D),
    muted: Color(0xFF5C6660),
    accent: Color(0xFF8A6620),
    onAccent: Color(0xFFFFFFFF),
    accentSoft: Color(0x1A8A6620),
    warningBg: Color(0x1FBE5438),
    warning: Color(0xFFA8442A),
    recording: Color(0xFFC9573B),
    track: Color(0xFFCFC8B8),
  );

  @override
  AnsitColors copyWith() => this;

  @override
  AnsitColors lerp(AnsitColors? other, double t) {
    if (other == null) return this;
    Color mix(Color a, Color b) => Color.lerp(a, b, t)!;
    return AnsitColors(
      bg: mix(bg, other.bg),
      surface: mix(surface, other.surface),
      surface2: mix(surface2, other.surface2),
      border: mix(border, other.border),
      divider: mix(divider, other.divider),
      navBg: mix(navBg, other.navBg),
      navBorder: mix(navBorder, other.navBorder),
      text: mix(text, other.text),
      muted: mix(muted, other.muted),
      accent: mix(accent, other.accent),
      onAccent: mix(onAccent, other.onAccent),
      accentSoft: mix(accentSoft, other.accentSoft),
      warningBg: mix(warningBg, other.warningBg),
      warning: mix(warning, other.warning),
      recording: mix(recording, other.recording),
      track: mix(track, other.track),
    );
  }
}

const fontSans = 'IBM Plex Sans Arabic';
const fontDisplay = 'Amiri';
const fontQuran = 'Amiri Quran';

extension AnsitTheme on BuildContext {
  AnsitColors get colors => Theme.of(this).extension<AnsitColors>()!;
}

ThemeData buildTheme(Brightness brightness) {
  final c = brightness == Brightness.dark
      ? AnsitColors.dark
      : AnsitColors.light;
  final base = ThemeData(
    brightness: brightness,
    useMaterial3: true,
    fontFamily: fontSans,
    scaffoldBackgroundColor: c.bg,
    colorScheme:
        ColorScheme.fromSeed(
          seedColor: c.accent,
          brightness: brightness,
        ).copyWith(
          primary: c.accent,
          onPrimary: c.onAccent,
          surface: c.surface,
          onSurface: c.text,
          error: c.warning,
        ),
    extensions: [c],
  );
  return base.copyWith(
    textTheme: base.textTheme.apply(bodyColor: c.text, displayColor: c.text),
    splashFactory: InkRipple.splashFactory,
    dividerColor: c.divider,
    textSelectionTheme: TextSelectionThemeData(cursorColor: c.accent),
  );
}
