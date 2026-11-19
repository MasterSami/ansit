/** Curated library additions. Audio URLs below were checked against MP3Quran's
 * public reciter API; records without audio stay visible as directory entries. */
export interface CuratedReciter {
  id: string;
  name_ar: string;
  name_en: string;
  image?: string;
  imageCredit?: string;
  sourceUrl: string;
  audioUrl?: string;
}

const mp3 = (server: string, surah = 1) =>
  `${server}${String(surah).padStart(3, "0")}.mp3`;

export const RECITER_IMAGES: Record<string, string> = {
  minshawi:
    "https://commons.wikimedia.org/wiki/Special:FilePath/Elminshwey.jpg",
  "abdul-basit":
    "https://commons.wikimedia.org/wiki/Special:FilePath/Abdel_Basit_Abdel_Samad_1955.png",
  sudais:
    "https://quranmedia.online/images/reciters/abdul-rahman-al-sudais/image/180x180.jpg.webp",
  alafasy:
    "https://quranmedia.online/images/reciters/mishary-rashid-alafasy/image/180x180.jpg.webp",
  muaiqly:
    "https://quranmedia.online/images/reciters/maher-al-muaiqly/image/180x180.jpg.webp",
  shuraim:
    "https://quranmedia.online/images/reciters/saud-al-shuraim/image/180x180.jpg.webp",
  neana:
    "https://quranmedia.online/images/reciters/ahmed-naina/image/180x180.jpg.webp",
  "yasser-dosari":
    "https://storage.googleapis.com/way2quran_storage/imgs/yasser-al-dosary.jpg",
  husary:
    "https://www.alkhaleej.ae/sites/default/files/styles/d08_standard/public/2025-11/7450307.jpeg?h=89897146&itok=zycwzxAd",
  banna:
    "https://gate.ahram.org.eg/Media/News/2025/7/20/2025-638886459547910043-791.jpeg",
  tablawi: "https://www.mwatan.news/Upload/libfiles/37/7/204.jpg",
  budair: "https://ar.islamway.net/uploads/authors/salah-al-budair.jpg",
  "hussain-sheikh":
    "https://www.al-madina.com/uploads/images/2025/12/05/2506745.jpg",
  "mustafa-ismail":
    "https://way2quran.com/_next/image?q=75&url=https%3A%2F%2Fstorage.googleapis.com%2Fway2quran_storage%2Fimgs%2Fmustafa-ismail.jpg&w=640",
  "muhammad-refaat":
    "https://www.aljazeera.net/wp-content/uploads/2019/05/48ab1b53-44a4-4f3d-ad57-6d94b77e801d.jpeg?quality=80&resize=730%2C410",
  "kamal-yusuf-al-bahtimi":
    "https://commons.wikimedia.org/wiki/Special:FilePath/Kamil_Yusuf_Al-Bahtimi.jpg?width=320",
  "shahat-anwar":
    "https://awkafonline.gov.eg/web/image/blog.post/11088/image_content_thumbnail",
  "abu-al-enein-shuaisha":
    "https://watanimg.elwatannews.com/image_archive/original_lower_quality/16943890151660318924.jpg",
  "ragheb-ghalwash":
    "https://gate.ahram.org.eg/Media/News/2024/7/5/2024-638557711777264726-726.jpg",
  "taha-al-fashni":
    "https://i1.sndcdn.com/artworks-XKkmWVcKKfglF1Y6-BpZ7QQ-t500x500.jpg",
  "badr-al-turki": "https://media.way2quran.com/imgs/badr-al-turki.jpg",
  "waleed-shamsan": "https://img.youtube.com/vi/mdZLoXQ1nc4/maxresdefault.jpg",
  "bandar-baleela":
    "https://i1.sndcdn.com/artworks-QLbSbMcexsj0i22x-l1p2DQ-t500x500.jpg",
  "salah-budair": "https://ar.islamway.net/uploads/authors/salah-al-budair.jpg",
  "abdullah-buaijan":
    "https://al-hadath.com/storage/post/media/2021/Dec/3cfc85a6b1ff0c35ad1cbc4ab5294146.jpg",
  "abdulbari-thubaiti":
    "https://www.okaz.com.sa/uploads/images/2024/04/08/2374548.jpg",
  "khalid-muhanna":
    "https://saudipedia.com/saudipedia/uploads/images/2025/01/09/172084.jpg",
  "saleh-al-maghamsi":
    "https://www.okaz.com.sa/okaz/uploads/images/2026/03/15/2677284.webp",
  "muhammad-burhaji":
    "https://media.gemini.media/img/large/2024/10/9/2024_10_9_21_38_45_940.jpg",
  "faisal-ghazzawi": "https://pbs.twimg.com/media/Gu5hgvPWkAEtcH2.jpg",
  "osama-khayyat":
    "https://www.arabnews.com/sites/default/files/styles/n_670_395/public/2022/04/17/3180391-1917980588.png?itok=r3S2LYeI",
};

export const RECITER_IMAGE_SOURCES: Record<
  string,
  { credit: string; url: string }
