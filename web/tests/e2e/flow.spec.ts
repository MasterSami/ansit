import { expect, type Page, type Route } from "@playwright/test";
import { test } from "@playwright/test";

// The API is mocked. Ayah text here is a placeholder, never real Quran text:
// in the app it always comes from the server.
const PLACEHOLDER = "نص تجريبي للاختبار";

const AYAH = {
  surah: 67,
  surah_name_ar: "الملك",
  surah_name_en: "Al-Mulk",
  ayah: 1,
  text_uthmani: PLACEHOLDER,
  juz: 29,
  page: 562,
  revelation: "meccan",
  ayah_count: 30,
};

const RECITER = {
  status: "identified",
  id: "alafasy",
  name_ar: "مشاري العفاسي",
  name_en: "Mishary Alafasy",
  style: "murattal",
  similarity: 0.82,
  alternatives: [],
};

const MATCH = {
  id: "11111111-1111-4111-8111-111111111111",
  status: "match",
  reason: null,
  ayah: AYAH,
  text_confidence: 0.96,
  candidates: [],
  repeated_count: null,
  reciter: RECITER,
};

const AMBIGUOUS = {
  ...MATCH,
  id: "22222222-2222-4222-8222-222222222222",
  status: "ambiguous",
  ayah: {
    ...AYAH,
    surah: 55,
    surah_name_ar: "الرحمن",
    surah_name_en: "Ar-Rahman",
    ayah: 13,
  },
  candidates: [
    {
      surah: 55,
      surah_name_ar: "الرحمن",
      ayah: 13,
      score: 0.97,
      context_before: PLACEHOLDER,
    },
    {
      surah: 55,
      surah_name_ar: "الرحمن",
      ayah: 16,
      score: 0.97,
      context_before: PLACEHOLDER,
    },
  ],
  repeated_count: 31,
  reciter: {
    ...RECITER,
    status: "unknown",
    id: null,
    name_ar: null,
    name_en: null,
  },
};

interface Mock {
  identify: object | number;
  identifyBodies: string[];
  feedback: unknown[];
}

test("serves browser security headers", async ({ page }) => {
  const response = await page.goto("/");
  const headers = await response?.allHeaders();
  expect(headers?.["x-content-type-options"]).toBe("nosniff");
  expect(headers?.["x-frame-options"]).toBe("DENY");
  expect(headers?.["referrer-policy"]).toBe("strict-origin-when-cross-origin");
  expect(headers?.["permissions-policy"]).toContain("microphone=(self)");
});

async function mockApi(page: Page, identify: object | number): Promise<Mock> {
  const mock: Mock = { identify, identifyBodies: [], feedback: [] };
  const json = (route: Route, body: unknown, status = 200) =>
    route.fulfill({
      status,
      contentType: "application/json",
      headers: { "access-control-allow-origin": "*" },
      body: JSON.stringify(body),
    });
  await page.route("**/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() === "OPTIONS") {
      return route.fulfill({
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-headers": "*",
          "access-control-allow-methods": "*",
        },
      });
    }
    if (path === "/v1/identify") {
      mock.identifyBodies.push(request.postData() ?? "");
      if (typeof mock.identify === "number") {
        return json(
          route,
          { error: { code: "x", message: "x" } },
          mock.identify,
        );
      }
      return json(route, mock.identify);
    }
    if (path === "/v1/surahs") {
      return json(route, {
        surahs: [
          {
            number: 55,
            name_ar: "الرحمن",
            name_en: "Ar-Rahman",
            ayah_count: 78,
            revelation: "medinan",
          },
          {
            number: 67,
            name_ar: "الملك",
            name_en: "Al-Mulk",
            ayah_count: 30,
            revelation: "meccan",
          },
        ],
      });
    }
    if (path.startsWith("/v1/ayahs/")) {
      const [, , , surah, ayah] = path.split("/");
      const selectedSurah = Number(surah);
      const selectedAyah = Number(ayah);
      return json(route, {
        ayah: {
          ...AMBIGUOUS.ayah,
          surah: selectedSurah,
          surah_name_ar: selectedSurah === 67 ? "الملك" : "الرحمن",
          ayah: selectedAyah,
        },
        context: [],
      });
    }
    if (path.startsWith("/v1/tafsir/")) {
      const [, , , surah, ayah] = path.split("/");
      return json(route, {
        surah: Number(surah),
        ayah: Number(ayah),
        text: "شرح من المصدر للاختبار",
        source_key: "arabic_moyassar",
        book: "التفسير الميسر",
        author: "نخبة من العلماء",
        publisher: "مجمع الملك فهد لطباعة المصحف الشريف",
        version: "غير منشور من المصدر",
        source_url: "https://quranenc.com/ar/browse/arabic_moyassar/67/1",
        attribution: "المصدر QuranEnc.com",
      });
    }
    if (path === "/v1/reciters") {
      return json(route, {
        reciters: [
          {
            id: "alafasy",
            name_ar: "مشاري العفاسي",
            name_en: "Mishary Alafasy",
            country: null,
            styles: ["murattal"],
          },
        ],
      });
    }
    if (path === "/v1/feedback") {
      mock.feedback.push(request.postDataJSON());
      return json(route, { stored: true });
    }
    return json(route, { error: { code: "not_found", message: "x" } }, 404);
  });
  return mock;
}

