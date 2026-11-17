from app.asr.engine import ASRResult
from app.asr.guards import GuardConfig, check_asr_result

CONFIG = GuardConfig()
# Arbitrary Arabic-letter words built from code points (not Quran text).
W1, W2, W3 = "باب", "كتب", "قلم"


def result(
    text: str, logprob: float = -0.1, no_speech: float = 0.01, ratio: float = 1.2
) -> ASRResult:
    return ASRResult(text, logprob, no_speech, 100.0, ratio)


def test_confident_result_passes() -> None:
    assert check_asr_result(result(f"{W1} {W2} {W3}"), CONFIG) == []


def test_empty_or_non_arabic_output() -> None:
    assert check_asr_result(result(""), CONFIG) == ["empty"]
    assert check_asr_result(result("  ...  "), CONFIG) == ["empty"]
    assert check_asr_result(result("thank you for watching"), CONFIG) == ["empty"]


def test_high_no_speech_probability() -> None:
    assert check_asr_result(result(f"{W1} {W2}", no_speech=0.9), CONFIG) == ["no_speech"]
    assert check_asr_result(result(f"{W1} {W2}", no_speech=0.6), CONFIG) == []  # boundary


def test_low_log_probability() -> None:
    assert check_asr_result(result(f"{W1} {W2}", logprob=-1.4), CONFIG) == ["low_logprob"]


def test_repetition_loop() -> None:
    looping = " ".join([W1] * 7)
    assert check_asr_result(result(looping), CONFIG) == ["repetition"]
    assert check_asr_result(result(" ".join([W1] * 6)), CONFIG) == []  # allowed run length
    assert check_asr_result(result(f"{W1} {W2}", ratio=3.0), CONFIG) == ["repetition"]


def test_known_hallucination_phrase_is_flagged_even_with_diacritics() -> None:
    credit = "ترجمة نانسي قنقر"
    assert "known_hallucination" in check_asr_result(result(f"{W1} {credit}"), CONFIG)
    marked = credit.replace("ت", "تَ", 1)  # add a fatha
    assert "known_hallucination" in check_asr_result(result(marked), CONFIG)


def test_several_flags_are_all_reported() -> None:
    flags = check_asr_result(result(" ".join([W1] * 9), logprob=-2.0, no_speech=0.95), CONFIG)
    assert flags == ["no_speech", "low_logprob", "repetition"]


def test_thresholds_are_configurable() -> None:
    strict = GuardConfig(max_no_speech_prob=0.1, min_avg_logprob=-0.05, max_word_run=1)
    flags = check_asr_result(result(f"{W1} {W1} {W2}", logprob=-0.1, no_speech=0.2), strict)
    assert flags == ["no_speech", "low_logprob", "repetition"]
