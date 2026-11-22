"use client";

/** Small building blocks shared by the screens. */

import Link from "next/link";
import Image from "next/image";
import { useState, type ComponentProps, type ReactNode } from "react";

import { BookIcon } from "./icons";
import { SiteHeader } from "./SiteHeader";

const ICON_BUTTON =
  "flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-border bg-surface text-text hover:border-text";

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
  "flex h-[52px] w-full items-center justify-center gap-2.5 rounded-lg bg-accent text-base font-semibold text-on-accent hover:opacity-90 disabled:opacity-50";

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
  "flex h-12 w-full items-center justify-center gap-2 rounded-lg text-[15px] hover:bg-surface-2 disabled:opacity-50 disabled:hover:bg-transparent";

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

/** A reciter portrait with a neutral book mark when no verified image exists. */
export function Avatar({
  name,
  size,
  image,
}: {
  name: string;
  size: "sm" | "md" | "lg";
  image?: string;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const box = {
    sm: "h-10 w-10 text-sm border-transparent bg-divider",
    md: "h-[52px] w-[52px] text-[17px] bg-divider border-[rgb(var(--accent-rgb)/0.4)]",
    lg: "h-24 w-24 text-3xl border-2 border-accent bg-surface",
  }[size];
  const imageSize = size === "lg" ? 96 : size === "md" ? 52 : 40;
  return (
    <div
      aria-hidden="true"
      className={`relative flex shrink-0 items-center justify-center overflow-hidden rounded-lg border text-accent ${box}`}
      title={name}
    >
      {image && !imageFailed ? (
        <Image
          src={image}
          alt=""
          fill
          sizes={`${imageSize}px`}
          unoptimized
          className="object-cover"
          onError={() => setImageFailed(true)}
        />
      ) : (
        <BookIcon size={size === "lg" ? 32 : size === "md" ? 22 : 18} />
      )}
    </div>
  );
}

/**
 * The app frame. On a wide screen it sits under the site navigation and uses
 * a readable column (or the full shell when `wide`); on a phone it is the
 * whole screen, with the bottom bar the page provides.
 */
export function Screen({
  children,
  className = "",
  wide = false,
}: {
  children: ReactNode;
  className?: string;
  wide?: boolean;
}) {
  return (
    <div className="flex min-h-dvh flex-col bg-bg">
      <SiteHeader />
      <div
        className={`mx-auto flex w-full grow flex-col ${
          wide
            ? "max-w-[430px] md:max-w-[min(1120px,calc(100%-80px))]"
            : "max-w-[430px] md:max-w-[680px]"
        } ${className}`}
      >
        {children}
      </div>
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
      className={`rounded-xl border border-border bg-surface ${className}`}
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
      className={`ansit-skeleton rounded-lg ${className}`}
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
