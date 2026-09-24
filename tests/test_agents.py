import asyncio
from typing import Any

import pytest
from llama_index.core.llms import (
    ChatMessage,
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback

from config.system_prompt import react_system_prompt
from Functions import text_to_speech as tts


class RecordingLLM(CustomLLM):
    """Offline LLM that answers immediately in ReAct format and records every prompt."""

    prompts: list = []

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name="recording")

    @llm_completion_callback()
    def complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponse:
        self.prompts.append(prompt)
        return CompletionResponse(text="Thought: I can answer.\nAnswer: pong")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, formatted: bool = False, **kwargs: Any) -> CompletionResponseGen:
        response = self.complete(prompt)
        yield CompletionResponse(text=response.text, delta=response.text)


@pytest.fixture
def agent_gemini(monkeypatch, fresh_import):
    """Import Agents.agent_gemini with Gemini swapped for an offline recording LLM."""
    import llama_index.llms.google_genai as google_genai

    llm = RecordingLLM()
    llm.prompts = []
    monkeypatch.setattr(google_genai, "GoogleGenAI", lambda **kwargs: llm)
    module = fresh_import("Agents.agent_gemini")
    module.recording_llm = llm
    return module


def test_gemini_agent_registers_all_tools(agent_gemini):
    names = {t.metadata.name for t in agent_gemini.tools}
    assert {"add", "open_app", "rename_files_to_episodes", "send_mail"} <= names
    assert len(names) == 12


def test_gemini_agent_generates_response(agent_gemini):
    history = [ChatMessage(role="user", content="ping")]

    assert asyncio.run(agent_gemini.generateResponse("ping", history)) == "pong"


@pytest.mark.xfail(reason="prompt is passed as user_msg AND as the last chat_history entry")
def test_user_message_sent_to_llm_once(agent_gemini):
    marker = "UNIQUE-MARKER-4821"
    history = [ChatMessage(role="user", content=marker)]

    asyncio.run(agent_gemini.generateResponse(marker, history))

    assert agent_gemini.recording_llm.prompts[-1].count(marker) == 1


@pytest.mark.xfail(reason="ReAct format examples (Thought/Action/Answer) were removed from the header")
def test_system_prompt_describes_react_format():
    template = react_system_prompt.get_template()
    for token in ["Thought:", "Action:", "Action Input:", "Answer:"]:
        assert token in template


@pytest.mark.xfail(raises=ImportError, reason="agent_ollama imports a non-existent `Tools` class")
def test_ollama_agent_imports(fresh_import):
    fresh_import("Agents.agent_ollama")


@pytest.mark.xfail(reason="text_to_speech swallows errors and returns None")
def test_text_to_speech_raises_on_failure(monkeypatch):
    def broken_init():
        raise RuntimeError("no speech engine")

    monkeypatch.setattr(tts.pyttsx3, "init", broken_init)
    monkeypatch.setattr(tts.os, "remove", lambda path: None)  # keep the real output WAVs

    with pytest.raises(RuntimeError):
        asyncio.run(tts.text_to_speech("hello"))
