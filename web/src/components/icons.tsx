/** Thin-stroke line icons (1.8 px), matching the mockups. No emoji anywhere. */

import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & {
  size?: number;
  strokeWidth?: number;
};

function Line({
  size = 20,
  strokeWidth = 1.8,
  children,
  ...rest
}: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  );
}

export const MicIcon = (p: IconProps) => (
  <Line {...p}>
    <rect x="9" y="2" width="6" height="12" rx="3" />
    <path d="M5 10v1a7 7 0 0 0 14 0v-1" />
    <path d="M12 18v4" />
  </Line>
);

export const HistoryIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M3 12a9 9 0 1 0 3-6.7L3 8" />
    <path d="M3 3v5h5" />
    <path d="M12 7v5l4 2" />
  </Line>
);

export const BookmarkIcon = ({
  filled,
  ...p
}: IconProps & { filled?: boolean }) => (
  <Line {...p} fill={filled ? "currentColor" : "none"}>
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </Line>
);

export const BookIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z" />
    <path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z" />
  </Line>
);

export const SettingsIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </Line>
);

/** Points to the start of the line in RTL (visually to the right). */
export const BackIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M5 12h14" />
    <path d="M13 6l6 6-6 6" />
  </Line>
);

export const ShareIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <path d="M8.6 13.5l6.8 4" />
    <path d="M15.4 6.5l-6.8 4" />
  </Line>
);

export const HelpIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3" />
    <path d="M12 17h.01" />
  </Line>
);

export const SearchIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="11" cy="11" r="7" />
    <path d="M21 21l-4.3-4.3" />
  </Line>
);

export const RefreshIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
    <path d="M21 3v5h-5" />
  </Line>
);

export const CheckIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M20 6L9 17l-5-5" />
  </Line>
);

export const HeartIcon = ({
  filled,
  ...p
}: IconProps & { filled?: boolean }) => (
  <Line {...p} fill={filled ? "currentColor" : "none"}>
    <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21.2l7.8-7.7 1-1.1a5.5 5.5 0 0 0 0-7.8z" />
  </Line>
);

export const PauseCircleIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M10 9v6" />
    <path d="M14 9v6" />
  </Line>
);

export const ShieldIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" />
    <path d="M9 12l2 2 4-4" />
  </Line>
);

export const BroadcastIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M4 10a8 8 0 0 1 16 0" />
    <path d="M7.5 12.5a4.5 4.5 0 0 1 9 0" />
    <circle cx="12" cy="16" r="2" />
  </Line>
);

export const WifiOffIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M2 2l20 20" />
    <path d="M8.5 16.4a5 5 0 0 1 7 0" />
    <path d="M5 12.9a10 10 0 0 1 5.2-2.7" />
    <path d="M19 12.9a10 10 0 0 0-2.3-1.7" />
    <path d="M2 8.8a15 15 0 0 1 4.2-2.6" />
    <path d="M22 8.8a15 15 0 0 0-11.3-3.7" />
    <path d="M12 20h.01" />
  </Line>
);

export const AlertIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="12" cy="12" r="10" />
    <path d="M12 8v4" />
    <path d="M12 16h.01" />
  </Line>
);

export const MicOffIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M2 2l20 20" />
    <path d="M9 9v2a3 3 0 0 0 5.1 2.1" />
    <path d="M15 9.3V5a3 3 0 0 0-5.7-1.3" />
    <path d="M19 10v1a7 7 0 0 1-.6 2.8" />
    <path d="M5 10v1a7 7 0 0 0 11.5 5.4" />
    <path d="M12 18v4" />
  </Line>
);

export const ClockIcon = (p: IconProps) => (
  <Line {...p}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </Line>
);

export const CloseIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M6 6l12 12" />
    <path d="M18 6L6 18" />
  </Line>
);

export const PlayIcon = ({ size = 16, ...p }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
    {...p}
  >
    <path d="M7 4l13 8-13 8z" />
  </svg>
);

export const PauseIcon = ({ size = 16, ...p }: IconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="currentColor"
    aria-hidden="true"
    {...p}
  >
    <rect x="6" y="4" width="4" height="16" rx="1" />
    <rect x="14" y="4" width="4" height="16" rx="1" />
  </svg>
);

export const StopIcon = (p: IconProps) => (
  <Line strokeWidth={2} {...p}>
    <rect x="6" y="6" width="12" height="12" rx="2" />
  </Line>
);

export const DownloadIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M12 3v12" />
    <path d="m7 10 5 5 5-5" />
    <path d="M4 20h16" />
  </Line>
);

export const ArrowIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M19 12H5" />
    <path d="m11 6-6 6 6 6" />
  </Line>
);

export const ExternalIcon = (p: IconProps) => (
  <Line {...p}>
    <path d="M14 4h6v6" />
    <path d="M20 4 10 14" />
    <path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" />
  </Line>
);
