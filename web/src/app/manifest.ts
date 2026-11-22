import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "ANSIT",
    short_name: "أنصت",
    description: "تعرّف على السورة والآية واسم القارئ من ثوانٍ من التلاوة",
    lang: "ar",
    dir: "rtl",
    // The installed app opens on the tool itself, not on the introduction.
    start_url: "/listen",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#0E1512",
    theme_color: "#0E1512",
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
      { src: "/icons/icon.svg", sizes: "any", type: "image/svg+xml" },
    ],
  };
}
