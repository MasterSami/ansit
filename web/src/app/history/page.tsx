import { Suspense } from "react";

import { HistoryScreen } from "@/components/HistoryScreen";

export default function Page() {
  // Reads query parameters, which are only known in the browser.
  return (
    <Suspense>
      <HistoryScreen />
    </Suspense>
  );
}
