"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getReciters, type ReciterSummary } from "@/lib/api";
import { toArabicDigits } from "@/lib/numerals";
import { Avatar, Screen, StateMessage } from "./ui";
import { AlertIcon } from "./icons";

type Group = "all" | "egypt" | "saudi" | "other";
const EGYPTIAN = new Set([
  "abdul-basit",
  "husary",
  "minshawi",
  "tablawi",
  "jibreel",
  "neana",
  "banna",
]);
const SAUDI = new Set([
  "sudais",
  "muaiqly",
  "shuraim",
  "juhany",
  "budair",
  "qasim",
  "yasser-dosari",
  "ahmad-talib",
]);
const LABELS: Record<Group, string> = {
  all: "كل القراء",
  egypt: "مدرسة التلاوة المصرية",
  saudi: "قراء السعودية",
  other: "قراء من بلدان أخرى",
};

export function ReciterLibraryScreen() {
  const [reciters, setReciters] = useState<ReciterSummary[] | null>(null);
  const [group, setGroup] = useState<Group>("all");
  const [query, setQuery] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    getReciters().then(setReciters, () => setFailed(true));
  }, []);
  const visible = useMemo(
    () =>
      (reciters ?? []).filter((r) => {
        const isEgypt = EGYPTIAN.has(r.id) || r.country === "Egypt";
        const isSaudi = SAUDI.has(r.id) || r.country === "Saudi Arabia";
        const inGroup =
          group === "all" ||
          (group === "egypt" && isEgypt) ||
          (group === "saudi" && isSaudi) ||
          (group === "other" && !isEgypt && !isSaudi);
        return (
          inGroup &&
          `${r.name_ar} ${r.name_en}`
            .toLocaleLowerCase()
            .includes(query.trim().toLocaleLowerCase())
        );
      }),
    [reciters, group, query],
  );

  return (
    <Screen className="pb-8">
      <header className="px-5 pt-[52px]">
        <Link href="/" className="text-sm text-muted">
          ← الرئيسية
        </Link>
        <h1 className="mt-4 text-2xl font-bold">مكتبة القراء</h1>
        <p className="mt-2 text-sm leading-7 text-muted">
          تصفّح القراء المتاحين في أنصت. ظهور القارئ هنا يعني أن لديه تسجيلات
          صوتية موثقة في المكتبة، ولا يعني بالضرورة أن التعرّف الآلي عليه مفعّل.
        </p>
        <input
          aria-label="ابحث عن قارئ"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="ابحث باسم القارئ"
          className="mt-4 h-12 w-full rounded-xl border border-border bg-surface px-4"
        />
      </header>
      <nav
        aria-label="تصنيفات القراء"
        className="mt-4 flex gap-2 overflow-x-auto px-5"
      >
        {(Object.keys(LABELS) as Group[]).map((key) => (
          <button
            key={key}
            onClick={() => setGroup(key)}
            aria-pressed={group === key}
            className={`shrink-0 rounded-full px-4 py-2 text-sm ${group === key ? "bg-accent text-on-accent" : "bg-surface text-muted"}`}
          >
            {LABELS[key]}
          </button>
        ))}
      </nav>
      {failed ? (
        <StateMessage
          icon={<AlertIcon size={40} />}
          title="تعذر تحميل المكتبة"
          body="تحقق من الاتصال ثم أعد المحاولة."
        />
      ) : reciters === null ? (
        <p className="p-8 text-center text-muted">جارٍ تحميل القراء…</p>
      ) : visible.length === 0 ? (
        <p className="p-8 text-center text-muted">لا توجد نتائج مطابقة.</p>
      ) : (
        <ul className="mt-4 grid gap-2 px-5">
          {visible.map((r) => (
            <li key={r.id}>
              <Link
                href={`/reciter?id=${encodeURIComponent(r.id)}`}
                className="flex min-h-16 items-center gap-3 rounded-2xl border border-border bg-surface px-3"
              >
                <Avatar name={r.name_ar} size="md" />
                <span className="min-w-0 grow">
                  <strong className="block">{r.name_ar}</strong>
                  <span className="text-xs text-muted">
                    {r.country || "قارئ"} · {r.styles.length} أنماط تلاوة
                  </span>
                </span>
                <span className="text-xs text-muted">
                  {toArabicDigits(r.styles.length)} ›
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Screen>
  );
}
