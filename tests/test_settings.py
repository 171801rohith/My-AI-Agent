import pytest

from config.settings import MissingSettingError, Settings


@pytest.fixture
def clean_env(monkeypatch):
    for name in ["GOOGLE_API_KEY", "GEMINI_MODEL", "OLLAMA_MODEL", "WAKE_WORD",
                 "WAKE_THRESHOLD", "WHISPER_MODEL"]:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_defaults(clean_env):
    s = Settings.from_env()

    assert s.google_api_key is None
    assert s.ollama_model == "hermes3:8b"
    assert s.wake_word == "hey_jarvis"
    assert s.wake_threshold == 0.5


def test_environment_overrides_defaults(clean_env):
    clean_env.setenv("OLLAMA_MODEL", "llama3.1:8b")
    clean_env.setenv("WAKE_THRESHOLD", "0.7")

    s = Settings.from_env()

    assert s.ollama_model == "llama3.1:8b"
    assert s.wake_threshold == 0.7


def test_empty_value_falls_back_to_default(clean_env):
    clean_env.setenv("WHISPER_MODEL", "")

    assert Settings.from_env().whisper_model == "base.en"


def test_require_missing_setting_names_the_variable(clean_env):
    with pytest.raises(MissingSettingError, match="GOOGLE_API_KEY is not set"):
        Settings.from_env().require("google_api_key")


def test_require_returns_value(clean_env):
    clean_env.setenv("GOOGLE_API_KEY", "abc")

    assert Settings.from_env().require("google_api_key") == "abc"
