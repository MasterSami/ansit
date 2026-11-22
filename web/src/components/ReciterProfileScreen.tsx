"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";

import { getReciter, type ReciterDetail, type Style } from "@/lib/api";
import { listEntries } from "@/lib/history";
import { ayahCount, toArabicDigits } from "@/lib/numerals";
import {
  categoryLabel,
  displayName,
  lifespan,
  relatedProfiles,
  type ReciterProfile,
} from "@/lib/reciterProfiles";
import { STYLE_TAB } from "@/lib/text";
import { daysAgo } from "@/lib/time";

import {
  ArrowIcon,
  CheckIcon,
  ExternalIcon,
  HeartIcon,
  MicIcon,
  PlayIcon,
} from "./icons";
import { PlayerBar } from "./PlayerBar";
import { Portrait } from "./Portrait";
import { usePlayer, useSurahs } from "./Providers";
import { SiteHeader } from "./SiteHeader";
import { BottomNav } from "./BottomNav";

const STYLE_ORDER: Style[] = ["murattal", "mujawwad", "muallim"];
const FAVOURITES_KEY = "ansit.favourites";

function readFavourites(): string[] {
  try {
    return JSON.parse(localStorage.getItem(FAVOURITES_KEY) ?? "[]") as string[];
  } catch {
    return [];
  }
}

/** What the server knows about this reciter: undefined while loading. */
type Server = ReciterDetail | "absent" | "offline" | undefined;

