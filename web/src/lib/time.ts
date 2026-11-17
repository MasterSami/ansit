/** Arabic relative and clock times for history rows. */

import { toArabicDigits } from "./numerals";

const MINUTE = 60_000;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

function counted(
  n: number,
  one: string,
  two: string,
  few: string,
  many: string,
): string {
  if (n === 1) return one;
  if (n === 2) return two;
  return `${toArabicDigits(n)} ${n >= 3 && n <= 10 ? few : many}`;
}

/** "الآن", "منذ ١٠ دقائق", "منذ ساعتين", "منذ ٣ أيام". */
export function relativeTime(then: number, now: number = Date.now()): string {
  const elapsed = Math.max(0, now - then);
  if (elapsed < MINUTE) return "الآن";
  if (elapsed < HOUR) {
    return `منذ ${counted(Math.floor(elapsed / MINUTE), "دقيقة", "دقيقتين", "دقائق", "دقيقة")}`;
  }
  if (elapsed < DAY) {
    return `منذ ${counted(Math.floor(elapsed / HOUR), "ساعة", "ساعتين", "ساعات", "ساعة")}`;
  }
  return `منذ ${counted(Math.floor(elapsed / DAY), "يوم", "يومين", "أيام", "يومًا")}`;
}

/** "٢:٤٠ م" */
export function clockTime(timestamp: number): string {
  const date = new Date(timestamp);
  const hours = date.getHours();
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const hour12 = hours % 12 === 0 ? 12 : hours % 12;
  return `${toArabicDigits(`${hour12}:${minutes}`)} ${hours < 12 ? "ص" : "م"}`;
}

function startOfDay(timestamp: number): number {
  const date = new Date(timestamp);
  date.setHours(0, 0, 0, 0);
  return date.getTime();
}

/** Whole days between two timestamps' calendar days (0 = same day). */
export function daysAgo(then: number, now: number = Date.now()): number {
  return Math.round((startOfDay(now) - startOfDay(then)) / DAY);
}

const MONTHS = [
  "يناير",
  "فبراير",
  "مارس",
  "أبريل",
  "مايو",
  "يونيو",
  "يوليو",
  "أغسطس",
  "سبتمبر",
  "أكتوبر",
  "نوفمبر",
  "ديسمبر",
];

/** Heading for a day in the history list: "اليوم", "أمس", or "١٤ نوفمبر". */
export function dayLabel(timestamp: number, now: number = Date.now()): string {
  const ago = daysAgo(timestamp, now);
  if (ago === 0) return "اليوم";
  if (ago === 1) return "أمس";
  const date = new Date(timestamp);
  return `${toArabicDigits(date.getDate())} ${MONTHS[date.getMonth()]}`;
}
