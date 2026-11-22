"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Wordmark } from "./BrandMark";
import { SettingsIcon } from "./icons";
import { InstallButton } from "./InstallPrompt";

const LINKS = [
  { href: "/listen", label: "الإنصات", match: ["/listen", "/result"] },
  { href: "/reciters", label: "القرّاء", match: ["/reciters", "/reciter"] },
  { href: "/mushaf", label: "المصحف", match: ["/mushaf"] },
  { href: "/history", label: "السجل", match: ["/history"] },
];

/** Top navigation. On phones the app screens use the bottom bar instead. */
export function SiteHeader({ always = false }: { always?: boolean }) {
  const pathname = usePathname();
  return (
    <header className={`site-header${always ? " site-header-always" : ""}`}>
      <div className="site-header-inner">
        <Link href="/" aria-label="أنصِت — الرئيسية">
          <Wordmark tagline="من الصوت إلى الآية" />
        </Link>
        <nav className="site-nav" aria-label="التنقل الرئيسي">
          {LINKS.map((link) => {
            const active = link.match.some(
              (prefix) =>
                pathname === prefix || pathname.startsWith(`${prefix}/`),
            );
            return (
              <Link
                key={link.href}
                href={link.href}
                aria-current={active ? "page" : undefined}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
        <div className="site-header-actions">
          <InstallButton />
          <Link
            href="/settings"
            className="site-icon-link"
            aria-label="الإعدادات"
          >
            <SettingsIcon size={19} />
          </Link>
        </div>
      </div>
    </header>
  );
}
