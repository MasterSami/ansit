/** Small building blocks shared by the screens. */

import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

import { initials } from "@/lib/text";

const ICON_BUTTON =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text";

/** 44 px round icon button. Always needs a label, since it has no text. */
export function IconButton({
  label,
  className = "",
  ...rest
}: ComponentProps<"button"> & { label: string }) {
  return (
    <button
      type="button"
      aria-label={label}
      className={`${ICON_BUTTON} ${className}`}
      {...rest}
    />
  );
}

export function IconLink({
  label,
  className = "",
  ...rest
}: ComponentProps<typeof Link> & { label: string }) {
  return (
    <Link
      aria-label={label}
      className={`${ICON_BUTTON} ${className}`}
      {...rest}
    />
  );
}

const PRIMARY =
  "flex h-[54px] w-full items-center justify-center gap-2.5 rounded-full bg-accent text-base font-bold text-on-accent disabled:opacity-60";

export function PrimaryButton({
  className = "",
  ...rest
}: ComponentProps<"button">) {
  return (
    <button type="button" className={`${PRIMARY} ${className}`} {...rest} />
  );
}

export function PrimaryLink({
  className = "",
  ...rest
}: ComponentProps<typeof Link>) {
  return <Link className={`${PRIMARY} ${className}`} {...rest} />;
}

const QUIET =
  "flex h-12 w-full items-center justify-center gap-2 rounded-full text-[15px]";

export function QuietButton({
  tone = "muted",
  className = "",
  ...rest
}: ComponentProps<"button"> & { tone?: "muted" | "accent" }) {
  const colour =
    tone === "accent" ? "font-semibold text-accent" : "font-medium text-muted";
  return (
    <button
      type="button"
      className={`${QUIET} ${colour} ${className}`}
      {...rest}
    />
  );
}

export function QuietLink({
  className = "",
  ...rest
}: ComponentProps<typeof Link>) {
  return (
    <Link
      className={`${QUIET} font-medium text-muted ${className}`}
      {...rest}
    />
  );
}

/** Initials avatar: reciters are never shown with photos. */
export function Avatar({
  name,
  size,
}: {
  name: string;
  size: "sm" | "md" | "lg";
}) {
  const box = {
    sm: "h-10 w-10 text-sm border-transparent bg-divider",
    md: "h-[52px] w-[52px] text-[17px] bg-divider border-[rgb(var(--accent-rgb)/0.4)]",
    lg: "h-24 w-24 text-3xl border-2 border-accent bg-surface",
  }[size];
  return (
    <div
      aria-hidden="true"
      className={`flex shrink-0 items-center justify-center rounded-full border font-bold text-accent ${box}`}
    >
      {initials(name)}
    </div>
  );
}

/** The app frame: a phone-width column, full height. */
export function Screen({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`mx-auto flex min-h-dvh w-full max-w-[430px] flex-col bg-bg ${className}`}
    >
      {children}
    </div>
  );
}

export function Card({
  children,
  className = "",
  ...rest
}: ComponentProps<"section">) {
  return (
    <section
      className={`rounded-3xl border border-border bg-surface ${className}`}
      {...rest}
    >
      {children}
    </section>
  );
}

/** Placeholder block shown while local data loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={`ansit-skeleton rounded-2xl ${className}`}
    />
  );
}

/** A calm full-screen message with an icon, for empty and error states. */
export function StateMessage({
  icon,
  title,
  body,
  tone = "neutral",
  children,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  tone?: "neutral" | "warning";
  children?: ReactNode;
}) {
  const badge =
    tone === "warning"
      ? "bg-warning-bg text-warning"
      : "bg-accent-soft text-accent";
  return (
    <div
      className="flex grow flex-col items-center justify-center gap-6 px-6 text-center"
      role="status"
    >
      <div
        className={`flex h-24 w-24 items-center justify-center rounded-full ${badge}`}
      >
        {icon}
      </div>
      <div className="flex max-w-[300px] flex-col gap-2">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-[15px] leading-[1.8] text-muted">{body}</p>
      </div>
      {children}
    </div>
  );
}
