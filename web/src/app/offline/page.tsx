import type { Metadata } from "next";
import Link from "next/link";

import { CheckIcon, WifiOffIcon } from "@/components/icons";

export const metadata: Metadata = { title: "لا يوجد اتصال" };

/** Shown by the service worker when a page is requested with no connection. */
export default function OfflinePage() {
  return (
    <main className="offline">
      <div>
        <span className="feature-brand">أنصِت</span>
        <WifiOffIcon size={40} />
        <h1>لا يوجد اتصال بالإنترنت</h1>
        <p>
          التعرّف على التلاوة وتشغيل التلاوات يحتاجان اتصالًا. ما زال بإمكانك:
        </p>
        <ul>
          <li>
            <CheckIcon size={15} />
            تصفّح سجلّ ما تعرّفت عليه، فهو محفوظ على هذا الجهاز.
          </li>
          <li>
            <CheckIcon size={15} />
            فتح الصفحات التي زرتها من قبل، ومنها صفحات القرّاء.
          </li>
        </ul>
        <div className="offline-actions">
          <Link className="btn btn-primary" href="/history">
            افتح السجل
          </Link>
          <Link className="btn btn-outline" href="/reciters">
            مكتبة القرّاء
          </Link>
        </div>
      </div>
    </main>
  );
}
