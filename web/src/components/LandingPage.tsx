import Link from "next/link";

import verses from "@/data/verses.json";
import { toArabicDigits } from "@/lib/numerals";
import { displayName, PROFILES } from "@/lib/reciterProfiles";

import { Wordmark } from "./BrandMark";
import { ArrowIcon, BookIcon, MicIcon, SearchIcon, ShieldIcon } from "./icons";
import { InstallBand } from "./InstallPrompt";
import { Portrait } from "./Portrait";
import { SiteHeader } from "./SiteHeader";

const FEATURED = [
  "minshawi",
  "abdul-basit",
  "husary",
  "mustafa-ismail",
  "sudais",
  "muaiqly",
  "alafasy",
  "shuraim",
];

const STEPS = [
  {
    title: "أنصِت",
    body: "اضغط زر الإنصات واسمح باستخدام الميكروفون، ثم قرّب الهاتف من صوت التلاوة لخمس ثوانٍ على الأقل.",
    Icon: MicIcon,
  },
  {
    title: "نُطابِق",
    body: "يُحلَّل المقطع ويُقارن بنص المصحف وبأصوات القرّاء المتاحة للعثور على أقرب تطابق موثوق.",
    Icon: SearchIcon,
  },
  {
    title: "تقرأ",
    body: "تظهر السورة والآية ونصّها، واسم القارئ حين تكون مطابقة صوته متاحة، ومعها التفسير الميسّر.",
    Icon: BookIcon,
  },
];

const VALUES = [
  {
    title: "خدمة القرآن",
    body: "تيسير التعرّف على الآيات والسور والتلاوات لكل من يسمع.",
  },
  {
    title: "الأمانة والموثوقية",
    body: "عرض النتائج بوضوح، دون ادعاء ما لا تثبته المطابقة.",
  },
  {
    title: "نفعٌ يتّسع",
    body: "تجربة نأمل أن تعين على التعلّم ومشاركة الخير.",
  },
];

