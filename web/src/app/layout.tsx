import type { Metadata, Viewport } from "next";
import {
  Amiri_Quran,
  Newsreader,
  Readex_Pro,
  Reem_Kufi,
} from "next/font/google";

import { Providers } from "@/components/Providers";
import { THEME_BOOTSTRAP } from "@/lib/theme";

import "./globals.css";
import "./shell.css";
import "./landing.css";
import "./reciters.css";

// Type system: Readex Pro for interface text (Arabic and Latin), Reem Kufi
// for the wordmark and headings, Amiri Quran for ayah text only, and
// Newsreader for Latin names set beside Arabic ones.
const readex = Readex_Pro({
  variable: "--font-readex",
  subsets: ["arabic", "latin"],
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});
const kufi = Reem_Kufi({
  variable: "--font-kufi",
  subsets: ["arabic"],
  weight: ["500", "700"],
  display: "swap",
});
const amiriQuran = Amiri_Quran({
  variable: "--font-amiri-quran",
  subsets: ["arabic"],
  weight: "400",
  display: "swap",
});
const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  display: "swap",
});

export const metadata: Metadata = {
  title: { default: "أنصِت — من الصوت إلى الآية", template: "%s · أنصِت" },
  description: "تعرّف على السورة والآية واسم القارئ من ثوانٍ من التلاوة",
  applicationName: "ANSIT",
  appleWebApp: {
    capable: true,
    title: "أنصت",
    statusBarStyle: "default",
  },
  icons: { icon: "/icons/icon.svg", apple: "/icons/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0E111B" },
    { media: "(prefers-color-scheme: light)", color: "#F6F1E7" },
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={`${readex.variable} ${kufi.variable} ${amiriQuran.variable} ${newsreader.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_BOOTSTRAP }} />
      </head>
      <body className="min-h-full">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
