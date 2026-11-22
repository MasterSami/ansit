"use client";

import Image from "next/image";
import { useState } from "react";

import { BookIcon } from "./icons";

/**
 * A reciter's portrait in a round frame. With no image, or when the image
 * fails to load, the frame shows a neutral book mark: the layout never
 * depends on a third-party picture arriving.
 */
export function Portrait({
  src,
  size,
  priority = false,
  className = "",
}: {
  /** Kept for callers; the portrait itself is decorative. */
  name?: string;
  src?: string;
  /** Rendered diameter in px. */
  size: number;
  priority?: boolean;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <span
      className={`portrait ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    >
      {src && !failed ? (
        <Image
          src={src}
          alt=""
          fill
          sizes={`${size}px`}
          unoptimized
          priority={priority}
          onError={() => setFailed(true)}
        />
      ) : (
        <BookIcon size={Math.round(size * 0.34)} />
      )}
    </span>
  );
}
