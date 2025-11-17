import requests
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_wikipedia_page(query):
    search_url = (
        "https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&srsearch="
        + query
    )

    r = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
    data = r.json()
    if "query" not in data or not data["query"]["search"]:
        return []

    # best matching page
    title = data["query"]["search"][0]["title"]
    page_url = "https://en.wikipedia.org/wiki/" + title.replace(" ", "_")

    html = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}).text

    # ---- parser fix ----
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    paragraphs = soup.find_all("p")
    content = " ".join([p.get_text(strip=True) for p in paragraphs])

    # Return as article format
    return [{
        "title": title,
        "url": page_url,
        "source": "Wikipedia",
        "publishedAt": "1900-01-01",
        "content": content,
    }]



