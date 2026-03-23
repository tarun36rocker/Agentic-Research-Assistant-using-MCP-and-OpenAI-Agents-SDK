import requests
import os

def search_serper(query):
    url = "https://google.serper.dev/search"

    payload = {"q": query}
    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    results = res.json()

    return [r["link"] for r in results.get("organic", [])]