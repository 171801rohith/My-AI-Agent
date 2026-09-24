from llama_index.core.llms import ChatMessage

from my_ai_agent import memory_store
from my_ai_agent.tools.memory_tools import MemoryTools


def test_remember_list_and_forget():
    tools = MemoryTools()

    assert tools.remember_fact("My brother's email is ravi@example.com").startswith("Remembered")
    assert tools.remember_fact("I prefer short answers").startswith("Remembered")
    assert tools.remember_fact("i prefer SHORT answers").startswith("Already")
    assert tools.list_facts() == (
        "- My brother's email is ravi@example.com\n- I prefer short answers"
    )

    assert tools.forget_fact("brother") == "Forgot: My brother's email is ravi@example.com"
    assert tools.forget_fact("brother").startswith("No remembered fact")
    assert memory_store.load_facts() == ["I prefer short answers"]


def test_facts_prompt():
    assert memory_store.facts_prompt() == ""
    memory_store.add_fact("I live in Chennai")

    assert "## What you remember about the user" in memory_store.facts_prompt()
    assert "- I live in Chennai" in memory_store.facts_prompt()


def test_history_keeps_recent_plain_messages_only():
    messages = [ChatMessage(role="system", content="persona")]
    for i in range(15):
        messages += [ChatMessage(role="user", content=f"q{i}"),
                     ChatMessage(role="assistant", content=f"a{i}")]
    messages.append(ChatMessage(role="tool", content="5"))
    messages.append(ChatMessage(role="assistant", content=""))  # tool-call step, no text

    memory_store.save_history(messages)
    loaded = memory_store.load_history()

    assert len(loaded) == memory_store.HISTORY_MESSAGES
    assert [m.content for m in loaded[-2:]] == ["q14", "a14"]
    assert {m.role.value for m in loaded} == {"user", "assistant"}


def test_damaged_files_do_not_break_startup():
    memory_store.FACTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    memory_store.FACTS_PATH.write_text("{not json", encoding="utf-8")
    memory_store.HISTORY_PATH.write_text("", encoding="utf-8")

    assert memory_store.load_facts() == []
    assert memory_store.load_history() == []
