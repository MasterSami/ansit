"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import { BookIcon, BookmarkIcon, HistoryIcon, MicIcon } from "./icons";

export type Tab = "listen" | "history" | "saved" | "mushaf";

const TABS = [
  { id: "listen", href: "/", Icon: MicIcon },
  { id: "history", href: "/history", Icon: HistoryIcon },
  { id: "saved", href: "/history?filter=saved", Icon: BookmarkIcon },
  { id: "mushaf", href: "/mushaf", Icon: BookIcon },
] as const;

export function BottomNav({ current }: { current: Tab }) {
  const t = useTranslations("nav");
  return (
    <nav
      aria-label={t("label")}
      className="sticky bottom-0 grid grid-cols-4 border-t border-nav-border bg-nav-bg px-2 pt-2.5 pb-[max(1rem,env(safe-area-inset-bottom))]"
    >
      {TABS.map(({ id, href, Icon }) => {
        const active = id === current;
        return (
          <Link
            key={id}
            href={href}
            aria-current={active ? "page" : undefined}
            className={`flex min-h-11 flex-col items-center gap-1 py-1.5 text-xs ${
              active ? "font-semibold text-accent" : "font-medium text-muted"
            }`}
          >
            <Icon size={22} />
            {t(id)}
          </Link>
        );
      })}
    </nav>
  );
}
