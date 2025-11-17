# fetch_news.py
import os
import requests
from dotenv import load_dotenv
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
from query_expander import expand_query_dynamically

load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def fetch_from_newsapi(query, page_size=10):
    expanded_query = expand_query_dynamically(query)

    url = (
        "https://newsapi.org/v2/everything?"
        f"q={expanded_query}&"
        "searchIn=title,description&"
        "sortBy=relevancy&"
        f"pageSize={page_size}&"
        f"apiKey={NEWSAPI_KEY}"
    )

    r = requests.get(url)
    data = r.json()

    if data.get("status") != "ok":
        print("NEWSAPI ERROR:", data)
        return []

    articles = []
    for a in data.get("articles", []):
        articles.append({
            "title": a.get("title"),
            "content": a.get("content") or a.get("description", ""),
            "url": a.get("url"),
            "source": a.get("source", {}).get("name"),
            "publishedAt": a.get("publishedAt")
        })

    return articles


def fetch_from_rss(feed_url, max_items=5):
    feed = feedparser.parse(feed_url)
    results = []
    for entry in feed.entries[:max_items]:
        title = entry.get('title')
        link = entry.get('link')
        published = entry.get('published') or entry.get('updated') or ''
        # try to fetch content for more text
        try:
            r = requests.get(link, timeout=8)
            soup = BeautifulSoup(r.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)[:3000]
        except Exception:
            text = entry.get('summary', '')[:3000]
        source = urlparse(link).netloc
        results.append({
            'title': title,
            'publishedAt': published,
            'content': text,
            'url': link,
            'source': source
        })
    return results

if __name__ == "__main__":
    print(fetch_from_newsapi("Chandrayaan-3", 3))
