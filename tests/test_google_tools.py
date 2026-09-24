import base64
import email
from unittest.mock import MagicMock

import pytest

from my_ai_agent import gmail_auth as service
from my_ai_agent.tools import google_tools
from my_ai_agent.tools.google_tools import GoogleTools


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
    def __init__(self, valid, expired=False, refresh_token="r", refresh_fails=False, scopes=None):
        self.scopes = service.SCOPES if scopes is None else scopes
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

    def has_scopes(self, scopes):
        return set(scopes) <= set(self.scopes)

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


def test_token_missing_new_scopes_triggers_new_sign_in(auth):
    send_only = FakeCreds(valid=True, scopes=["https://www.googleapis.com/auth/gmail.send"])
    auth.use_cached(send_only)

    assert service.load_credentials() is auth.flow.run_local_server.return_value


def test_create_draft_saves_without_confirmation(gmail, confirm_answer):
    gmail.users().drafts().create().execute.return_value = {"id": "d1"}

    result = GoogleTools().create_draft("Hi", "Hello there", "friend@example.com")

    assert "NOT been sent" in result
    body = gmail.users().drafts().create.call_args.kwargs["body"]["message"]["raw"]
    message = email.message_from_bytes(base64.urlsafe_b64decode(body))
    assert message["To"] == "friend@example.com"
    assert confirm_answer.asked == []
    gmail.users().messages().send().execute.assert_not_called()


def b64(text):
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def fake_inbox(gmail, messages):
    """messages: {id: (from, subject, snippet, payload)}"""
    gmail.users().messages().list().execute.return_value = {
        "messages": [{"id": i} for i in messages]
    }

    def get(userId, id, format, **kwargs):
        sender, subject, snippet, payload = messages[id]
        headers = [{"name": "From", "value": sender}, {"name": "Subject", "value": subject},
                   {"name": "Date", "value": "Mon, 1 Sep 2026"}]
        request = MagicMock()
        request.execute.return_value = {
            "id": id, "snippet": snippet, "payload": {"headers": headers, **payload}
        }
        return request

    gmail.users().messages().get.side_effect = get


def test_list_unread_emails(gmail):
    fake_inbox(gmail, {"m1": ("Amazon <a@amazon.in>", "Your order", "Arriving &#39;today&#39;", {}),
                       "m2": ("Boss <b@x.com>", "Meeting", "At 4pm", {})})

    result = GoogleTools().list_unread_emails(5)

    assert result.startswith(google_tools.UNTRUSTED_NOTE)
    assert "1. id=m1 | From: Amazon <a@amazon.in> | Subject: Your order" in result
    assert "Arriving 'today'" in result
    assert gmail.users().messages().list.call_args.kwargs["q"] == "is:unread in:inbox"


def test_search_emails_caps_results_and_reports_none(gmail):
    gmail.users().messages().list().execute.return_value = {}

    assert GoogleTools().search_emails("from:nobody", max_results=500) == (
        "No emails matching 'from:nobody' found."
    )
    assert gmail.users().messages().list.call_args.kwargs["maxResults"] == 10


def test_read_email_prefers_plain_text(gmail):
    payload = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/plain", "body": {"data": b64("Hello,\nSee you at 4.")}},
        {"mimeType": "text/html", "body": {"data": b64("<p>Hello</p>")}},
    ]}
    fake_inbox(gmail, {"m1": ("Boss <b@x.com>", "Meeting", "", payload)})

    result = GoogleTools().read_email("m1")

    assert "Subject: Meeting" in result
    assert result.endswith("Hello,\nSee you at 4.")
    assert google_tools.UNTRUSTED_NOTE in result


def test_extract_text_strips_html_when_no_plain_part():
    payload = {"mimeType": "text/html", "body": {"data": b64(
        "<style>p{color:red}</style><p>Your code is <b>123&amp;4</b></p>")}}

    assert google_tools.extract_text(payload) == "Your code is 123&4"


def test_read_email_truncates_long_bodies(gmail):
    payload = {"mimeType": "text/plain", "body": {"data": b64("x" * 10000)}}
    fake_inbox(gmail, {"m1": ("a", "b", "", payload)})

    assert GoogleTools().read_email("m1").endswith("[... truncated ...]")


def test_gmail_errors_are_reported(monkeypatch):
    def broken():
        raise RuntimeError("offline")

    monkeypatch.setattr(google_tools, "get_gmail_service", broken)
    tools = GoogleTools()

    for result in [tools.create_draft("s", "b", "t@x.com"), tools.list_unread_emails(),
                   tools.search_emails("q"), tools.read_email("m1")]:
        assert result.startswith("Failed") and "offline" in result
