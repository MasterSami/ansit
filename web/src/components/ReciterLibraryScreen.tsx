"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getReciters, type ReciterSummary } from "@/lib/api";
import {
  CURATED_RECITERS,
  RECITER_IMAGES,
  RECITER_IMAGE_SOURCES,
} from "@/lib/reciterCatalog";
import { Avatar, Screen, StateMessage } from "./ui";
import { AlertIcon } from "./icons";

interface LibraryEntry extends ReciterSummary {
  image?: string;
  sourceUrl?: string;
  imageCredit?: string;
  audioUrl?: string;
  inApp: boolean;
}

function normalizeName(name: string): string {
  return name
    .replace(/[ً-ٰٟ]/g, "")
    .replace(/[أإآ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ـ/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export function ReciterLibraryScreen() {
  const [reciters, setReciters] = useState<ReciterSummary[] | null>(null);
  const [query, setQuery] = useState("");
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    getReciters().then(setReciters, () => setFailed(true));
  }, []);

  const entries = useMemo(() => {
    if (!reciters) return [];
    const availableNames = new Set(
      reciters.map((r) => normalizeName(r.name_ar)),
    );
    const apiEntries: LibraryEntry[] = reciters.map((r) => {
      const curated = CURATED_RECITERS.find((c) => c.id === r.id);
      const imageSource = RECITER_IMAGE_SOURCES[r.id];
      return {
        ...r,
        image: curated?.image ?? RECITER_IMAGES[r.id],
        sourceUrl: curated?.sourceUrl ?? imageSource?.url,
        imageCredit: curated?.imageCredit ?? imageSource?.credit,
        inApp: true,
      };
    });
    const additions: LibraryEntry[] = CURATED_RECITERS.filter(
      (r) => !availableNames.has(normalizeName(r.name_ar)),
    ).map((r) => ({
      id: r.id,
      name_ar: r.name_ar,
      name_en: r.name_en,
      country: null,
      styles: [],
      image: r.image,
      sourceUrl: r.sourceUrl,
      imageCredit: r.imageCredit,
      audioUrl: r.audioUrl,
      inApp: false,
    }));
    return [...apiEntries, ...additions]
      .filter((r) =>
        `${r.name_ar} ${r.name_en}`
          .toLocaleLowerCase()
          .includes(query.trim().toLocaleLowerCase()),
      )
      .sort((a, b) => a.name_ar.localeCompare(b.name_ar, "ar"));
  }, [reciters, query]);

  return (
    <Screen className="pb-8">
      <header className="px-5 pt-[52px]">
        <Link href="/" className="text-sm text-muted">
          ← الرئيسية
        </Link>
        <h1 className="mt-4 text-2xl font-bold">مكتبة القراء</h1>
        <p className="mt-2 text-sm leading-7 text-muted">
          كل القراء في قائمة واحدة. زر الاستماع داخل التطبيق يظهر للقراء الذين
          لديهم تلاوات مفهرسة؛ أما الروابط الخارجية فتفتح التسجيلات المنشورة في
          مصادرها.
        </p>
        <input
          aria-label="ابحث عن قارئ"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="ابحث باسم القارئ"
          className="mt-4 h-12 w-full rounded-xl border border-border bg-surface px-4"
        />
        {reciters && (
          <p className="mt-2 text-xs text-muted" aria-live="polite">
            {entries.length} قارئًا
          </p>
        )}
      </header>

      {failed ? (
        <StateMessage
          icon={<AlertIcon size={40} />}
          title="تعذر تحميل المكتبة"
          body="تحقق من الاتصال ثم أعد المحاولة."
        />
      ) : reciters === null ? (
        <p className="p-8 text-center text-muted">جارٍ تحميل القراء…</p>
      ) : entries.length === 0 ? (
        <p className="p-8 text-center text-muted">لا توجد نتائج مطابقة.</p>
      ) : (
        <ul className="mt-4 grid gap-2 px-5">
          {entries.map((reciter) => (
            <li
              key={reciter.id}
              className="flex min-h-[76px] items-center gap-3 rounded-2xl border border-border bg-surface px-3 py-2"
            >
              <Avatar name={reciter.name_ar} size="md" image={reciter.image} />
              <span className="min-w-0 grow">
                <strong className="block text-[15px]">{reciter.name_ar}</strong>
                <span className="text-xs text-muted">
                  {reciter.inApp
                    ? `${reciter.styles.length} أنماط متاحة في أنصت`
                    : reciter.audioUrl
                      ? "تسجيل متاح من المصدر الصوتي"
                      : "إضافة تعريفية؛ الصوت غير مفهرس بعد"}
                </span>
                {reciter.sourceUrl && reciter.imageCredit && (
                  <a
                    href={reciter.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="block text-[10px] text-muted underline underline-offset-2"
                  >
                    مصدر الصورة: {reciter.imageCredit}
                  </a>
                )}
              </span>
              {reciter.inApp ? (
                <Link
                  href={`/reciter?id=${encodeURIComponent(reciter.id)}`}
                  className="shrink-0 rounded-full bg-accent-soft px-3 py-2 text-xs font-semibold text-accent"
                >
                  استمع
                </Link>
              ) : reciter.audioUrl ? (
                <a
                  href={reciter.audioUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="shrink-0 rounded-full bg-accent-soft px-3 py-2 text-xs font-semibold text-accent"
                >
                  استمع
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </Screen>
  );
}
