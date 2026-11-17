"""Quran metadata, reciters and feedback endpoints."""

import uuid
from typing import Any

import httpx

from tests.api.conftest import Harness, api_client

# --------------------------------------------------------------------- quran


async def test_surah_list(api: httpx.AsyncClient, harness: Harness) -> None:
    body = (await api.get("/v1/surahs")).json()
    assert len(body["surahs"]) == 114
    assert [s["number"] for s in body["surahs"]] == list(range(1, 115))
    assert sum(s["ayah_count"] for s in body["surahs"]) == 6236
    assert body["surahs"][66] == {
        "number": 67,
        "name_ar": harness.index.surahs[66].name_ar,
        "name_en": "Al-Mulk",
        "ayah_count": 30,
        "revelation": "meccan",
    }
    assert "tanzil.net" in body["text_attribution"]


async def test_surah_detail(api: httpx.AsyncClient, harness: Harness) -> None:
    mulk = (await api.get("/v1/surahs/67")).json()
    assert (mulk["first_page"], mulk["first_juz"], mulk["ayah_count"]) == (562, 29, 30)
    assert (
        mulk["basmala_uthmani"]
        == harness.index.ayahs[harness.index.ayah_index(67, 1)].basmala_uthmani
    )
    assert mulk["basmala_uthmani"]
    # In Al-Fatiha the basmala is ayah 1; At-Tawba has none.
    assert (await api.get("/v1/surahs/1")).json()["basmala_uthmani"] is None
    assert (await api.get("/v1/surahs/9")).json()["basmala_uthmani"] is None


async def test_surah_out_of_range(api: httpx.AsyncClient) -> None:
    for number in ("0", "115", "abc"):
        response = await api.get(f"/v1/surahs/{number}")
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "invalid_request"


async def test_ayah_with_neighbours(api: httpx.AsyncClient, harness: Harness) -> None:
    body = (await api.get("/v1/ayahs/55/13", params={"context": 2})).json()
    index = harness.index
    assert body["ayah"]["surah"] == 55 and body["ayah"]["ayah"] == 13
    assert body["ayah"]["text_uthmani"] == index.ayahs[index.ayah_index(55, 13)].text_uthmani
    assert [a["ayah"] for a in body["context"]["before"]] == [11, 12]
    assert [a["ayah"] for a in body["context"]["after"]] == [14, 15]
    assert (
        body["context"]["before"][1]["text_uthmani"]
        == index.ayahs[index.ayah_index(55, 12)].text_uthmani
    )
    assert body["basmala_uthmani"] is None
    assert "tanzil.net" in body["text_attribution"]


async def test_ayah_context_stays_inside_the_surah(api: httpx.AsyncClient) -> None:
    first = (await api.get("/v1/ayahs/2/1", params={"context": 3})).json()
    assert first["context"]["before"] == []
    assert [a["ayah"] for a in first["context"]["after"]] == [2, 3, 4]
    assert first["basmala_uthmani"]

    last = (await api.get("/v1/ayahs/114/6", params={"context": 3})).json()
    assert [a["ayah"] for a in last["context"]["before"]] == [3, 4, 5]
    assert last["context"]["after"] == []

    plain = (await api.get("/v1/ayahs/2/255")).json()
    assert plain["context"] == {"before": [], "after": []}


async def test_ayah_not_found(api: httpx.AsyncClient) -> None:
    response = await api.get("/v1/ayahs/1/8")
    assert response.status_code == 404
    assert response.json()["error"] == {"code": "not_found", "message": "Surah 1 has no ayah 8."}
    assert (await api.get("/v1/ayahs/2/1", params={"context": 9})).status_code == 422


async def test_metadata_is_unavailable_until_the_index_loads() -> None:
    async with api_client(None) as client:
        response = await client.get("/v1/surahs")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "not_ready"


# ------------------------------------------------------------------ reciters


async def test_reciter_list(api: httpx.AsyncClient) -> None:
    reciters = (await api.get("/v1/reciters")).json()["reciters"]
    assert [r["id"] for r in reciters] == ["alafasy", "husary", "minshawi"]  # by English name
    husary = reciters[1]
    assert husary["styles"] == ["murattal", "mujawwad"]
    assert husary["country"] is None
    assert set(husary) == {"id", "name_ar", "name_en", "country", "styles"}  # no photo field


async def test_reciter_detail_with_audio_links(api: httpx.AsyncClient) -> None:
    body = (await api.get("/v1/reciters/husary")).json()
    assert [a["style"] for a in body["ayah_audio"]] == ["murattal", "mujawwad"]
    murattal = body["ayah_audio"][0]
    assert murattal["url_template"] == (
        "https://everyayah.com/data/husary_murattal_64kbps/{sss}{aaa}.mp3"
    )
    assert murattal["url"] is None

    at_ayah = (await api.get("/v1/reciters/husary", params={"surah": 67, "ayah": 1})).json()
    assert at_ayah["ayah_audio"][0]["url"] == (
        "https://everyayah.com/data/husary_murattal_64kbps/067001.mp3"
    )


async def test_reciter_errors(api: httpx.AsyncClient) -> None:
    assert (await api.get("/v1/reciters/nobody")).status_code == 404
    half = await api.get("/v1/reciters/husary", params={"surah": 67})
    assert half.status_code == 422
    beyond = await api.get("/v1/reciters/husary", params={"surah": 1, "ayah": 8})
    assert beyond.status_code == 404


# ------------------------------------------------------------------ feedback


def feedback(**fields: object) -> dict[str, object]:
    return {"identify_id": str(uuid.uuid4()), "kind": "wrong_ayah", **fields}


async def test_feedback_is_validated(api: httpx.AsyncClient) -> None:
    cases: list[tuple[dict[str, Any], str]] = [
        ({"kind": "nonsense"}, "kind"),
        ({"identify_id": "not-a-uuid"}, "identify_id"),
        ({"correct_surah": 115, "correct_ayah": 1}, "correct_surah"),
        ({"correct_surah": 2}, "both correct_surah and correct_ayah"),
        ({"correct_surah": 1, "correct_ayah": 8}, "no ayah 8"),
        ({"kind": "wrong_reciter", "correct_reciter_id": "nobody"}, "correct_reciter_id"),
    ]
    for fields, expected in cases:
        response = await api.post("/v1/feedback", json=feedback(**fields))
        assert response.status_code == 422, fields
        error = response.json()["error"]
        assert error["code"] == "invalid_request"
        assert expected in error["message"], error


async def test_feedback_without_a_database_says_so(api: httpx.AsyncClient) -> None:
    response = await api.post("/v1/feedback", json=feedback(correct_surah=67, correct_ayah=2))
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "feedback_unavailable"


async def test_openapi_documents_the_v1_endpoints(api: httpx.AsyncClient) -> None:
    paths = (await api.get("/openapi.json")).json()["paths"]
    assert {
        "/v1/identify",
        "/v1/surahs",
        "/v1/surahs/{number}",
        "/v1/ayahs/{surah}/{ayah}",
        "/v1/reciters",
        "/v1/reciters/{reciter_id}",
        "/v1/feedback",
        "/healthz",
        "/readyz",
    } <= set(paths)
