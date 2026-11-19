import Image from "next/image";
import Link from "next/link";
import type { Metadata } from "next";

import { BookIcon, MicIcon, PlayIcon, SearchIcon, ShieldIcon } from "@/components/icons";

const featuredReciters = [
  { id: "sudais", name: "عبدالرحمن السديس", image: "https://quranmedia.online/images/reciters/abdul-rahman-al-sudais/image/180x180.jpg.webp" },
  { id: "alafasy", name: "مشاري العفاسي", image: "https://quranmedia.online/images/reciters/mishary-rashid-alafasy/image/180x180.jpg.webp" },
  { id: "muaiqly", name: "ماهر المعيقلي", image: "https://quranmedia.online/images/reciters/maher-al-muaiqly/image/180x180.jpg.webp" },
  { id: "shuraim", name: "سعود الشريم", image: "https://quranmedia.online/images/reciters/saud-al-shuraim/image/180x180.jpg.webp" },
  { id: "neana", name: "أحمد نعينع", image: "https://quranmedia.online/images/reciters/ahmed-naina/image/180x180.jpg.webp" },
  { id: "yasser", name: "ياسر الدوسري", image: "https://storage.googleapis.com/way2quran_storage/imgs/yasser-al-dosary.jpg" },
];

const waveHeights = [14, 24, 32, 19, 40, 28, 48, 22, 36, 16, 29, 42, 20, 34, 15];

export const metadata: Metadata = {
  title: "أنصِت | التقنية في خدمة القرآن الكريم",
  description:
    "أنصت مبادرة خيرية توظّف التقنية والذكاء الاصطناعي لتيسير التعرّف على آيات القرآن الكريم وتلاوات القرّاء.",
};

function BrandMark() {
  return (
    <span className="landing-brand-mark" aria-hidden="true">
      <svg viewBox="0 0 48 48" fill="none">
        <path d="M12 38V22a12 12 0 0 1 24 0v16" />
        <path d="M18 37V23a6 6 0 0 1 12 0v14" />
        <path d="M24 28v10M8 41h32" />
      </svg>
    </span>
  );
}

function Waveform({ compact = false }: { compact?: boolean }) {
  return (
    <span className={`landing-waveform${compact ? " landing-waveform-compact" : ""}`} aria-hidden="true">
      {waveHeights.map((height, index) => (
        <i key={`${height}-${index}`} style={{ height: `${height}px`, animationDelay: `${index * 65}ms` }} />
      ))}
    </span>
  );
}

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function SectionKicker({ children }: { children: React.ReactNode }) {
  return <p className="landing-section-kicker"><span />{children}</p>;
}

