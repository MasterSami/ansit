"""Build the reciter registry: ml/registry/reciters.json (committed).

Usage: uv run --project backend python ml/scripts/build_registry.py

Names come from the mp3quran API (never typed by hand); recording folders come
from EveryAyah. The mapping between the two is the table below, checked by eye
against both sources. Country is left null: neither source provides it.
"""

import json
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()
OUT = REPO / "ml" / "registry" / "reciters.json"
MP3QURAN = "https://www.mp3quran.net/api/v3/reciters"

# slug -> (mp3quran reciter id, {EveryAyah folder: style})
# One folder per (reciter, style). Hafs only; translations, Warsh and folders
# that duplicate a recording at another bitrate are left out.
RECITERS: dict[str, tuple[int, dict[str, str]]] = {
    "abdul-basit": (
        51,
        {"Abdul_Basit_Murattal_64kbps": "murattal", "Abdul_Basit_Mujawwad_128kbps": "mujawwad"},
    ),
    "basfar": (60, {"Abdullah_Basfar_64kbps": "murattal"}),
    "sudais": (54, {"Abdurrahmaan_As-Sudais_64kbps": "murattal"}),
    "shatri": (4, {"Abu_Bakr_Ash-Shaatree_64kbps": "murattal"}),
    "ajmy": (5, {"ahmed_ibn_ali_al_ajamy_128kbps": "murattal"}),
    "alafasy": (123, {"Alafasy_64kbps": "murattal"}),
    "ghamdi": (30, {"Ghamadi_40kbps": "murattal"}),
    "rifai": (89, {"Hani_Rifai_64kbps": "murattal"}),
    "husary": (
        118,
        {
            "Husary_64kbps": "murattal",
            "Husary_Mujawwad_64kbps": "mujawwad",
            "Husary_Muallim_128kbps": "muallim",
        },
    ),
    "hudhaify": (74, {"Hudhaify_64kbps": "murattal"}),
    "akhdar": (1, {"Ibrahim_Akhdar_32kbps": "murattal"}),
    "muaiqly": (102, {"Maher_AlMuaiqly_64kbps": "murattal"}),
    "minshawi": (
        112,
        {"Minshawy_Murattal_128kbps": "murattal", "Minshawy_Mujawwad_64kbps": "mujawwad"},
    ),
    "tablawi": (106, {"Mohammad_al_Tablaway_64kbps": "murattal"}),
    "ayyub": (109, {"Muhammad_Ayyoub_64kbps": "murattal"}),
    "jibreel": (111, {"Muhammad_Jibreel_64kbps": "murattal"}),
    "shuraim": (31, {"Saood_ash-Shuraym_64kbps": "murattal"}),
    "bukhatir": (46, {"Salaah_AbdulRahman_Bukhatir_128kbps": "murattal"}),
    "qasim": (67, {"Muhsin_Al_Qasim_192kbps": "murattal"}),
    "juhany": (62, {"Abdullaah_3awwaad_Al-Juhaynee_128kbps": "murattal"}),
    "budair": (43, {"Salah_Al_Budair_128kbps": "murattal"}),
    "matrood": (59, {"Abdullah_Matroud_128kbps": "murattal"}),
    "neana": (9, {"Ahmed_Neana_128kbps": "murattal"}),
    "yasser-dosari": (92, {"Yasser_Ad-Dussary_128kbps": "murattal"}),
    "qatami": (86, {"Nasser_Alqatami_128kbps": "murattal"}),
    "ali-jaber": (76, {"Ali_Jaber_64kbps": "murattal"}),
    "fares-abbad": (81, {"Fares_Abbad_64kbps": "murattal"}),
    "banna": (121, {"mahmoud_ali_al_banna_32kbps": "murattal"}),
    "tunaiji": (24, {"khalefa_al_tunaiji_64kbps": "murattal"}),
    "qahtani": (21, {"Khaalid_Abdullaah_al-Qahtaanee_192kbps": "murattal"}),
    "sahl-yassin": (32, {"Sahl_Yassin_128kbps": "murattal"}),
    "yasser-salamah": (152, {"Yaser_Salamah_128kbps": "murattal"}),
    "alaqmi": (10, {"Akram_AlAlaqimy_128kbps": "murattal"}),
    "souasi": (77, {"Ali_Hajjaj_AlSuesy_128kbps": "murattal"}),
    "sowaid": (21203, {"Ayman_Sowaid_64kbps": "muallim"}),
}

