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
import { AlertIcon, SearchIcon } from "./icons";

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
    const availableIds = new Set(reciters.map((r) => r.id));
    const apiEntries: LibraryEntry[] = reciters.map((r) => {
      const curated = CURATED_RECITERS.find((c) => c.id === r.id);
      const imageSource = RECITER_IMAGE_SOURCES[r.id];
      return {
        ...r,
        // Prefer the curated full name when the API uses a shortened variant.
        name_ar: curated?.name_ar ?? r.name_ar,
        name_en: curated?.name_en ?? r.name_en,
        image: curated?.image ?? RECITER_IMAGES[r.id],
        sourceUrl: curated?.sourceUrl ?? imageSource?.url,
        imageCredit: curated?.imageCredit ?? imageSource?.credit,
        inApp: true,
      };
    });
    const additions: LibraryEntry[] = CURATED_RECITERS.filter(
      (r) =>
        !availableIds.has(r.id) &&
        !availableNames.has(normalizeName(r.name_ar)),
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
    <Screen wide className="reciter-library-screen">
      <header className="reciter-library-header">
        <div className="reciter-library-topbar">
          <Link href="/" className="reciter-library-back">← الرئيسية</Link>
          <span className="reciter-library-kicker">أنصِت · مكتبة الأصوات</span>
        </div>
        <div className="reciter-library-intro">
          <div>
            <p className="reciter-library-eyebrow">كل القراء في مكان واحد</p>
            <h1>مكتبة القراء</h1>
            <p className="reciter-library-description">
              تصفّح القراء وابحث عن الاسم. علامة التعرّف توضّح الأصوات الموجودة في أنصت.
            </p>
          </div>
          <label className="reciter-library-search">
            <SearchIcon size={19} />
            <input
              aria-label="ابحث عن قارئ"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="ابحث باسم القارئ"
            />
            {query && (
              <button type="button" onClick={() => setQuery("")} aria-label="مسح البحث">
                ×
              </button>
            )}
          </label>
        </div>
        {reciters && (
          <div className="reciter-library-summary" aria-live="polite">
            <span><strong>{entries.length}</strong> قارئ</span>
            <span><strong>{entries.filter((entry) => entry.inApp).length}</strong> بصمة متاحة للتعرّف</span>
            <span><strong>{entries.filter((entry) => !entry.inApp).length}</strong> في الدليل</span>
          </div>
        )}
      </header>

      {failed ? (
        <StateMessage
          icon={<AlertIcon size={40} />}
          title="تعذر تحميل المكتبة"
          body="تحقق من الاتصال ثم أعد المحاولة."
        />
      ) : reciters === null ? (
        <div className="reciter-library-loading" role="status">جارٍ تحميل مكتبة القراء…</div>
      ) : entries.length === 0 ? (
        <div className="reciter-library-empty">لا توجد نتائج مطابقة.</div>
      ) : (
        <ul className="reciter-library-grid">
          {entries.map((reciter) => (
            <li key={reciter.id} className="reciter-library-card">
              <div className="reciter-library-card-main">
                <Avatar name={reciter.name_ar} size="lg" image={reciter.image} />
                <div className="reciter-library-card-name">
                  <span className={`reciter-library-badge ${reciter.inApp ? "is-available" : "is-directory"}`}>
                    <span aria-hidden="true" />
                    {reciter.inApp ? "بصمة متاحة" : "في الدليل"}
                  </span>
                  <h2>{reciter.name_ar}</h2>
                  <p dir="ltr">{reciter.name_en}</p>
                </div>
              </div>
              <div className="reciter-library-card-meta">
                {reciter.inApp
                  ? reciter.styles.map((style) => <span className="reciter-library-style" key={style}>{style}</span>)
                  : <span>{reciter.audioUrl ? "له تسجيل منشور" : "لا يتوفر تسجيل مصدر حاليًا"}</span>}
              </div>
              <div className="reciter-library-card-footer">
                {reciter.sourceUrl && reciter.imageCredit && (
                  <a href={reciter.sourceUrl} target="_blank" rel="noreferrer" className="reciter-library-credit">
                    مصدر الصورة: {reciter.imageCredit}
                  </a>
                )}
                {reciter.inApp ? (
                  <Link href={`/reciter?id=${encodeURIComponent(reciter.id)}`} className="reciter-library-action">
                    استمع داخل أنصت <span aria-hidden="true">←</span>
                  </Link>
                ) : reciter.audioUrl ? (
                  <a href={reciter.audioUrl} target="_blank" rel="noreferrer" className="reciter-library-action">
                    استمع للمصدر <span aria-hidden="true">↗</span>
                  </a>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      )}
    </Screen>
  );
}
