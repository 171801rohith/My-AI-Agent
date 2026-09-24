import base64
import email
import pickle
from unittest.mock import MagicMock

import pytest

import service
from Tools import google_tools
from Tools.google_tools import GoogleTools


@pytest.fixture
def gmail(monkeypatch):
    fake = MagicMock()
    fake.users().messages().send().execute.return_value = {"id": "abc123"}
    monkeypatch.setattr(google_tools, "get_gmail_service", lambda: fake)
    return fake


def sent_message(gmail):
    body = gmail.users().messages().send.call_args.kwargs["body"]
    return email.message_from_bytes(base64.urlsafe_b64decode(body["raw"]))


def html_part(message):
    return next(
        p.get_payload(decode=True).decode()
        for p in message.walk()
        if p.get_content_type() == "text/html"
    )


def test_send_mail_builds_message(gmail):
    result = GoogleTools().send_mail("Hi", "Hello there", "friend@example.com")

    assert result == "Successfully sent a mail: friend@example.com."
    message = sent_message(gmail)
    assert message["To"] == "friend@example.com"
    assert message["Subject"] == "Hi"
    assert "Disclaimer" in html_part(message)


def test_send_mail_reports_errors(monkeypatch):
    def broken():
        raise RuntimeError("no network")

    monkeypatch.setattr(google_tools, "get_gmail_service", broken)
    assert GoogleTools().send_mail("s", "b", "x@example.com").startswith("Failed")


@pytest.mark.xfail(reason="mail_body is inserted into the HTML part without escaping")
def test_send_mail_escapes_html(gmail):
    GoogleTools().send_mail("s", "<script>alert(1)</script>", "x@example.com")

    assert "<script>" not in html_part(sent_message(gmail))


class FakeCreds:
    def __init__(self, valid, expired=False, refresh_token="r"):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refreshed = False

    def refresh(self, request):
        self.refreshed = True
        self.valid = True


def test_get_gmail_service_uses_cached_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "token.pickle").write_bytes(pickle.dumps(FakeCreds(valid=True)))
    monkeypatch.setattr(service, "build", lambda *a, **k: "gmail-client")
    monkeypatch.setattr(service.InstalledAppFlow, "from_client_secrets_file", MagicMock())

    assert service.get_gmail_service() == "gmail-client"
    service.InstalledAppFlow.from_client_secrets_file.assert_not_called()


@pytest.mark.xfail(reason="expired credentials are never refreshed or re-authorised")
def test_get_gmail_service_refreshes_expired_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "token.pickle").write_bytes(
        pickle.dumps(FakeCreds(valid=False, expired=True))
    )
    captured = {}
    monkeypatch.setattr(
        service, "build", lambda *a, credentials, **k: captured.setdefault("c", credentials)
    )

    service.get_gmail_service()

    assert captured["c"].valid
