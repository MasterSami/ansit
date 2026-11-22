"use client";

import Image from "next/image";
import { useState } from "react";

import { initials } from "@/lib/text";

/**
 * A reciter's portrait in a squared frame. With no image, or when the image
 * fails to load, the frame shows the reciter's initials instead: the layout
 * never depends on a third-party picture arriving.
 */
export function Portrait({
  name,
  src,
  size,
  priority = false,
  className = "",
}: {
  name: string;
  src?: string;
  /** Rendered width in px; the frame is 4:5. */
  size: number;
  priority?: boolean;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  return (
    <span
      className={`portrait ${className}`}
      style={{ width: size, fontSize: Math.round(size * 0.3) }}
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
        <span className="portrait-initials">{initials(name)}</span>
      )}
    </span>
  );
}
