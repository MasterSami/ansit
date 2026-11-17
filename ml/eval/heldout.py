"""Surahs and reciters reserved for evaluation.

The reciter gallery (Phase 3) must not use any ayah from HELDOUT_SURAHS, so that
reciter identification is evaluated on audio the gallery has never seen.
"""

# Varied ayah lengths and styles; 55 is included for its 31-fold refrain.
HELDOUT_SURAHS: tuple[int, ...] = (12, 19, 36, 55, 56, 67, 71, 75, 78, 87, 89, 93)

# EveryAyah folder -> recitation style. One folder per reciter (Hafs only; no
# translations, no Warsh, no teaching recordings). Verified against
# https://everyayah.com/data/recitations.js
EVAL_RECITERS: dict[str, str] = {
    "Abdul_Basit_Murattal_64kbps": "murattal",
    "Abdullah_Basfar_64kbps": "murattal",
    "Abdurrahmaan_As-Sudais_64kbps": "murattal",
    "Abu_Bakr_Ash-Shaatree_64kbps": "murattal",
    "Alafasy_64kbps": "murattal",
    "Ghamadi_40kbps": "murattal",
    "Hani_Rifai_64kbps": "murattal",
    "Husary_64kbps": "murattal",
    "Hudhaify_64kbps": "murattal",
    # The 64kbps folder is listed in recitations.js but every file in it is 404.
    "Ibrahim_Akhdar_32kbps": "murattal",
    "Maher_AlMuaiqly_64kbps": "murattal",
    "Minshawy_Murattal_128kbps": "murattal",
    "Mohammad_al_Tablaway_64kbps": "murattal",
    "Muhammad_Ayyoub_64kbps": "murattal",
    "Muhammad_Jibreel_64kbps": "murattal",
    "Saood_ash-Shuraym_64kbps": "murattal",
    "Salaah_AbdulRahman_Bukhatir_128kbps": "murattal",
    "Muhsin_Al_Qasim_192kbps": "murattal",
    "Abdullaah_3awwaad_Al-Juhaynee_128kbps": "murattal",
    "Salah_Al_Budair_128kbps": "murattal",
    "Abdullah_Matroud_128kbps": "murattal",
    "Ahmed_Neana_128kbps": "murattal",
    "Yasser_Ad-Dussary_128kbps": "murattal",
    "Nasser_Alqatami_128kbps": "murattal",
    "Ali_Jaber_64kbps": "murattal",
    "Fares_Abbad_64kbps": "murattal",
    "Abdul_Basit_Mujawwad_128kbps": "mujawwad",
    "Minshawy_Mujawwad_64kbps": "mujawwad",
}
