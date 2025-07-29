import webbrowser  

def open_web_url(web_name: str) -> str:
    web_urls = {
        "youtube": "https://www.youtube.com/",
        "hotstar": "https://www.hotstar.com/in/mypage",
        "chatgpt": "https://chatgpt.com/",
        "leetcode": "https://leetcode.com/problemset/",
        "github": "https://github.com/171801rohith",
    }

    url = web_urls.get(web_name.lower())

    if url:
        webbrowser.open_new_tab(url)
        return f"Successfully opened {web_name} at {url}"
    else:
        return f"Failed to open {web_name}. Browser did not open the URL."
