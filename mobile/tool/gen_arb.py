"""Build lib/l10n/app_ar.arb from the web app's Arabic copy.

The web app's `messages/ar.json` is the single source of interface text. This
script flattens it (`home.tapToListen` -> `homeTapToListen`), declares the
placeholders, and applies the few strings that differ on a phone.

Usage (from the repository root):  python mobile/tool/gen_arb.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "web" / "messages" / "ar.json"
TARGET = ROOT / "mobile" / "lib" / "l10n" / "app_ar.arb"

# Strings that talk about a browser on the web, or exist only on mobile.
OVERRIDES: dict[str, str] = {
    "statesDeniedBody": (
        "لا نستطيع الإنصات بدون إذن المايكروفون. اسمح به من إعدادات التطبيق، ثم حاول مرة أخرى."
    ),
    "statesUnavailableBody": "لم نجد مايكروفونًا يعمل على هذا الجهاز.",
    "statesNotFoundBody": "ربما حُذفت من سجلّ هذا الجهاز.",
    "statesOpenSettings": "فتح إعدادات التطبيق",
    "settingsServer": "الخادم",
    "settingsServerLabel": "عنوان الخادم",
    "settingsServerHint": "للتجربة فقط: عنوان خدمة أنصِت على شبكتك",
    "settingsServerSave": "حفظ العنوان",
    "settingsServerSaved": "تم حفظ العنوان",
}


def main() -> None:
    messages: dict[str, dict[str, str]] = json.loads(SOURCE.read_text(encoding="utf-8"))
    flat: dict[str, str] = {}
    for namespace, entries in messages.items():
        for key, value in entries.items():
            flat[f"{namespace}{key[0].upper()}{key[1:]}"] = value
    flat.update(OVERRIDES)

    arb: dict[str, object] = {"@@locale": "ar"}
    for key in sorted(flat):
        value = flat[key]
        arb[key] = value
        names = sorted(set(re.findall(r"\{(\w+)\}", value)))
        if names:
            arb[f"@{key}"] = {"placeholders": {name: {"type": "String"} for name in names}}

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(arb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(flat)} strings to {TARGET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
