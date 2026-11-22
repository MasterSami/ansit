import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/",
    name: "ANSIT",
    short_name: "أنصت",
    description:
      "تعرّف على السورة والآية واسم القارئ من ثوانٍ من التلاوة، وتصفّح مكتبة القرّاء.",
    lang: "ar",
    dir: "rtl",
    // The installed app opens on the tool itself, not on the introduction.
    start_url: "/listen",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#F6F1E7",
    theme_color: "#F6F1E7",
    categories: ["education", "books", "music"],
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
    shortcuts: [
      { name: "الإنصات", url: "/listen" },
      { name: "مكتبة القرّاء", url: "/reciters" },
      { name: "السجل", url: "/history" },
    ],
  };
}
