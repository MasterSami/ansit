import Link from "next/link";

import { Wordmark } from "@/components/BrandMark";

export default function NotFound() {
  return (
    <main className="offline">
      <div>
        <Wordmark />
        <h1>الصفحة غير موجودة</h1>
        <p>ربما تغيّر العنوان، أو أن القارئ ليس في المكتبة بعد.</p>
        <div className="offline-actions">
          <Link className="btn btn-primary" href="/">
            الرئيسية
          </Link>
          <Link className="btn btn-outline" href="/reciters">
            مكتبة القرّاء
          </Link>
        </div>
      </div>
    </main>
  );
}
