import { Suspense } from "react";

import { ListenScreen } from "@/components/ListenScreen";

export default function ListenPage() {
  // The screen reads ?prev= ("listen longer"), which is only known in the browser.
  return (
    <Suspense>
      <ListenScreen />
    </Suspense>
  );
}
