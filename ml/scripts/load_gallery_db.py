"""Load the reciter registry and gallery into PostgreSQL.

Usage:
  DATABASE_URL=postgresql+asyncpg://... \\
    uv run --project backend python ml/scripts/load_gallery_db.py [--reciter ID ...]

Run `make migrate` first. With --reciter only those reciters' rows are replaced,
which is how a new reciter is added without touching anyone else.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.speaker.gallery import Gallery
from app.speaker.store import load_gallery, save_gallery, upsert_reciters

REGISTRY = REPO / "ml" / "registry" / "reciters.json"
GALLERY = REPO / "ml" / "artifacts" / "gallery.npz"


async def run(url: str, reciters: set[str] | None) -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    gallery = Gallery.load(GALLERY)
    in_gallery = {v.reciter_id for v in gallery.voices}
    wanted = reciters or in_gallery
    missing = wanted - in_gallery
    if missing:
        raise SystemExit(f"not in {GALLERY.name}: {sorted(missing)} - run `make gallery` first")

    engine = create_async_engine(url)
    async with AsyncSession(engine) as session:
        await upsert_reciters(session, [r for r in registry if r["id"] in wanted])
        await save_gallery(session, gallery, wanted)
        await session.commit()
        stored = await load_gallery(session)
    await engine.dispose()
    print(
        f"loaded    {len(wanted)} reciter(s); database now holds "
        f"{len({v.reciter_id for v in stored.voices})} reciters, {len(stored.voices)} voices, "
        f"{len(stored.embeddings)} clip embeddings"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reciter", action="append", help="only load this reciter id")
    args = parser.parse_args()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("set DATABASE_URL")
    asyncio.run(run(url, set(args.reciter) if args.reciter else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
