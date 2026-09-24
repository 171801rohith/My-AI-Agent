import base64
import email
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


def test_send_mail_escapes_html(gmail):
    GoogleTools().send_mail("s", "<script>alert(1)</script>", "x@example.com")

    assert "<script>" not in html_part(sent_message(gmail))


class FakeCreds:
    def __init__(self, valid, expired=False, refresh_token="r", refresh_fails=False):
        self.valid = valid
        self.expired = expired
        self.refresh_token = refresh_token
        self.refresh_fails = refresh_fails
        self.refreshed = False

    def refresh(self, request):
        if self.refresh_fails:
            raise service.RefreshError("token revoked")
        self.refreshed = True
        self.valid = True

    def to_json(self):
        return '{"fake": true}'


@pytest.fixture
def auth(tmp_path, monkeypatch):
    """Point service.py at a temp token file and fake the Google auth calls."""
    token = tmp_path / "token.json"
    monkeypatch.setattr(service, "TOKEN_PATH", str(token))
    flow = MagicMock()
    flow.run_local_server.return_value = FakeCreds(valid=True)
    monkeypatch.setattr(
        service.InstalledAppFlow, "from_client_secrets_file", MagicMock(return_value=flow)
    )

    def use_cached(creds):
        token.write_text("{}")
        monkeypatch.setattr(
            service.Credentials, "from_authorized_user_file", MagicMock(return_value=creds)
        )

    auth = MagicMock(token=token, flow=flow, use_cached=use_cached)
    return auth


def test_valid_cached_token_is_used(auth):
    creds = FakeCreds(valid=True)
    auth.use_cached(creds)

    assert service.load_credentials() is creds
    auth.flow.run_local_server.assert_not_called()


def test_expired_token_is_refreshed_and_saved(auth):
    creds = FakeCreds(valid=False, expired=True)
    auth.use_cached(creds)

    assert service.load_credentials() is creds
    assert creds.refreshed
    assert auth.token.read_text() == '{"fake": true}'
    auth.flow.run_local_server.assert_not_called()


def test_revoked_token_triggers_new_sign_in(auth):
    auth.use_cached(FakeCreds(valid=False, expired=True, refresh_fails=True))

    assert service.load_credentials() is auth.flow.run_local_server.return_value


def test_first_run_signs_in_and_saves_token(auth):
    creds = service.load_credentials()

    assert creds is auth.flow.run_local_server.return_value
    assert auth.token.read_text() == '{"fake": true}'


def test_get_gmail_service_builds_client(auth, monkeypatch):
    auth.use_cached(FakeCreds(valid=True))
    monkeypatch.setattr(service, "build", lambda *a, **k: "gmail-client")

    assert service.get_gmail_service() == "gmail-client"


def test_declined_send_mail_is_not_sent(gmail, confirm_answer):
    confirm_answer.approve = False

    assert GoogleTools().send_mail("s", "b", "x@example.com").startswith("Cancelled")
    gmail.users().messages().send().execute.assert_not_called()
    assert "To: x@example.com" in confirm_answer.asked[0][1]


def test_send_mail_keeps_line_breaks_in_html(gmail):
    GoogleTools().send_mail("s", "Hi,\nSee you", "x@example.com")

    assert "Hi,<br>See you" in html_part(sent_message(gmail))