/**
 * Home → record with the fake microphone → stop. Depending on the Chromium
 * build, the fake-UI flag reports the microphone as already granted (recording
 * starts at once) or as "ask" (our explainer shows first); both are handled.
 */
async function listen(page: Page) {
  await page.goto("/");
  await page.getByRole("link", { name: "جرّب التعرّف على التلاوة" }).click();
  const allow = page.getByRole("button", { name: "السماح بالمايكروفون" });
  const listening = page.getByText("جارٍ الإنصات…");
  const identifying = page.getByText("جارٍ التعرّف…");
  let granted = false;
  // Recording can start automatically when permission is already granted, or
  // finish quickly on a loaded CI worker. Accept every real post-capture state.
  await expect(async () => {
    if (!granted && (await allow.isVisible())) {
      await allow.click({ timeout: 1_000 });
      granted = true;
    }
    const active =
      (await listening.isVisible()) ||
      (await identifying.isVisible()) ||
      (await page.locator(".listen-web-problem").isVisible()) ||
      new URL(page.url()).pathname === "/result";
    expect(active).toBeTruthy();
  }).toPass({ timeout: 15_000 });

  // The server rejects clips under 3 s; stop after the minimum when the
  // recording is still active. A fast test/browser may already have finished.
  if (await listening.isVisible()) {
    await page.waitForTimeout(3_300);
    const stop = page.getByRole("button", { name: "إيقاف" });
    if (await stop.isVisible()) await stop.click();
  }
}

test("identifies a recitation and keeps it in the local history", async ({
  page,
}) => {
  const mock = await mockApi(page, MATCH);
  await listen(page);

  await expect(page).toHaveURL(/\/result\?id=1111/);
  await expect(page.getByRole("heading", { name: "سورة الملك" })).toBeVisible();
  await expect(page.getByText(PLACEHOLDER)).toBeVisible();
  await expect(
    page.getByRole("region", { name: "القارئ" }).getByText("مشاري العفاسي"),
  ).toBeVisible();
  await expect(page.getByText("٩٦٪")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "نص المصحف من مشروع تنزيل" }),
  ).toBeVisible();

  // An audio clip was uploaded, tagged as coming from the web client.
  expect(mock.identifyBodies).toHaveLength(1);
  expect(mock.identifyBodies[0]).toContain('name="audio"');
  expect(mock.identifyBodies[0]).toContain("web");

  // Save it, then find it again in the history and under "saved".
  await page.getByRole("button", { name: "حفظ" }).click();
  await expect(page.getByRole("button", { name: "محفوظة" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );

  await page.goto("/history");
  await expect(
    page.getByRole("link", { name: /سورة الملك · الآية ١/ }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "المحفوظة" }).click();
  await expect(page.getByRole("link", { name: /سورة الملك/ })).toBeVisible();
  await page.getByLabel("ابحث في السجل").fill("البقرة");
  await expect(page.getByText("لا نتائج")).toBeVisible();

  // Nothing but the result is stored in the browser: no audio, no transcript.
  const stored = await page.evaluate(
    () =>
      new Promise<string[]>((resolve, reject) => {
        const open = indexedDB.open("ansit");
        open.onerror = () => reject(open.error);
        open.onsuccess = () => {
          const all = open.result
            .transaction("history")
            .objectStore("history")
            .getAll();
          all.onsuccess = () => resolve(Object.keys(all.result[0]).sort());
        };
      }),
  );
  expect(stored).toEqual(
    [
      "ayah",
      "candidates",
      "createdAt",
      "id",
      "reciter",
      "repeatedCount",
      "saved",
      "status",
      "textConfidence",
    ].sort(),
  );
});

test("opens the identified ayah tafsir on demand", async ({ page }) => {
  await mockApi(page, MATCH);
  await page.goto("/");
  await page.evaluate(
    (response) =>
      new Promise<void>((resolve, reject) => {
        const open = indexedDB.open("ansit", 1);
        open.onerror = () => reject(open.error);
        open.onupgradeneeded = () => {
          open.result
            .createObjectStore("history", { keyPath: "id" })
            .createIndex("createdAt", "createdAt");
        };
        open.onsuccess = () => {
          const tx = open.result.transaction("history", "readwrite");
          tx.oncomplete = () => resolve();
          tx.onerror = () => reject(tx.error);
          tx.objectStore("history").put({
            id: response.id,
            createdAt: Date.now(),
            status: response.status,
            ayah: response.ayah,
            textConfidence: response.text_confidence,
            candidates: response.candidates,
            repeatedCount: response.repeated_count,
            reciter: response.reciter,
            saved: false,
          });
        };
      }),
    MATCH,
  );
  await page.goto(`/result?id=${MATCH.id}`);

  await page.getByRole("button", { name: "التفسير" }).click();
  await expect(page.getByText("شرح من المصدر للاختبار")).toBeVisible();
  await expect(page.getByText(/غير منشور من المصدر/)).toBeVisible();
});

