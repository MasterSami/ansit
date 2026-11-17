import { Suspense } from "react";

import { ReciterScreen } from "@/components/ReciterScreen";

export default function Page() {
  // Reads query parameters, which are only known in the browser.
  return (
    <Suspense>
      <ReciterScreen />
    </Suspense>
  );
}