> = {
  minshawi: {
    credit: "Wikimedia Commons",
    url: "https://commons.wikimedia.org/wiki/File:Elminshwey.jpg",
  },
  "abdul-basit": {
    credit: "Wikimedia Commons",
    url: "https://commons.wikimedia.org/wiki/File:Abdel_Basit_Abdel_Samad_1955.png",
  },
  sudais: { credit: "QuranMedia", url: "https://quranmedia.online" },
  alafasy: { credit: "QuranMedia", url: "https://quranmedia.online" },
  muaiqly: { credit: "QuranMedia", url: "https://quranmedia.online" },
  shuraim: { credit: "QuranMedia", url: "https://quranmedia.online" },
  neana: { credit: "QuranMedia", url: "https://quranmedia.online" },
  "yasser-dosari": { credit: "Way2Quran", url: "https://www.way2quran.com" },
  husary: {
    credit: "الخليج",
    url: "https://www.alkhaleej.ae/2025-11-25/مصر-تحيي-ذكرى-رحيل-الشيخ-الحصري-بتلاواته-النادرة-6193311/محطات/منوعات",
  },
  banna: {
    credit: "بوابة الأهرام",
    url: "https://gate.ahram.org.eg/News/5250832.aspx",
  },
  tablawi: {
    credit: "مواطن",
    url: "https://www.mwatan.news/860523",
  },
  budair: {
    credit: "طريق الإسلام",
    url: "https://ar.islamway.net/scholar/785/صالح-بن-محمد-البدير",
  },
};

