"""Download Quran-tuned Whisper models and convert them to CTranslate2 (int8, CPU).

Usage: uv run --project backend --group ml python ml/scripts/convert_models.py [NAME ...]

Output: ml/artifacts/asr/<name>/ (gitignored), loadable by faster-whisper offline.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.core.system_certs import use_system_certs_if_requested

use_system_certs_if_requested()
OUT_DIR = REPO / "ml" / "artifacts" / "asr"

# name -> (Hugging Face repo, pinned revision, license). Verified in docs/DATA_SOURCES.md.
MODELS: dict[str, tuple[str, str, str]] = {
    "tarteel-base": (
        "tarteel-ai/whisper-base-ar-quran",
        "5c3c53fdf9272c4f6ee0bee09a1e5a4a615ee25c",
        "apache-2.0",
    ),
    "tarteel-tiny": (
        "tarteel-ai/whisper-tiny-ar-quran",
        "c3d7e624af5c81bef25a10a2af3a5a84cb4dd0f0",
        "apache-2.0",
    ),
    "deepdml-small": (
        "deepdml/whisper-small-ar-quran-mix-norm",
        "2d0929ee4d62cf3642e4184c16e9cb939d86ea78",
        "apache-2.0",
    ),
}
DEFAULT_MODEL = "deepdml-small"


def convert(name: str, quantization: str, force: bool) -> Path:
    import ctranslate2
    from huggingface_hub import model_info
    from transformers import WhisperTokenizerFast

    repo, revision, license_id = MODELS[name]
    out = OUT_DIR / name
    if (out / "model.bin").exists() and not force:
        print(f"keep      {name}")
        return out
    if out.exists():
        shutil.rmtree(out)

    commit = model_info(repo, revision=revision).sha
    print(f"convert   {repo}@{commit[:10]} -> {out.relative_to(REPO)} ({quantization})")
    converter = ctranslate2.converters.TransformersConverter(
        repo, revision=commit, copy_files=["preprocessor_config.json"]
    )
    converter.convert(str(out), quantization=quantization)
    # faster-whisper needs tokenizer.json next to the model to run fully offline.
    tokenizer = WhisperTokenizerFast.from_pretrained(repo, revision=commit)
    tokenizer.backend_tokenizer.save(str(out / "tokenizer.json"))
    (out / "SOURCE.json").write_text(
        json.dumps(
            {
                "repo": repo,
                "commit": commit,
                "license": license_id,
                "quantization": quantization,
                "ctranslate2": ctranslate2.__version__,
            },
            indent=2,
        )
        + "\n"
    )
    size_mb = sum(f.stat().st_size for f in out.iterdir()) / 1e6
    print(f"done      {name}  ({size_mb:.0f} MB)")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="*", metavar="NAME", help=f"any of: {', '.join(MODELS)}")
    parser.add_argument("--all", action="store_true", help="convert every known model")
    parser.add_argument("--quantization", default="int8")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    names = list(MODELS) if args.all else (args.names or [DEFAULT_MODEL])
    unknown = [n for n in names if n not in MODELS]
    if unknown:
        parser.error(f"unknown model(s): {', '.join(unknown)}")
    for name in names:
        convert(name, args.quantization, args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
