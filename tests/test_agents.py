import asyncio
from typing import Any

import pytest
from llama_index.core.bridge.pydantic import Field
from llama_index.core.llms import ChatMessage, ChatResponse, LLMMetadata
from llama_index.core.llms.function_calling import FunctionCallingLLM
from llama_index.core.llms.llm import ToolSelection

from my_ai_agent.persona import persona_prompt
from my_ai_agent.audio import text_to_speech as tts
from my_ai_agent.tools.basic_tools import BasicTools


class ScriptedLLM(FunctionCallingLLM):
    """Offline tool-calling LLM. Each script step is either a text answer or a
    (tool_name, kwargs) tool call. Every message list it receives is recorded."""

    script: list = Field(default_factory=list)
    calls: list = Field(default_factory=list)

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name="scripted", is_function_calling_model=True)

    def _prepare_chat_with_tools(self, tools, user_msg=None, chat_history=None, **kwargs):
        messages = list(chat_history or [])
        if user_msg:
            messages.append(ChatMessage(role="user", content=str(user_msg)))
        return {"messages": messages, "tools": tools}

    def get_tool_calls_from_response(self, response, error_on_no_tool_call=True, **kwargs):
        return response.message.additional_kwargs.get("tool_calls", [])

    def _next(self, messages) -> ChatResponse:
        self.calls.append(list(messages))
        step = self.script.pop(0)
        if isinstance(step, str):
            return ChatResponse(message=ChatMessage(role="assistant", content=step), delta=step)
        name, kwargs = step
        call = ToolSelection(tool_id=f"call-{len(self.calls)}", tool_name=name, tool_kwargs=kwargs)
        return ChatResponse(
            message=ChatMessage(role="assistant", content="", additional_kwargs={"tool_calls": [call]})
        )

    def chat(self, messages, **kwargs: Any) -> ChatResponse:
        return self._next(messages)

    async def achat(self, messages, **kwargs: Any) -> ChatResponse:
        return self._next(messages)

    def stream_chat(self, messages, **kwargs: Any):
        yield self._next(messages)

    async def astream_chat(self, messages, **kwargs: Any):
        response = self._next(messages)

        async def gen():
            yield response

        return gen()

    def complete(self, *args, **kwargs):
        raise NotImplementedError

    async def acomplete(self, *args, **kwargs):
        raise NotImplementedError

    def stream_complete(self, *args, **kwargs):
        raise NotImplementedError

    async def astream_complete(self, *args, **kwargs):
        raise NotImplementedError


@pytest.fixture
def agent_gemini(monkeypatch, fresh_import):
    """Import my_ai_agent.agents.gemini with Gemini swapped for an offline scripted LLM."""
    import llama_index.llms.google_genai as google_genai

    import my_ai_agent.settings as config_settings

    llm = ScriptedLLM()
    monkeypatch.setattr(google_genai, "GoogleGenAI", lambda **kwargs: llm)
    # Don't depend on a real key in .env.
    monkeypatch.setattr(
        config_settings, "settings", config_settings.Settings(google_api_key="test-key")
    )
    module = fresh_import("my_ai_agent.agents.gemini")
    module.fake_llm = llm
    return module


def ask(agent_module, message):
    return asyncio.run(agent_module.generateResponse(message))


def contents(messages, role):
    return [m.content for m in messages if m.role == role]


def test_gemini_agent_registers_all_tools(agent_gemini):
    names = {t.metadata.name for t in agent_gemini.tools}
    assert {"add", "open_app", "rename_files_to_episodes", "send_mail"} <= names
    assert len(names) == 22


def test_gemini_agent_generates_response(agent_gemini):
    agent_gemini.fake_llm.script = ["pong"]

    assert ask(agent_gemini, "ping") == "pong"


def test_persona_is_sent_as_system_prompt(agent_gemini):
    agent_gemini.fake_llm.script = ["pong"]
    ask(agent_gemini, "ping")

    first = agent_gemini.fake_llm.calls[0][0]
    assert first.role == "system"
    assert "I am Sanctuary" in first.content
    assert "{tool_desc}" not in persona_prompt


def test_agent_calls_tools_and_uses_result(agent_gemini):
    agent_gemini.fake_llm.script = [("add", {"a": 2, "b": 3}), "The answer is 5"]

    assert ask(agent_gemini, "what is 2 + 3?") == "The answer is 5"
    tool_messages = [m for m in agent_gemini.fake_llm.calls[1] if m.role == "tool"]
    assert "5" in str(tool_messages[0].content)


