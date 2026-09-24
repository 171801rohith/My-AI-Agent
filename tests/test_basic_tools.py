import pytest

from Functions import open_url
from Tools.basic_tools import BasicTools


@pytest.fixture
def tools():
    return BasicTools()


@pytest.fixture
def opened(monkeypatch):
    urls = []
    monkeypatch.setattr(open_url.webbrowser, "open_new_tab", urls.append)
    return urls


def test_registered_tool_names(tools):
    names = {t.metadata.name for t in tools.tools}
    assert names == {"add", "multiply", "quotient", "remainder", "power", "open_url"}


@pytest.mark.parametrize(
    "method, a, b, expected",
    [
        ("add", 2, 3, 5),
        ("multiply", 4, 2.5, 10),
        ("quotient", 7, 2, 3.5),
        ("remainder", 7, 3, 1),
        ("power", 2, 10, 1024),
    ],
)
def test_math(tools, method, a, b, expected):
    assert getattr(tools, method)(a, b) == expected


@pytest.mark.xfail(reason="substract() exists but is never registered as a tool")
def test_subtract_is_exposed_to_agent(tools):
    assert "substract" in {t.metadata.name for t in tools.tools}


def test_quotient_by_zero_raises(tools):
    with pytest.raises(ZeroDivisionError):
        tools.quotient(1, 0)


def test_open_web_url_known_site(opened):
    result = open_url.open_web_url("YouTube")
    assert opened == ["https://www.youtube.com/"]
    assert result.startswith("Successfully")


def test_open_web_url_unknown_site(opened):
    result = open_url.open_web_url("nonexistent")
    assert opened == []
    assert result.startswith("Failed")


def test_open_url_tool_known_site(tools, opened):
    assert tools.open_url("github").startswith("Successfully")


@pytest.mark.xfail(reason="open_url reports success even when the site is unknown")
def test_open_url_tool_reports_unknown_site_as_failure(tools, opened):
    assert tools.open_url("nonexistent").startswith("Failed")
