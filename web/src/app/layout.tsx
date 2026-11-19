import type { Metadata, Viewport } from "next";
import { Amiri, Amiri_Quran, IBM_Plex_Sans_Arabic } from "next/font/google";

import { Providers } from "@/components/Providers";
import { THEME_BOOTSTRAP } from "@/lib/theme";

import "./globals.css";

// UI text, display (wordmark, surah names) and ayah text, per the design tokens.
const plex = IBM_Plex_Sans_Arabic({
  variable: "--font-plex",
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});
const amiri = Amiri({
  variable: "--font-amiri",
  subsets: ["arabic"],
  weight: ["400", "700"],
  display: "swap",
});
const amiriQuran = Amiri_Quran({
  variable: "--font-amiri-quran",
  subsets: ["arabic"],
  weight: "400",
  display: "swap",
});

export const metadata: Metadata = {
  title: "أنصِت",
  description: "أنصِت، منصة خيرية مدعومة بالذكاء الاصطناعي للتعرّف على آيات القرآن الكريم وقرّائه.",
  applicationName: "أنصِت",
  appleWebApp: {
    capable: true,
    title: "أنصِت",
    statusBarStyle: "black-translucent",
  },
  icons: { icon: "/icons/icon.svg", apple: "/icons/icon-192.png" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: dark)", color: "#0E1512" },
    { media: "(prefers-color-scheme: light)", color: "#F7F4EC" },
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
      className={`${plex.variable} ${amiri.variable} ${amiriQuran.variable} h-full antialiased`}
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
