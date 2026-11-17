import { Suspense } from "react";

import { ResultScreen } from "@/components/ResultScreen";

export default function Page() {
  // Reads query parameters, which are only known in the browser.
  return (
    <Suspense>
      <ResultScreen />
    </Suspense>
  );
}
