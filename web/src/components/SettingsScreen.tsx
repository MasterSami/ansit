"use client";

import { useTranslations } from "next-intl";
import { type ReactNode, useEffect, useState } from "react";

import { clearHistory } from "@/lib/history";
import { applyTheme, readTheme, type ThemeChoice } from "@/lib/theme";

import { BackIcon } from "./icons";
import { InstallRow } from "./InstallPrompt";
import { IconLink, Screen } from "./ui";

const THEMES: ThemeChoice[] = ["system", "dark", "light"];
const VERSION = process.env.NEXT_PUBLIC_APP_VERSION ?? "0.1.0";

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2.5">
      <h2 className="text-[13px] font-semibold text-muted">{title}</h2>
      <div className="flex flex-col gap-3 rounded-[20px] border border-border bg-surface p-4">
        {children}
      </div>
    </section>
  );
}

export function SettingsScreen() {
  const t = useTranslations();
  const [theme, setTheme] = useState<ThemeChoice>("system");
  const [clearing, setClearing] = useState<"idle" | "confirm" | "done">("idle");

  // The stored choice is only readable in the browser, after hydration.
  useEffect(() => queueMicrotask(() => setTheme(readTheme())), []);

  const choose = (choice: ThemeChoice) => {
    applyTheme(choice);
    setTheme(choice);
  };

  const clear = async () => {
    if (clearing !== "confirm") {
      setClearing("confirm");
      return;
    }
    await clearHistory().catch(() => undefined);
    setClearing("done");
  };

  const credit = "text-[13px] leading-[1.8] text-muted";
  const link = "text-accent underline underline-offset-4";

  return (
    <Screen>
      <header className="flex items-center gap-3 px-5 pt-[52px]">
        <IconLink href="/" label={t("common.back")}>
          <BackIcon />
        </IconLink>
        <h1 className="text-xl font-bold">{t("settings.title")}</h1>
      </header>

      <main className="flex grow flex-col gap-6 px-5 pt-6 pb-10">
        <Section title={t("settings.appearance")}>
          <div
            role="radiogroup"
            aria-label={t("settings.appearance")}
            className="grid grid-cols-3 gap-1.5 rounded-2xl bg-bg p-1"
          >
            {THEMES.map((choice) => (
              <button
                key={choice}
                type="button"
                role="radio"
                aria-checked={theme === choice}
                onClick={() => choose(choice)}
                className={`h-11 rounded-xl text-sm font-semibold ${
                  theme === choice ? "bg-accent text-on-accent" : "text-muted"
                }`}
              >
                {t(`settings.${choice}`)}
              </button>
            ))}
          </div>
        </Section>

        <Section title={t("settings.privacy")}>
          <ul className="flex list-disc flex-col gap-1.5 ps-5 text-sm leading-[1.8]">
            <li>{t("settings.privacyMic")}</li>
            <li>{t("settings.privacyClip")}</li>
            <li>{t("settings.privacyHistory")}</li>
          </ul>
        </Section>

        <Section title={t("settings.data")}>
          <button
            type="button"
            onClick={clear}
            disabled={clearing === "done"}
            className="flex min-h-11 items-center justify-between text-start text-[15px] font-semibold text-warning disabled:text-muted"
          >
            {clearing === "done"
              ? t("settings.cleared")
              : t("settings.clearHistory")}
            {clearing === "confirm" && (
              <span className="text-xs font-medium" role="status">
                {t("settings.clearConfirm")}
              </span>
            )}
          </button>
        </Section>

        <Section title={t("settings.install")}>
          <InstallRow />
        </Section>

        <Section title={t("settings.about")}>
          <p className={credit}>
            {t("settings.creditTanzil")}{" "}
            <a
              className={link}
              href="https://tanzil.net"
              target="_blank"
              rel="noreferrer"
            >
              tanzil.net
            </a>
          </p>
          <p className={credit}>
            {t("settings.creditWespeaker")}{" "}
            <a
              className={link}
              href="https://github.com/wenet-e2e/wespeaker"
              target="_blank"
              rel="noreferrer"
            >
              WeSpeaker
            </a>
          </p>
          <p className={credit}>{t("settings.creditAsr")}</p>
          <p className={credit}>
            {t("settings.creditAudio")}{" "}
            <a
              className={link}
              href="https://everyayah.com"
              target="_blank"
              rel="noreferrer"
            >
              everyayah.com
            </a>
          </p>
          <p className="text-xs text-muted" dir="ltr">
            {t("settings.version", { version: VERSION })}
          </p>
        </Section>
      </main>
    </Screen>
  );
}
