import requests

HEADERS = {
    "User-Agent": "ai-engineering-buildcamp/1.0"
}


def get_page(title: str):
    print(f"[TOOL CALL] get_page: {title}")
    title = title.replace(" ", "_")

    url = (
        "https://en.wikipedia.org/w/index.php"
        f"?title={title}&action=raw"
    )

    response = requests.get(url, headers=HEADERS)

    return response.text