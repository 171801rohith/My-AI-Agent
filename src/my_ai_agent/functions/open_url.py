import webbrowser

from my_ai_agent.websites import WEB_URLS


def open_web_url(web_name: str) -> str:
    """Open a known site in a new browser tab and return its URL.
    Raises ValueError for unknown sites so callers cannot mistake it for success."""
    url = WEB_URLS.get(web_name.strip().lower())
    if url is None:
        raise ValueError(f"Unknown site '{web_name}'. Known sites: {', '.join(WEB_URLS)}")
    if not webbrowser.open_new_tab(url):
        raise RuntimeError("No web browser could be opened.")
    return url