export function LandingPage() {
  const verse = verses.listen;
  const featured = FEATURED.map((id) =>
    PROFILES.find((profile) => profile.id === id),
  ).filter((profile) => profile !== undefined);

  return (
    <div className="landing">
      <SiteHeader always />

      <main>
        {/* Hero: the claim on one side, the verse that names the app on the other. */}
        <section className="landing-hero shell" aria-labelledby="hero-title">
          <div className="landing-hero-copy ansit-rise">
            <p className="kicker">مبادرة خيرية لخدمة القرآن الكريم</p>
            <h1 id="hero-title">
              من صوت التلاوة
              <br />
              <em>إلى موضع الآية.</em>
            </h1>
            <p className="landing-lead">
              أنصِت يستمع إلى ثوانٍ من أي تلاوة تسمعها حولك، فيدلّك على السورة
              والآية واسم القارئ، ويفتح لك نصّها وتفسيرها.
            </p>
            <div className="landing-actions">
              <Link className="btn btn-primary" href="/listen">
                <MicIcon size={19} />
                جرّب التعرّف على التلاوة
              </Link>
              <Link className="btn btn-outline" href="/reciters">
                تصفّح مكتبة القرّاء
              </Link>
            </div>
            <p className="landing-assurance">
              <ShieldIcon size={16} />
              الميكروفون لا يعمل إلا حين تضغط، والمقطع يُحذف بعد التعرّف.
            </p>
          </div>

          <figure className="landing-folio" aria-labelledby="folio-reference">
            <div className="landing-folio-frame">
              <span className="landing-folio-label">قال الله تعالى</span>
              <blockquote className="quran-text" lang="ar">
                {verse.text}{" "}
                <span className="ayah-mark">
                  ﴿{toArabicDigits(verse.ayah)}﴾
                </span>
              </blockquote>
              <figcaption id="folio-reference">
                سورة الأعراف · الآية {toArabicDigits(verse.ayah)}
              </figcaption>
            </div>
            <p className="landing-folio-credit">
              نص المصحف من{" "}
              <a href="https://tanzil.net" target="_blank" rel="noreferrer">
                مشروع تنزيل
              </a>
              ، معروض دون أي تعديل.
            </p>
          </figure>
        </section>

        {/* How it works, as three numbered columns. */}
        <section className="landing-steps shell" aria-labelledby="steps-title">
          <header className="landing-section-head">
            <p className="kicker">كيف يعمل</p>
            <h2 id="steps-title">ثلاث خطوات، من الصوت إلى الصفحة.</h2>
          </header>
          <ol>
            {STEPS.map(({ title, body, Icon }, index) => (
              <li key={title}>
                <span className="landing-step-number">
                  {toArabicDigits(index + 1)}
                </span>
                <Icon size={22} />
                <h3>{title}</h3>
                <p>{body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Mission. */}
        <section
          className="landing-mission"
          id="mission"
          aria-labelledby="mission-title"
        >
          <div className="shell landing-mission-grid">
            <div>
              <p className="kicker">لماذا أنصِت؟</p>
              <h2 id="mission-title">
                غايةٌ نؤمن بها،
                <br />
                وأثرٌ نرجو امتداده.
              </h2>
            </div>
            <div className="landing-prose">
              <p>
                انطلقت أنصِت مبادرةً خيرية هدفها الإسهام في خدمة القرآن الكريم
                والسنة النبوية، وتيسير وصول الناس إلى المعرفة والمحتوى النافع
                باستخدام التقنية.
              </p>
              <p>
                نبدأ من لحظة إنصات: آية تسمعها ولا تعرف موضعها، أو تلاوة ترغب في
                معرفة قارئها. ونوظّف التقنية لمساعدتك على الوصول إلى المعلومة، في
                تجربة بسيطة تحترم قدسية المحتوى وأمانة نقله.
              </p>
            </div>
            <ul className="landing-values">
              {VALUES.map((value) => (
                <li key={value.title}>
                  <h3>{value.title}</h3>
                  <p>{value.body}</p>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* What the technology does, and what it does not. */}
        <section
          className="landing-tech shell"
          id="ai"
          aria-labelledby="ai-title"
        >
          <header className="landing-section-head">
            <p className="kicker">التقنية وراء التجربة</p>
            <h2 id="ai-title">الذكاء الاصطناعي وسيلة، لا غاية.</h2>
            <p>
              يحلّل النظام خصائص المقطع الصوتي ويقارنه بنص المصحف وبأصوات القرّاء
              المتاحة، ثم يعرض أقرب نتيجة يمكن الاعتماد عليها. وإن لم تكن
              المطابقة واضحة قال ذلك صراحة.
            </p>
          </header>
          <aside className="landing-note">
            <ShieldIcon size={20} />
            <p>
              <strong>توضيح مهم:</strong> أنصِت أداة تقنية مساعدة للتعرّف على
              التلاوات ومواضع الآيات، وليست أداة لتفسير القرآن أو إصدار الفتاوى
              والأحكام الشرعية. وعند عدم وضوح المطابقة، لا ينبغي اعتبار النتيجة
              مؤكدة.
            </p>
          </aside>
        </section>

        {/* Reciters. */}
        <section
          className="landing-reciters shell"
          aria-labelledby="reciters-title"
        >
          <header className="landing-section-head landing-section-head-row">
            <div>
              <p className="kicker">مكتبة القرّاء</p>
              <h2 id="reciters-title">أصواتٌ لكلٍّ منها سيرة.</h2>
            </div>
            <Link className="text-link" href="/reciters">
              كل القرّاء
              <ArrowIcon size={16} />
            </Link>
          </header>
          <ul className="landing-reciter-strip">
            {featured.map((profile) => (
              <li key={profile.id}>
                <Link href={`/reciters/${profile.id}`}>
                  <Portrait
                    name={profile.name_ar}
                    src={profile.portrait?.src}
                    size={132}
                  />
                  <strong>{displayName(profile)}</strong>
                  {profile.country_ar && <small>{profile.country_ar}</small>}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <InstallBand />

        <section
          className="landing-closing shell"
          aria-labelledby="closing-title"
        >
          <p className="kicker">شاركنا طريق النفع</p>
          <h2 id="closing-title">
            قد تكون بداية الخير
            <br />
            <em>آيةٌ تصل إليها.</em>
          </h2>
          <Link className="btn btn-primary" href="/listen">
            <MicIcon size={19} />
            ابدأ الإنصات الآن
          </Link>
        </section>
      </main>

      <footer className="landing-footer">
        <div className="shell landing-footer-grid">
          <Wordmark tagline="التقنية في خدمة القرآن" />
          <p>
            مبادرة خيرية تسعى لخدمة القرآن الكريم والسنة النبوية.
            <br />
            تم التصميم والبرمجة والتدريب بواسطة م. أحمد سامي التحيوي
          </p>
          <nav aria-label="روابط التذييل">
            <Link href="/listen">الإنصات</Link>
            <Link href="/reciters">القرّاء</Link>
            <Link href="/mushaf">المصحف</Link>
            <Link href="/settings">الإعدادات والمصادر</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
