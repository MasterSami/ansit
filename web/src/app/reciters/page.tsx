import type { Metadata } from "next";

import { ReciterLibraryScreen } from "@/components/ReciterLibraryScreen";

export const metadata: Metadata = {
  title: "مكتبة القرّاء",
  description:
    "قرّاء من مصر والحرمين الشريفين والعالم: سيرة موثّقة لكل قارئ وما يتوفر من تلاواته.",
};

export default function RecitersPage() {
  return <ReciterLibraryScreen />;
}
