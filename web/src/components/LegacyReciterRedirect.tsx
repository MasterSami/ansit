"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export function LegacyReciterRedirect() {
  const router = useRouter();
  const params = useSearchParams();
  useEffect(() => {
    const id = params.get("id");
    const surah = params.get("surah");
    router.replace(
      id
        ? `/reciters/${encodeURIComponent(id)}${surah ? `?surah=${surah}` : ""}`
        : "/reciters",
    );
  }, [params, router]);
  return null;
}
