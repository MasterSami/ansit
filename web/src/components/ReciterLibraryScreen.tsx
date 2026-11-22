"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getReciters, type ReciterSummary } from "@/lib/api";
import { toArabicDigits } from "@/lib/numerals";
import {
  CATEGORIES,
  categoryLabel,
  displayName,
  matchesQuery,
  PROFILES,
  type ReciterCategory,
} from "@/lib/reciterProfiles";

import { BottomNav } from "./BottomNav";
import { CheckIcon, CloseIcon, SearchIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { Portrait } from "./Portrait";
import { SiteHeader } from "./SiteHeader";

type Filter = "all" | ReciterCategory;

/**
 * The reciter library. Names, portraits and biographies are part of the app,
 * so the page works without the server; what the server adds, once it
 * answers, is which voices recognition currently supports.
 */
export function ReciterLibraryScreen() {
  const [server, setServer] = useState<ReciterSummary[] | null | "offline">(
    null,
  );
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    getReciters().then(setServer, () => setServer("offline"));
  }, []);

  const recognised = useMemo(
    () =>
      Array.isArray(server)
        ? new Set(
            server
              .filter((r) => r.recognition_enabled ?? true)
              .map((r) => r.id),
          )
        : null,
    [server],
  );

  const shown = useMemo(
    () =>
      PROFILES.filter(
        (profile) =>
          (filter === "all" || profile.category === filter) &&
          matchesQuery(profile, query),
      ).sort((a, b) => a.name_ar.localeCompare(b.name_ar, "ar")),
    [filter, query],
  );

  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <SiteHeader />
      <main className="library shell">
        <header className="library-head">
          <div>
            <p className="kicker">مكتبة القرّاء</p>
            <h1>أصواتٌ لكلٍّ منها سيرة.</h1>
            <p>
              {toArabicDigits(PROFILES.length)} قارئًا من مصر والحرمين الشريفين
              والعالم. لكل قارئ صفحة فيها ما وثّقناه من سيرته وما يتوفر من
              تلاواته.
              {recognised &&
                ` يتعرّف أنصِت حاليًا على صوت ${toArabicDigits(recognised.size)} منهم.`}
            </p>
          </div>
          <label className="library-search">
            <SearchIcon size={18} />
            <span className="sr-only">ابحث عن قارئ</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="ابحث بالاسم، بالعربية أو بالإنجليزية"
            />
            {query && (
              <button
                type="button"
                aria-label="مسح البحث"
                onClick={() => setQuery("")}
              >
                <CloseIcon size={15} />
              </button>
            )}
          </label>
        </header>

        <div
          role="tablist"
          aria-label="تصنيف القرّاء"
          className="tabs library-tabs"
        >
          {[{ id: "all" as const, label: "الكل" }, ...CATEGORIES].map(
            (category) => (
              <button
                key={category.id}
                type="button"
                role="tab"
                aria-selected={filter === category.id}
                onClick={() => setFilter(category.id)}
              >
                {category.label}
              </button>
            ),
          )}
        </div>

        <p className="library-count" role="status">
          {shown.length === 0
            ? "لا نتائج مطابقة. جرّب اسمًا آخر أو تصنيفًا آخر."
            : `${toArabicDigits(shown.length)} قارئًا`}
        </p>

        <ul className="library-grid">
          {shown.map((profile) => {
            const supported = recognised?.has(profile.id) ?? false;
            const category = categoryLabel(profile.category);
            return (
              <li key={profile.id}>
                <Link href={`/reciters/${profile.id}`} className="reciter-card">
                  <Portrait
                    name={profile.name_ar}
                    src={profile.portrait?.src}
                    size={88}
                  />
                  <span className="reciter-card-text">
                    <strong>{displayName(profile)}</strong>
                    <span className="reciter-card-en" dir="ltr" lang="en">
                      {profile.name_en}
                    </span>
                    <span className="reciter-card-meta">
                      {[profile.country_ar, category]
                        .filter(Boolean)
                        .join(" · ")}
                    </span>
                    {profile.short_bio_ar && (
                      <span className="reciter-card-bio">
                        {toArabicDigits(profile.short_bio_ar)}
                      </span>
                    )}
                    <span className="reciter-card-tags">
                      {supported && (
                        <span className="badge badge-on">
                          <CheckIcon size={12} />
                          تعرّف صوتي
                        </span>
                      )}
                      {profile.in_registry ? (
                        <span className="badge badge-muted">تلاوات متاحة</span>
                      ) : profile.external_audio ? (
                        <span className="badge badge-muted">تسجيل خارجي</span>
                      ) : null}
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      </main>
      <div className="mt-auto">
        <div className="shell">
          <PlayerBar />
        </div>
        <BottomNav current="reciters" />
      </div>
    </div>
  );
}
