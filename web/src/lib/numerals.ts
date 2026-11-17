/** Eastern Arabic numerals and number-dependent Arabic wording for the UI. */

const EASTERN = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];

/** 562 -> "٥٦٢". Non-digits pass through, so it is safe on formatted strings. */
export function toArabicDigits(value: number | string): string {
  return String(value).replace(/[0-9]/g, (digit) => EASTERN[Number(digit)]);
}

/** 0.96 -> "٩٦٪" */
export function formatPercent(fraction: number): string {
  const clamped = Math.min(1, Math.max(0, fraction));
  return `${toArabicDigits(Math.round(clamped * 100))}٪`;
}

/** 6.4 -> "٠:٠٦" */
export function formatElapsed(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(whole / 60);
  const rest = String(whole % 60).padStart(2, "0");
  return toArabicDigits(`${minutes}:${rest}`);
}

/**
 * Arabic counted noun for ayahs: "آية واحدة", "آيتان", "٧ آيات", "٣٠ آية".
 * 3-10 take the plural; 11 and above take the singular.
 */
export function ayahCount(count: number): string {
  if (count === 1) return "آية واحدة";
  if (count === 2) return "آيتان";
  const noun = count >= 3 && count <= 10 ? "آيات" : "آية";
  return `${toArabicDigits(count)} ${noun}`;
}

/** "٢٨ موضعًا آخر" with the right form of the noun for the count. */
export function otherPlaces(count: number): string {
  if (count === 1) return "موضع واحد آخر";
  if (count === 2) return "موضعان آخران";
  const noun = count >= 3 && count <= 10 ? "مواضع أخرى" : "موضعًا آخر";
  return `${toArabicDigits(count)} ${noun}`;
}

/** "تتكرر ٣١ مرة" */
export function repeatedTimes(count: number): string {
  if (count === 2) return "تتكرر مرتين";
  const noun = count >= 3 && count <= 10 ? "مرات" : "مرة";
  return `تتكرر ${toArabicDigits(count)} ${noun}`;
}