def test_user_message_sent_to_llm_once(agent_gemini):
    marker = "UNIQUE-MARKER-4821"
    agent_gemini.fake_llm.script = ["ok"]

    ask(agent_gemini, marker)

    assert contents(agent_gemini.fake_llm.calls[-1], "user").count(marker) == 1


def test_conversation_is_remembered_between_turns(agent_gemini):
    agent_gemini.fake_llm.script = ["pong", "second answer"]

    ask(agent_gemini, "ping")
    ask(agent_gemini, "again")

    last = agent_gemini.fake_llm.calls[-1]
    assert contents(last, "user") == ["ping", "again"]
    assert "pong" in contents(last, "assistant")


def test_ollama_agent_uses_hermes3_with_native_tool_calling(fresh_import):
    agent_ollama = fresh_import("my_ai_agent.agents.ollama")

    assert agent_ollama.llm.model == "hermes3:8b"
    assert type(agent_ollama.agent).__name__ == "FunctionAgent"
    assert "I am Sanctuary" in agent_ollama.agent.system_prompt


def test_react_agent_keeps_full_format_and_persona():
    from my_ai_agent.agents.common import build_agent

    tools = BasicTools().tools
    agent = build_agent(ScriptedLLM(), tools, native_tool_calling=False)

    assert type(agent).__name__ == "ReActAgent"
    system = agent.formatter.format(tools, chat_history=[])[0]
    assert "I am Sanctuary" in system.content
    for token in ["Thought:", "Action:", "Action Input:", "Answer:"]:
        assert token in system.content


def test_both_agents_expose_the_same_tools(agent_gemini, fresh_import):
    agent_ollama = fresh_import("my_ai_agent.agents.ollama")

    gemini = {t.metadata.name for t in agent_gemini.tools}
    assert {t.metadata.name for t in agent_ollama.tools} == gemini


def test_text_to_speech_raises_on_failure(monkeypatch):
    def broken_init():
        raise RuntimeError("no speech engine")

    monkeypatch.setattr(tts.pyttsx3, "init", broken_init)
    monkeypatch.setattr(tts.os, "remove", lambda path: None)  # keep the real output WAVs

    with pytest.raises(RuntimeError):
        asyncio.run(tts.text_to_speech("hello"))


def test_conversation_is_saved_and_resumed_by_a_new_responder(agent_gemini):
    from my_ai_agent.agents.common import make_responder

    agent_gemini.fake_llm.script = ["pong", "you said ping"]
    ask(agent_gemini, "ping")

    restarted = make_responder(agent_gemini.agent)  # like starting the app again
    assert restarted.resume_history() == 2
    asyncio.run(restarted("what did I say?"))

    last = agent_gemini.fake_llm.calls[-1]
    assert contents(last, "user") == ["ping", "what did I say?"]
    assert "pong" in contents(last, "assistant")


def test_remembered_facts_are_in_the_system_prompt(monkeypatch, fresh_import):
    from my_ai_agent import memory_store
    from my_ai_agent.agents.common import build_agent

    memory_store.add_fact("My name is Rohith")
    agent = build_agent(ScriptedLLM(), [], native_tool_calling=True)

    assert "- My name is Rohith" in agent.system_prompt


def test_responder_streams_final_text_but_not_tool_steps(agent_gemini):
    agent_gemini.fake_llm.script = [("add", {"a": 2, "b": 3}), "The answer is 5"]
    deltas = []

    reply = asyncio.run(agent_gemini.generateResponse("2 + 3?", on_text=deltas.append))

    assert reply == "The answer is 5"
    assert deltas == ["The answer is 5"]


def test_react_agent_does_not_stream_scratch_text():
    from my_ai_agent.agents.common import build_agent, make_responder

    llm = ScriptedLLM()
    responder = make_responder(build_agent(llm, [], native_tool_calling=False))
    deltas = []

    class Handler:
        def __await__(self):
            async def done():
                return "final"
            return done().__await__()

        async def stream_events(self):
            raise AssertionError("ReAct output must not be streamed")
            yield

    responder.agent = type("FakeReAct", (), {"run": lambda self, **kw: Handler()})()

    assert asyncio.run(responder("hi", on_text=deltas.append)) == "final"
    assert deltas == []
