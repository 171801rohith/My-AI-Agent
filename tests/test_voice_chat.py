import pytest


@pytest.fixture
def voice_chat(stub_modules, fresh_import):
    async def fake_async(*args, **kwargs):
        return None

    stub_modules(
        **{
            "Agents.agent_gemini": {"generateResponse": fake_async},
            "Functions.wake_word": {"wake_sanctuary": lambda: False},
            "Functions.play_audio": {
                "play_audio_and_print_response": fake_async,
                "play_intro_outro": fake_async,
            },
            "Functions.speech_to_text": {
                "speech_to_text": lambda: "",
                "record_audio": lambda console: False,
            },
        }
    )
    return fresh_import("main_voice_chat")


@pytest.mark.parametrize("phrase", ["exit chat", "quit chat", "please quit chat now"])
def test_termination_phrases(voice_chat, phrase):
    assert voice_chat.check_for_termination(phrase)


@pytest.mark.parametrize("phrase", ["chat", "open chat", "exit", "chat exit"])
def test_non_termination_phrases(voice_chat, phrase):
    assert not voice_chat.check_for_termination(phrase)


@pytest.mark.parametrize("phrase", ["Exit chat.", "Quit, chat!", "OK. Exit chat"])
def test_termination_ignores_case_and_punctuation(voice_chat, phrase):
    assert voice_chat.check_for_termination(phrase)


def test_termination_needs_whole_words(voice_chat):
    assert not voice_chat.check_for_termination("exit chatroom")