export function LandingPage() {
  return (
    <div className="landing-page">
      <header className="landing-header landing-shell">
        <Link className="landing-brand" href="/" aria-label="أنصت — الرئيسية">
          <BrandMark />
          <span className="landing-brand-copy"><strong>أنصِت</strong><small>من الصوت إلى الآية</small></span>
        </Link>
        <nav className="landing-nav" aria-label="التنقل الرئيسي">
          <a href="#mission">رسالتنا</a>
          <a href="#ai">الذكاء الاصطناعي</a>
          <a href="#how">كيف يعمل</a>
          <a href="#reciters">مكتبة القرّاء</a>
        </nav>
        <Link className="landing-nav-cta" href="/mushaf">اكتشف أنصت <ArrowIcon /></Link>
      </header>

      <main>
        <section className="landing-hero landing-shell" aria-labelledby="hero-title">
          <div className="landing-hero-copy">
            <div className="landing-quran-verse">
              <span>قال الله تعالى</span>
              <p>وَإِذَا قُرِئَ الْقُرْآنُ فَاسْتَمِعُوا لَهُ وَأَنْصِتُوا لَعَلَّكُمْ تُرْحَمُونَ</p>
              <small>سورة الأعراف · ٢٠٤</small>
            </div>
            <p className="landing-eyebrow"><span className="landing-eyebrow-dot" />مبادرة خيرية لخدمة القرآن الكريم والسنة النبوية</p>
            <h1 id="hero-title">من صوت التلاوة،<br /><span>إلى موضع الآية.</span></h1>
            <p className="landing-hero-lead">
              أنصت مبادرة تقنية خيرية تسخّر أدوات الذكاء الاصطناعي لتيسير التعرّف على آيات القرآن الكريم وتلاوات القرّاء؛ لتكون التقنية وسيلة تقرّبك من كتاب الله وتعينك على متابعة ما تسمع.
            </p>
            <div className="landing-actions">
              <Link className="landing-button landing-button-primary" href="/listen"><MicIcon size={20} />جرّب التعرّف على التلاوة<ArrowIcon /></Link>
              <a className="landing-button landing-button-quiet" href="#mission">تعرّف على رسالتنا</a>
            </div>
            <div className="landing-android-note"><span>قريبًا</span> تطبيق أنصت للهواتف بنظام Android</div>
            <div className="landing-hero-trust">
              <span><ShieldIcon size={17} />خصوصيتك أولوية</span>
              <span><BookIcon size={17} />خدمة القرآن غايتنا</span>
            </div>
          </div>

          <div className="landing-hero-visual" aria-label="تصميم بصري يرمز إلى المصحف والتلاوة">
            <div className="landing-hero-halo" />
            <div className="landing-hero-arch">
              <div className="landing-arch-inner">
                <div className="landing-ornament">۞</div>
                <span className="landing-arch-label">أنصِت</span>
                <div className="landing-arch-rule" />
                <p className="landing-arch-verse">وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا</p>
                <span className="landing-arch-reference">المزّمّل · ٤</span>
                <div className="landing-arch-wave"><Waveform /></div>
              </div>
            </div>
            <div className="landing-floating-card landing-floating-top"><span className="landing-floating-icon"><MicIcon size={19} /></span><span><small>استمع إلى التلاوة</small><strong>ثوانٍ قليلة تكفي للبدء</strong></span></div>
            <div className="landing-floating-card landing-floating-bottom"><span className="landing-floating-icon"><BookIcon size={19} /></span><span><small>النتيجة</small><strong>السورة وموضع الآية</strong></span><b>✓</b></div>
            <span className="landing-orbit landing-orbit-one" /><span className="landing-orbit landing-orbit-two" />
          </div>
        </section>

        <section className="landing-manifesto landing-shell" aria-label="رسالة أنصت">
          <p>نؤمن أن التقنية حين تُسخّر للخير، يمكن أن تفتح أبوابًا جديدة للمعرفة والنفع.</p>
          <span className="landing-manifesto-caption">أنصت — التقنية في خدمة القرآن</span>
        </section>

        <section className="landing-mission landing-shell" id="mission" aria-labelledby="mission-title">
          <div className="landing-mission-intro">
            <SectionKicker>لماذا أنصت؟</SectionKicker>
            <h2 id="mission-title">غايةٌ نؤمن بها،<br /><span>وأثرٌ نرجو امتداده.</span></h2>
          </div>
          <div className="landing-mission-copy">
            <p>انطلقت أنصت كمبادرة خيرية يكون هدفها الإسهام في خدمة القرآن الكريم والسنة النبوية، وتيسير وصول الناس إلى المعرفة والمحتوى النافع باستخدام التقنية.</p>
            <p>نبدأ من لحظة إنصات؛ آية تسمعها ولا تعرف موضعها، أو تلاوة ترغب في معرفة قارئها. ونوظّف التقنية لمساعدتك على الوصول إلى المعلومة، في تجربة بسيطة تحترم قدسية المحتوى وأمانة نقله.</p>
          </div>
          <div className="landing-values">
            <article><span>01</span><BookIcon size={22} /><h3>خدمة القرآن</h3><p>تسهيل التعرّف على الآيات والسور والتلاوات.</p></article>
            <article><span>02</span><ShieldIcon size={22} /><h3>الأمانة والموثوقية</h3><p>عرض النتائج بوضوح دون ادعاء ما لا تثبته المطابقة.</p></article>
            <article><span>03</span><span className="landing-value-spark">✦</span><h3>نفعٌ يتسع</h3><p>تجربة نأمل أن تعين على التعلم ومشاركة الخير.</p></article>
          </div>
        </section>

        <section className="landing-ai-section" id="ai" aria-labelledby="ai-title">
          <div className="landing-shell">
            <div className="landing-ai-heading">
              <div><SectionKicker>التقنية وراء التجربة</SectionKicker><h2 id="ai-title">ماذا يفعل الذكاء الاصطناعي؟<br /><span>وكيف يساعدك أنصت؟</span></h2></div>
              <p>الذكاء الاصطناعي هنا ليس غاية بحد ذاته؛ إنه وسيلة لتحليل الصوت ومقارنة التلاوة بالمحتوى المتاح، ثم إظهار أقرب نتيجة يمكن الاعتماد عليها.</p>
            </div>
            <div className="landing-ai-flow">
              <article><span className="landing-ai-number">01</span><div className="landing-ai-icon"><MicIcon size={23} /></div><h3>استقبال مقطع صوتي</h3><p>تبدأ أنت الاستماع وتمنح إذن استخدام الميكروفون، فيلتقط التطبيق جزءًا قصيرًا من التلاوة.</p></article>
              <div className="landing-ai-connector"><ArrowIcon /></div>
              <article><span className="landing-ai-number">02</span><div className="landing-ai-icon"><SearchIcon size={24} /></div><h3>تحليل ومطابقة</h3><p>تحلل الأنظمة خصائص المقطع وتقارنه ببيانات الآيات والتلاوات المتاحة للعثور على تطابق مناسب.</p></article>
              <div className="landing-ai-connector"><ArrowIcon /></div>
              <article><span className="landing-ai-number">03</span><div className="landing-ai-icon"><BookIcon size={23} /></div><h3>الوصول إلى الآية</h3><p>تظهر السورة والآية عند توافر نتيجة مناسبة، ويظهر اسم القارئ عندما تكون مطابقة صوته متاحة وموثوقة.</p></article>
            </div>
            <div className="landing-ai-disclaimer"><ShieldIcon size={20} /><p><strong>توضيح مهم:</strong> أنصت أداة تقنية مساعدة للتعرّف على التلاوات ومواضع الآيات، وليست أداة لتفسير القرآن أو إصدار الفتاوى والأحكام الشرعية. وعند عدم وضوح المطابقة، لا ينبغي اعتبار النتيجة مؤكدة.</p></div>
          </div>
        </section>

        <section className="landing-how landing-shell" id="how" aria-labelledby="how-title">
          <div className="landing-how-heading"><SectionKicker>تجربة بسيطة</SectionKicker><h2 id="how-title">من لحظة الإنصات،<br /><span>إلى معرفة الموضع.</span></h2><p>لا تحتاج إلى معرفة اسم السورة مسبقًا. ابدأ من الصوت واتبع الخطوات.</p><Link className="landing-text-link" href="/listen">ابدأ التجربة الآن <ArrowIcon /></Link></div>
          <div className="landing-how-steps">
            <article><span>١</span><MicIcon size={22} /><h3>ابدأ الاستماع</h3><p>اضغط على زر الاستماع واسمح للمتصفح باستخدام الميكروفون.</p></article>
            <article><span>٢</span><Waveform compact /><h3>قرّب صوت التلاوة</h3><p>اجعل التلاوة واضحة ودع التطبيق يحلل مقطعًا قصيرًا منها.</p></article>
            <article><span>٣</span><BookIcon size={22} /><h3>تعرّف على الآية</h3><p>راجع السورة ورقم الآية، واسم القارئ إن توفرت مطابقة موثوقة.</p></article>
          </div>
        </section>

        <section className="landing-features landing-shell" aria-labelledby="features-title">
          <div className="landing-features-heading"><SectionKicker>مصمّم لخدمة رحلتك</SectionKicker><h2 id="features-title">تفاصيل صغيرة،<br /><span>تجعل الوصول أسهل.</span></h2></div>
          <div className="landing-feature-grid">
            <article><BookIcon size={22} /><h3>موضع الآية</h3><p>الوصول إلى اسم السورة ورقم الآية والنص المرتبط بالنتيجة.</p></article>
            <article><PlayIcon size={21} /><h3>التعرّف على القارئ</h3><p>إظهار اسم القارئ عندما تتوفر بيانات ومطابقة صوتية مناسبة.</p></article>
            <article><ShieldIcon size={22} /><h3>خصوصية أوضح</h3><p>لا يحتفظ الخادم بملف التسجيل الصوتي بعد انتهاء عملية التعرّف.</p></article>
          </div>
        </section>

        <section className="landing-reciter-section landing-shell" id="reciters" aria-labelledby="reciters-title">
          <div className="landing-reciter-heading"><div><SectionKicker>أصوات نحب الاستماع إليها</SectionKicker><h2 id="reciters-title">من مكتبة القرّاء.</h2></div><p>تعرّف على بعض القرّاء المتاحين ضمن مكتبة أنصت، واستكشف التلاوات من داخل التطبيق.</p></div>
          <div className="landing-reciter-row">{featuredReciters.map((reciter) => <div className="landing-reciter" key={reciter.id}><Image className="landing-reciter-photo" src={reciter.image} alt={`صورة القارئ ${reciter.name}`} width={84} height={84} unoptimized /><strong>{reciter.name}</strong></div>)}<Link className="landing-reciter-more" href="/mushaf"><span>+</span><small>اكتشف المكتبة</small></Link></div>
        </section>

        <section className="landing-final-cta landing-shell" aria-labelledby="final-title">
          <div className="landing-final-pattern" aria-hidden="true">۞</div>
          <SectionKicker>شاركنا طريق النفع</SectionKicker>
          <h2 id="final-title">قد تكون بداية الخير،<br /><span>آيةٌ تصل إليها.</span></h2>
          <p>جرّب أنصت، وشارك المبادرة مع من تحب؛ لعلها تكون سببًا في نفعٍ يمتد.</p>
          <Link className="landing-button landing-button-primary" href="/listen"><MicIcon size={20} />ابدأ الاستماع الآن<ArrowIcon /></Link>
          <small>الميكروفون لا يعمل إلا بعد اختيارك بدء الاستماع.</small>
        </section>
      </main>

      <footer className="landing-footer landing-shell">
        <Link className="landing-brand" href="/" aria-label="أنصت — الرئيسية"><BrandMark /><span className="landing-brand-copy"><strong>أنصِت</strong><small>التقنية في خدمة القرآن</small></span></Link>
        <p>مبادرة خيرية تسعى لخدمة القرآن الكريم والسنة النبوية.<br /><span className="landing-credit">تم التصميم والبرمجة والتدريب بواسطة م. أحمد سامي التحيوي</span></p>
        <div><Link href="/mushaf">افتح التطبيق</Link><Link href="/settings">الإعدادات</Link></div>
      </footer>
    </div>
  );
}