test("opens a mushaf ayah and its tafsir", async ({ page }) => {
  await mockApi(page, MATCH);
  await page.goto("/mushaf");

  await page.getByLabel("السورة").selectOption("67");
  await page.getByLabel("الآية").fill("1");
  await page.getByRole("button", { name: "عرض الآية" }).click();
  await expect(
    page.getByRole("heading", { name: "سورة الملك · الآية ١" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "عرض التفسير" }).click();
  await expect(page.getByText("شرح من المصدر للاختبار")).toBeVisible();
});

test("shows one searchable reciter list with the requested additions", async ({
  page,
}) => {
  await mockApi(page, MATCH);
  await page.goto("/reciters");

  await expect(page.getByText("كامل يوسف البهتيمي")).toBeVisible();
  await expect(page.getByText("الشحات محمد أنور")).toBeVisible();
  await expect(page.getByText("بدر بن محمد التركي")).toBeVisible();
  await expect(page.getByText("الوليد بن خالد الشمسان")).toBeVisible();
  await expect(page.getByLabel("تصنيفات القراء")).toHaveCount(0);
  await expect(page.getByLabel("ابحث عن قارئ")).toBeVisible();
  await page.getByLabel("ابحث عن قارئ").fill("الشمسان");
  await expect(page.getByText("كامل يوسف البهتيمي")).toHaveCount(0);
  await expect(page.getByText("الوليد بن خالد الشمسان")).toBeVisible();

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/");
  const header = page.locator(".landing-header");
  await expect(header.getByRole("link", { name: /مكتبة القراء/ })).toHaveCount(
    1,
  );
  await expect(header.locator(".landing-nav-cta")).toHaveCount(1);
});

test("sends feedback about a wrong result", async ({ page }) => {
  const mock = await mockApi(page, MATCH);
  await listen(page);
  await page.getByRole("button", { name: "نتيجة خاطئة؟" }).click();
  await page.getByLabel(/رقم السورة/).fill("2");
  await page.getByLabel(/رقم الآية/).fill("255");
  await page.getByRole("button", { name: "إرسال" }).click();
  await expect(page.getByText("شكرًا، وصلتنا ملاحظتك")).toBeVisible();
  expect(mock.feedback).toEqual([
    {
      identify_id: MATCH.id,
      kind: "wrong_ayah",
      correct_surah: 2,
      correct_ayah: 255,
    },
  ]);
});

test("lets the user pick the place of a repeated ayah", async ({ page }) => {
  await mockApi(page, AMBIGUOUS);
  await listen(page);

  await expect(page.getByText("تتكرر ٣١ مرة")).toBeVisible();
  await expect(page.getByText("و٢٩ موضعًا آخر")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "أنصت ١٠ ثوانٍ إضافية" }),
  ).toHaveAttribute("href", `/listen?prev=${AMBIGUOUS.id}`);

  await page.getByRole("radio", { name: /الآية ١٦/ }).click();
  await page.getByRole("button", { name: "تأكيد الموضع المختار" }).click();
  await expect(page.getByText("الآية ١٦", { exact: true })).toBeVisible();
  await expect(page.getByText("قارئ غير معروف")).toBeVisible();
  await expect(page.getByRole("button", { name: "أضِف الاسم" })).toBeVisible();
});

test("explains a failed recognition and offers a retry", async ({ page }) => {
  await mockApi(page, {
    ...MATCH,
    status: "no_match",
    reason: "no_speech",
    ayah: null,
    reciter: null,
  });
  await listen(page);
  await expect(
    page.getByRole("heading", { name: "لم نسمع تلاوة" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "حاول مرة أخرى" }),
  ).toBeVisible();
});

test("shows a rate-limit message when the server says slow down", async ({
  page,
}) => {
  await mockApi(page, 429);
  await listen(page);
  await expect(page.getByRole("heading", { name: "تمهّل قليلًا" })).toBeVisible();
});

test("says so when the server cannot recognise reciters", async ({ page }) => {
  await mockApi(page, { ...MATCH, reciter: null });
  await listen(page);
  await expect(
    page.getByText("التعرّف على القارئ غير متاح حاليًا"),
  ).toBeVisible();
  await expect(page.getByText("لم نتأكد من صوت القارئ")).toHaveCount(0);
});

test("switches theme and remembers it", async ({ page }) => {
  await mockApi(page, MATCH);
  await page.goto("/settings");
  await page.getByRole("radio", { name: "فاتح" }).click();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("radio", { name: "فاتح" })).toHaveAttribute(
    "aria-checked",
    "true",
  );
});
