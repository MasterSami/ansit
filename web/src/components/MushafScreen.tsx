"use client";

import { useTranslations } from "next-intl";

import { BottomNav } from "./BottomNav";
import { BookIcon } from "./icons";
import { PlayerBar } from "./PlayerBar";
import { Screen, StateMessage } from "./ui";

/** The full mushaf reader is out of scope for v1. */
export function MushafScreen() {
  const t = useTranslations();
  return (
    <Screen>
      <StateMessage
        icon={<BookIcon size={40} />}
        title={`${t("mushaf.title")} · ${t("common.soon")}`}
        body={t("mushaf.body")}
      />
      <PlayerBar />
      <BottomNav current="mushaf" />
    </Screen>
  );
}
