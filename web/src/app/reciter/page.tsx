import { Suspense } from "react";

import { LegacyReciterRedirect } from "@/components/LegacyReciterRedirect";

// The old address (/reciter?id=…) still works: it forwards to the profile.
export default function Page() {
  return (
    <Suspense>
      <LegacyReciterRedirect />
    </Suspense>
  );
}
