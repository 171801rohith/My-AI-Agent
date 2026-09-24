import logging

from my_ai_agent import logging_setup


def test_logs_go_to_rotating_file(tmp_path, monkeypatch):
    monkeypatch.setattr(logging_setup, "LOG_DIR", tmp_path / "logs")
    root = logging.getLogger()
    before = list(root.handlers)
    try:
        logging_setup.setup_logging()
        logging.getLogger("my_ai_agent.tools.google_tools").info("Sent mail to x@example.com")
        for handler in root.handlers:
            handler.flush()
    finally:
        for handler in root.handlers[len(before):]:
            handler.close()
            root.removeHandler(handler)

    log = (tmp_path / "logs" / "sanctuary.log").read_text(encoding="utf-8")
    assert "INFO my_ai_agent.tools.google_tools: Sent mail to x@example.com" in log
