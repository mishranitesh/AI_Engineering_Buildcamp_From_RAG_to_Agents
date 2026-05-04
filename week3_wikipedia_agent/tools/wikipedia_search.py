import requests

HEADERS = {
    "User-Agent": "ai-engineering-buildcamp/1.0"
}


def search_wikipedia(query: str):
    print(f"[TOOL CALL] search_wikipedia: {query}")
    query = query.replace(" ", "+")

    url = (
        "https://en.wikipedia.org/w/api.php"
        f"?action=query&format=json&list=search&srsearch={query}"
    )

    response = requests.get(url, headers=HEADERS)

    return response.json()