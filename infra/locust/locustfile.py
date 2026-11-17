"""Load test for POST /v1/identify.

Each simulated user uploads one recitation clip after another, with no pause.

Usage (server already running, rate limit raised for the test):
  uvx locust -f infra/locust/locustfile.py --headless --host http://localhost:8000 \
      -u 4 -r 4 -t 90s --csv /tmp/ansit-load

Clips are read from ANSIT_LOAD_CLIPS (default: the Phase 2 evaluation clips,
phone-like WebM/Opus, built by ml/eval/build_audio_eval.py). They are not in
the repository.
"""

import os
import random
from pathlib import Path

from locust import HttpUser, constant, events, task

REPO = Path(__file__).resolve().parents[2]
CLIPS_DIR = Path(os.environ.get("ANSIT_LOAD_CLIPS", REPO / "ml" / "data" / "eval_audio" / "clips"))
CLIPS = sorted(p for p in CLIPS_DIR.glob("*/*_phone.webm") if not p.parent.name.startswith("_"))


@events.init.add_listener
def _check_clips(environment: object, **_: object) -> None:
    if not CLIPS:
        raise SystemExit(f"no clips under {CLIPS_DIR}; build them or set ANSIT_LOAD_CLIPS")


class Listener(HttpUser):
    wait_time = constant(0)

    @task
    def identify(self) -> None:
        clip = random.choice(CLIPS)  # noqa: S311 - load generation, not security
        with self.client.post(
            "/v1/identify",
            files={"audio": (clip.name, clip.read_bytes(), "audio/webm")},
            data={"client": "web"},
            name="/v1/identify",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code}: {response.text[:120]}")
            elif response.json().get("status") not in ("match", "ambiguous", "no_match"):
                response.failure("unexpected body")