export function ReciterProfileScreen({ profile }: { profile: ReciterProfile }) {
  const name = displayName(profile);
  const [server, setServer] = useState<Server>(
    profile.in_registry ? undefined : "absent",
  );
  const [favourite, setFavourite] = useState(false);

  useEffect(() => {
    queueMicrotask(() => setFavourite(readFavourites().includes(profile.id)));
    if (!profile.in_registry) return;
    getReciter(profile.id).then(setServer, (error: { status?: number }) =>
      setServer(error?.status === 404 ? "absent" : "offline"),
    );
  }, [profile.id, profile.in_registry]);

  const toggleFavourite = () => {
    const current = readFavourites();
    const next = favourite
      ? current.filter((id) => id !== profile.id)
      : [...current, profile.id];
    try {
      localStorage.setItem(FAVOURITES_KEY, JSON.stringify(next));
    } catch {
      // storage blocked: the heart still toggles for this visit
    }
    setFavourite(!favourite);
  };

  const detail = typeof server === "object" ? server : null;
  const recognised = detail ? (detail.recognition_enabled ?? true) : false;
  const life = lifespan(profile, toArabicDigits);
  const category = categoryLabel(profile.category);
  const related = relatedProfiles(profile);

  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <SiteHeader />
      <main className="profile shell">
        <nav className="profile-crumbs" aria-label="مسار التنقل">
          <Link href="/reciters">
            <ArrowIcon size={15} className="rotate-180" />
            مكتبة القرّاء
          </Link>
        </nav>

        <header className="profile-head ansit-rise">
          <Portrait
            name={profile.name_ar}
            src={profile.portrait?.src}
            size={240}
            priority
            className="profile-portrait"
          />
          <div className="profile-head-text">
            {category && <p className="kicker">{category}</p>}
            <h1>{name}</h1>
            <p className="profile-name-en" dir="ltr" lang="en">
              {profile.name_en}
            </p>
            <dl className="profile-facts">
              {profile.country_ar && (
                <div>
                  <dt>البلد</dt>
                  <dd>{profile.country_ar}</dd>
                </div>
              )}
              {life && (
                <div>
                  <dt>{profile.died ? "حياته" : "الميلاد"}</dt>
                  <dd>{life}</dd>
                </div>
              )}
              <div>
                <dt>التعرّف الصوتي</dt>
                <dd>
                  <RecognitionBadge server={server} recognised={recognised} />
                </dd>
              </div>
            </dl>
            {profile.short_bio_ar && (
              <p className="profile-intro">
                {toArabicDigits(profile.short_bio_ar)}
              </p>
            )}
            <div className="profile-actions">
              {recognised && (
                <Link className="btn btn-primary" href="/listen">
                  <MicIcon size={18} />
                  تعرّف على تلاوة له
                </Link>
              )}
              <button
                type="button"
                className="btn btn-outline"
                aria-pressed={favourite}
                onClick={toggleFavourite}
              >
                <HeartIcon size={17} filled={favourite} />
                {favourite ? "في المفضّلة" : "أضِف إلى المفضّلة"}
              </button>
            </div>
            {profile.portrait?.credit && (
              <p className="profile-credit">
                مصدر الصورة:{" "}
                {profile.portrait.source_url ? (
                  <a
                    href={profile.portrait.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {profile.portrait.credit}
                  </a>
                ) : (
                  profile.portrait.credit
                )}
              </p>
            )}
          </div>
        </header>

        <div className="profile-body">
          <div className="profile-main">
            <section aria-labelledby="bio-title">
              <h2 id="bio-title">السيرة</h2>
              {profile.bio_ar?.length ? (
                <div className="profile-prose">
                  {profile.bio_ar.map((paragraph) => (
                    <p key={paragraph.slice(0, 32)}>
                      {toArabicDigits(paragraph)}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="profile-empty">
                  {profile.short_bio_ar
                    ? "لم نوثّق بعد سيرة مفصّلة لهذا القارئ. نعرض ما تأكّدنا منه فقط."
                    : "لم نجد بعد مصادر موثوقة لسيرة هذا القارئ، ولا نكتب ما لا نتأكد منه."}
                </p>
              )}
              {profile.milestones_ar?.length ? (
                <>
                  <h3>محطات موثّقة</h3>
                  <ul className="profile-milestones">
                    {profile.milestones_ar.map((item) => (
                      <li key={item}>{toArabicDigits(item)}</li>
                    ))}
                  </ul>
                </>
              ) : null}
              {profile.sources?.length ? (
                <>
                  <h3>المصادر</h3>
                  <ul className="profile-sources">
                    {profile.sources.map((source) => (
                      <li key={source.url}>
                        <a href={source.url} target="_blank" rel="noreferrer">
                          {source.title}
                          <ExternalIcon size={13} />
                        </a>
                      </li>
                    ))}
                  </ul>
                </>
              ) : null}
            </section>
          </div>

          <aside className="profile-side">
            <Suspense>
              <Listening profile={profile} server={server} />
            </Suspense>
          </aside>
        </div>

        {related.length > 0 && (
          <section className="profile-related" aria-labelledby="related-title">
            <h2 id="related-title">
              {category ? `من ${category}` : "قرّاء آخرون"}
            </h2>
            <ul>
              {related.map((other) => (
                <li key={other.id}>
                  <Link href={`/reciters/${other.id}`}>
                    <Portrait
                      name={other.name_ar}
                      src={other.portrait?.src}
                      size={72}
                    />
                    <span>
                      <strong>{displayName(other)}</strong>
                      {other.country_ar && <small>{other.country_ar}</small>}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        )}
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

function RecognitionBadge({
  server,
  recognised,
}: {
  server: Server;
  recognised: boolean;
}) {
  if (server === undefined)
    return <span className="badge badge-muted">جارٍ التحقق…</span>;
  if (server === "offline")
    return <span className="badge badge-muted">تعذّر الاتصال بالخادم</span>;
  return recognised ? (
    <span className="badge badge-on">
      <CheckIcon size={13} />
      يتعرّف أنصِت على صوته
    </span>
  ) : (
    <span className="badge badge-muted">غير مدعوم حاليًا</span>
  );
}

/** Recordings: per-ayah audio where it exists, otherwise full surahs. */
function Listening({
  profile,
  server,
}: {
  profile: ReciterProfile;
  server: Server;
}) {
  const fromSurah = Number(useSearchParams().get("surah")) || null;
  const surahs = useSurahs();
  const player = usePlayer();
  const [picked, setPicked] = useState<Style | null>(null);
  const [heardToday, setHeardToday] = useState<Set<number>>(new Set());
  const detail = typeof server === "object" ? server : null;

  useEffect(() => {
    // Surahs identified today with this reciter are marked.
    listEntries().then(
      (entries) =>
        setHeardToday(
          new Set(
            entries
              .filter(
                (e) =>
                  daysAgo(e.createdAt) === 0 &&
                  (e.userReciter?.id === profile.id ||
                    (!e.userReciter && e.reciter?.id === profile.id)),
              )
              .map((e) => e.ayah.surah),
          ),
        ),
      () => undefined,
    );
  }, [profile.id]);

  // One entry per style: per-ayah audio when there is some, else full surahs.
  const recordings = useMemo(() => {
    if (!detail) return [];
    const styles = new Set<Style>([
      ...detail.ayah_audio.map((a) => a.style),
      ...(detail.surah_audio ?? []).map((a) => a.style),
    ]);
    return STYLE_ORDER.filter((style) => styles.has(style)).map((style) => {
      const ayah = detail.ayah_audio.find((a) => a.style === style);
      const surah = detail.surah_audio?.find((a) => a.style === style);
      return ayah
        ? { style, kind: "ayah" as const, template: ayah.url_template }
        : { style, kind: "surah" as const, template: surah!.url_template };
    });
  }, [detail]);
  const recording =
    recordings.find((r) => r.style === picked) ?? recordings[0] ?? null;

  const ordered = useMemo(
    () =>
      surahs
        ? [...surahs].sort(
            (a, b) =>
              Number(b.number === fromSurah) - Number(a.number === fromSurah) ||
              a.number - b.number,
          )
        : null,
    [surahs, fromSurah],
  );

  const play = (surah: number, stopAtSurahEnd: boolean) => {
    if (!recording || !detail) return;
    player.play({
      reciterId: detail.id,
      reciterName: displayName(profile),
      kind: recording.kind,
      template: recording.template,
      surah,
      ayah: 1,
      stopAtSurahEnd,
    });
  };

  return (
    <section aria-labelledby="listen-title" className="profile-listen">
      <h2 id="listen-title">التلاوات</h2>

      {server === undefined && (
        <p className="profile-empty" role="status">
          جارٍ تحميل التلاوات…
        </p>
      )}
      {server === "offline" && (
        <p className="profile-empty" role="status">
          تعذّر تحميل التلاوات. تحقّق من اتصالك ثم أعد فتح الصفحة.
        </p>
      )}
      {server === "absent" &&
        (profile.external_audio ? (
          <a
            className="btn btn-outline"
            href={profile.external_audio}
            target="_blank"
            rel="noreferrer"
          >
            استمع من المصدر
            <ExternalIcon size={15} />
          </a>
        ) : (
          <p className="profile-empty">
            لا تتوفر لدينا تسجيلات لهذا القارئ حتى الآن.
          </p>
        ))}

      {detail && !recording && (
        <p className="profile-empty">
          لا تتوفر لدينا تسجيلات لهذا القارئ حتى الآن.
        </p>
      )}

      {detail && recording && (
        <>
          {recordings.length > 1 && (
            <div role="tablist" aria-label="نوع التلاوة" className="tabs">
              {recordings.map((r) => (
                <button
                  key={r.style}
                  type="button"
                  role="tab"
                  aria-selected={r.style === recording.style}
                  onClick={() => setPicked(r.style)}
                >
                  {STYLE_TAB[r.style]}
                </button>
              ))}
            </div>
          )}
          <p className="profile-listen-note">
            {recording.kind === "ayah"
              ? "التشغيل آيةً آية، وينتقل تلقائيًا إلى الآية التالية."
              : "تسجيل للسورة كاملة."}
          </p>
          <button
            type="button"
            className="btn btn-primary profile-play-all"
            onClick={() => play(1, false)}
          >
            <PlayIcon size={15} />
            استمع من أول المصحف
          </button>
          <ul className="surah-list">
            {(ordered ?? []).map((surah) => {
              const heard = heardToday.has(surah.number);
              return (
                <li key={surah.number} className={heard ? "is-heard" : ""}>
                  <span className="surah-number">
                    {toArabicDigits(surah.number)}
                  </span>
                  <span className="surah-name">
                    <strong>{surah.name_ar}</strong>
                    <small>
                      {ayahCount(surah.ayah_count)}
                      {heard && " · تعرّفت عليها اليوم"}
                    </small>
                  </span>
                  <button
                    type="button"
                    aria-label={`تشغيل سورة ${surah.name_ar}`}
                    onClick={() => play(surah.number, true)}
                  >
                    <PlayIcon size={13} />
                  </button>
                </li>
              );
            })}
          </ul>
          {ordered === null && (
            <p className="profile-empty" role="status">
              جارٍ تحميل قائمة السور…
            </p>
          )}
        </>
      )}
    </section>
  );
}