# Reciters with no per-ayah recording on EveryAyah: slug -> mp3quran reciter id.
# Their gallery voice is built from mp3quran's full-surah files, and the apps
# cannot offer per-ayah playback for them.
MP3QURAN_ONLY: dict[str, int] = {
    "ahmad-talib": 137,
    "luhaidan": 107,
    "dukhain": 273,
}

# mp3quran labels each recording ("moshaf") in Arabic; these markers are
# compared after reading them from the API response, see _style_of().
HAFS_REWAYA_ID = 1


def _style_of(moshaf_type: int) -> str | None:
    """mp3quran moshaf_type = rewaya_id * 10 + kind; kind 1 murattal, 2 mujawwad, 3 muallim."""
    return {1: "murattal", 2: "mujawwad", 3: "muallim"}.get(moshaf_type % 10)


def main() -> int:
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        by_lang = {}
        for lang in ("ar", "eng"):
            response = client.get(MP3QURAN, params={"language": lang})
            response.raise_for_status()
            by_lang[lang] = {r["id"]: r for r in response.json()["reciters"]}
        folders = client.get("https://everyayah.com/data/recitations.js")
        folders.raise_for_status()
    text = folders.text
    listed = {
        v["subfolder"]
        for v in json.loads(text[text.index("{") : text.rindex("}") + 1]).values()
        if isinstance(v, dict)
    }

    registry = []
    everyone = {**RECITERS, **{slug: (mq_id, {}) for slug, mq_id in MP3QURAN_ONLY.items()}}
    for slug, (mq_id, sources) in everyone.items():
        if mq_id not in by_lang["ar"] or mq_id not in by_lang["eng"]:
            raise SystemExit(f"{slug}: mp3quran has no reciter {mq_id}")
        unknown = set(sources) - listed
        if unknown:
            raise SystemExit(f"{slug}: not in EveryAyah's recitations.js: {sorted(unknown)}")
        audio = [
            {"style": style, "server": moshaf["server"], "surah_total": moshaf["surah_total"]}
            for moshaf in by_lang["ar"][mq_id]["moshaf"]
            if moshaf["rewaya_id"] == HAFS_REWAYA_ID
            and (
                style := _style_of(moshaf["moshaf_type"])
                # mp3quran files some Hafs recordings under other kinds (for
                # example "special recitation"); for reciters we only have
                # there, those count as murattal.
                or ("murattal" if slug in MP3QURAN_ONLY else None)
            )
            is not None
        ]
        if not sources and not audio:
            raise SystemExit(f"{slug}: no EveryAyah folder and no Hafs recording on mp3quran")
        registry.append(
            {
                "id": slug,
                "name_ar": by_lang["ar"][mq_id]["name"].strip(),
                "name_en": " ".join(by_lang["eng"][mq_id]["name"].split()),
                "country": None,
                "styles": sorted(set(sources.values()) or {a["style"] for a in audio}),
                "sources": {
                    "everyayah": [{"folder": f, "style": s} for f, s in sources.items()],
                    "mp3quran_id": mq_id,
                    "mp3quran_audio": audio,
                },
                "active": True,
            }
        )
        print(f"{slug:16} {registry[-1]['name_en']:32} {registry[-1]['name_ar']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote     {OUT.relative_to(REPO)}  ({len(registry)} reciters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