export const CURATED_RECITERS: CuratedReciter[] = [
  {
    id: "kamal-yusuf-al-bahtimi",
    name_ar: "كامل يوسف البهتيمي",
    name_en: "Kamil Yusuf Al-Bahtimi",
    image: RECITER_IMAGES["kamal-yusuf-al-bahtimi"],
    imageCredit: "Wikimedia Commons",
    sourceUrl:
      "https://commons.wikimedia.org/wiki/File:Kamil_Yusuf_Al-Bahtimi.jpg",
    audioUrl: "https://soundcloud.com/way2quran/i3fp7udtcegu",
  },
  {
    id: "shahat-anwar",
    name_ar: "الشحات محمد أنور",
    name_en: "Al-Shahat Muhammad Anwar",
    image: RECITER_IMAGES["shahat-anwar"],
    imageCredit: "وزارة الأوقاف المصرية",
    sourceUrl:
      "https://awkafonline.gov.eg/content-sections/131/11088/أمير-النغم-القرآني-الشيخ-الشحات-محمد-أنور",
    audioUrl: "https://soundcloud.com/shahatanour",
  },
  {
    id: "muhammad-refaat",
    name_ar: "محمد رفعت",
    name_en: "Muhammad Refaat",
    image: RECITER_IMAGES["muhammad-refaat"],
    imageCredit: "الجزيرة",
    sourceUrl: "https://www.aljazeera.net/culture/2021/4/18/الشيخ-محمد-رفعت",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/muhammad-refaat/r1/"),
  },
  {
    id: "mustafa-ismail",
    name_ar: "مصطفى إسماعيل",
    name_en: "Mustafa Ismail",
    image: RECITER_IMAGES["mustafa-ismail"],
    imageCredit: "Way2Quran",
    sourceUrl: "https://way2quran.com/en/reciters/mustafa-ismail",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/mustafa-ismail/r2/"),
  },
  {
    id: "abu-al-enein-shuaisha",
    name_ar: "أبو العينين شعيشع",
    name_en: "Abu Al-Enein Shuaisha",
    image: RECITER_IMAGES["abu-al-enein-shuaisha"],
    imageCredit: "الوطن",
    sourceUrl: "https://www.elwatannews.com/news/details/6246070",
  },
  {
    id: "ragheb-ghalwash",
    name_ar: "راغب مصطفى غلوش",
    name_en: "Ragheb Mustafa Ghalwash",
    image: RECITER_IMAGES["ragheb-ghalwash"],
    imageCredit: "بوابة الأهرام",
    sourceUrl: "https://gate.ahram.org.eg/News/4358314.aspx",
  },
  {
    id: "taha-al-fashni",
    name_ar: "طه الفشني",
    name_en: "Taha Al-Fashni",
    image: RECITER_IMAGES["taha-al-fashni"],
    imageCredit: "SoundCloud",
    sourceUrl: "https://soundcloud.com/passer_by_or_aber_sabil/hodpevdkya5d",
  },
  {
    id: "saleh-bin-humayd",
    name_ar: "صالح بن عبدالله بن حميد",
    name_en: "Saleh bin Humaid",
    sourceUrl:
      "https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226",
  },
  {
    id: "osama-khayyat",
    name_ar: "أسامة بن عبدالله خياط",
    name_en: "Osama Khayyat",
    image: RECITER_IMAGES["osama-khayyat"],
    imageCredit: "Arab News",
    sourceUrl: "https://www.arabnews.com/node/2064611/saudi-arabia",
  },
  {
    id: "faisal-ghazzawi",
    name_ar: "فيصل بن جميل غزاوي",
    name_en: "Faisal Ghazzawi",
    image: RECITER_IMAGES["faisal-ghazzawi"],
    imageCredit: "X: @alla1402",
    sourceUrl: "https://x.com/alla1402/status/1940595710908670259",
  },
  {
    id: "badr-al-turki",
    name_ar: "بدر بن محمد التركي",
    name_en: "Badr Al-Turki",
    image: RECITER_IMAGES["badr-al-turki"],
    imageCredit: "Way2Quran",
    sourceUrl: "https://www.way2quran.com/en/reciters/badr-al-turki",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/badr-turki/r1/"),
  },
  {
    id: "waleed-shamsan",
    name_ar: "الوليد بن خالد الشمسان",
    name_en: "Al-Waleed Al-Shamsan",
    image: RECITER_IMAGES["waleed-shamsan"],
    imageCredit: "YouTube",
    sourceUrl: "https://www.youtube.com/watch?v=mdZLoXQ1nc4",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/waleed-shamsan/r1/"),
  },
  {
    id: "bandar-baleela",
    name_ar: "بندر بن عبدالعزيز بليلة",
    name_en: "Bandar Balilah",
    image: RECITER_IMAGES["bandar-baleela"],
    imageCredit: "SoundCloud",
    sourceUrl: "https://soundcloud.com/pqrzi3wbpqko/sets/1441-1-a0",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/bandar-baleela/r1/"),
  },
  {
    id: "abdullah-buaijan",
    name_ar: "عبدالله بن عبدالرحمن البعيجان",
    name_en: "Abdullah Al-Buaijan",
    image: RECITER_IMAGES["abdullah-buaijan"],
    imageCredit: "الحدث",
    sourceUrl: "https://al-hadath.com/post/19068",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/abdullah-buaijan/r1/"),
  },
  {
    id: "hussain-sheikh",
    name_ar: "حسين آل الشيخ",
    name_en: "Hussain Al-Sheikh",
    image: RECITER_IMAGES["hussain-sheikh"],
    imageCredit: "جريدة المدينة",
    sourceUrl:
      "https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/hussain-sheikh/r1/", 2),
  },
  {
    id: "ali-hudhaifi",
    name_ar: "علي بن عبدالرحمن الحذيفي",
    name_en: "Ali Al-Hudhaifi",
    sourceUrl: "https://www.mp3quran.net/ar/reciters",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/ali-hudhaifi/r3/"),
  },
  {
    id: "abdulbari-thubaiti",
    name_ar: "عبدالبارئ بن عوض الثبيتي",
    name_en: "Abdulbari Al-Thubaiti",
    image: RECITER_IMAGES["abdulbari-thubaiti"],
    imageCredit: "عكاظ",
    sourceUrl: "https://www.okaz.com.sa/news/local/2159137",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/abdulbari-thubaiti/r1/"),
  },
  {
    id: "abdulmohsen-qasim",
    name_ar: "عبدالمحسن بن محمد القاسم",
    name_en: "Abdulmohsen Al-Qasim",
    sourceUrl:
      "https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/abdulmohsen-qasim/r1/"),
  },
  {
    id: "khalid-muhanna",
    name_ar: "خالد بن سليمان المهنا",
    name_en: "Khalid Al-Muhanna",
    image: RECITER_IMAGES["khalid-muhanna"],
    imageCredit: "سعوديبيديا",
    sourceUrl:
      "https://saudipedia.com/article/16219/شخصيات/شخصيات-دينية/خالد-المهنا",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/khalid-mohanna/r1/"),
  },
  {
    id: "ahmad-hudhaifi",
    name_ar: "أحمد بن علي الحذيفي",
    name_en: "Ahmad Al-Hudhaifi",
    sourceUrl:
      "https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/ahmad-hudhaifi/r1/"),
  },
  {
    id: "muhammad-burhaji",
    name_ar: "محمد برهجي",
    name_en: "Muhammad Burhaji",
    image: RECITER_IMAGES["muhammad-burhaji"],
    imageCredit: "مصراوي",
    sourceUrl:
      "https://www.masrawy.com/islameyat/others-islamic_ppl_news/details/2024/10/9/2655752",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/muhammad-burhaji/r1/"),
  },
  {
    id: "abdullah-qarafi",
    name_ar: "عبدالله بن عبدالمحسن القرافي",
    name_en: "Abdullah Al-Qarafi",
    sourceUrl:
      "https://prh.gov.sa/ar/component/content/article?Itemid=440&id=226",
    audioUrl: mp3("https://cdn.mp3quran.net/audio/abdullah-qarafi/r1/"),
  },
  {
    id: "saleh-al-maghamsi",
    name_ar: "صالح المغامسي",
    name_en: "Saleh Al-Maghamsi",
    image: RECITER_IMAGES["saleh-al-maghamsi"],
    imageCredit: "عكاظ",
    sourceUrl: "https://www.okaz.com.sa/local/na/2240104",
  },
];
