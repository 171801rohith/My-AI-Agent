import pytest

from my_ai_agent.functions import open_url
from my_ai_agent.tools.basic_tools import BasicTools


@pytest.fixture
def tools():
    return BasicTools()


@pytest.fixture
def opened(monkeypatch):
    urls = []
    monkeypatch.setattr(open_url.webbrowser, "open_new_tab", lambda url: urls.append(url) or True)
    return urls


def test_registered_tool_names(tools):
    names = {t.metadata.name for t in tools.tools}
    assert names == {"add", "subtract", "multiply", "quotient", "remainder", "power", "open_url"}


@pytest.mark.parametrize(
    "method, a, b, expected",
    [
        ("add", 2, 3, 5),
        ("subtract", 2, 3, -1),
        ("multiply", 4, 2.5, 10),
        ("quotient", 7, 2, 3.5),
        ("remainder", 7, 3, 1),
        ("power", 2, 10, 1024),
    ],
)
def test_math(tools, method, a, b, expected):
    assert getattr(tools, method)(a, b) == expected


@pytest.mark.parametrize("method", ["quotient", "remainder"])
def test_division_by_zero_returns_error(tools, method):
    assert getattr(tools, method)(1, 0).startswith("Error")


def test_open_web_url_known_site(opened):
    assert open_url.open_web_url("YouTube ") == "https://www.youtube.com/"
    assert opened == ["https://www.youtube.com/"]


def test_open_web_url_unknown_site_raises(opened):
    with pytest.raises(ValueError, match="Known sites: youtube"):
        open_url.open_web_url("nonexistent")
    assert opened == []


def test_open_web_url_no_browser_raises(monkeypatch):
    monkeypatch.setattr(open_url.webbrowser, "open_new_tab", lambda url: False)
    with pytest.raises(RuntimeError):
        open_url.open_web_url("github")


def test_open_url_tool_known_site(tools, opened):
    assert tools.open_url("github") == "Successfully opened github at https://github.com/171801rohith"


def test_open_url_tool_reports_unknown_site_as_failure(tools, opened):
    assert tools.open_url("nonexistent").startswith("Failed")
