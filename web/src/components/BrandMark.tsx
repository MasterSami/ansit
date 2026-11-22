/**
 * The ANSIT mark: an eight-pointed star (two squares, as in manuscript
 * illumination) holding three bars of sound.
 */
export function BrandMark({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
    >
      <rect
        x="9"
        y="9"
        width="30"
        height="30"
        stroke="currentColor"
        strokeWidth="2"
      />
      <rect
        x="9"
        y="9"
        width="30"
        height="30"
        stroke="currentColor"
        strokeWidth="2"
        transform="rotate(45 24 24)"
      />
      <path
        d="M18 21v6M24 17v14M30 21v6"
        stroke="var(--rubric, currentColor)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function Wordmark({ tagline }: { tagline?: string }) {
  return (
    <span className="brand">
      <span className="brand-mark">
        <BrandMark />
      </span>
      <span className="brand-text">
        <strong>أنصِت</strong>
        {tagline && <small>{tagline}</small>}
      </span>
    </span>
  );
}
