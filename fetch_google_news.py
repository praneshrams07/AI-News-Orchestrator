import feedparser
import html
import urllib.parse

def fetch_google_news(query, max_results=10):
    """
    Fetches news from Google News RSS (free, unrestricted)
    """

    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    feed = feedparser.parse(url)

    articles = []
    for entry in feed.entries[:max_results]:
        articles.append({
            "title": html.unescape(entry.title),
            "content": html.unescape(entry.summary),
            "publishedAt": entry.get("published", ""),
            "url": entry.link,
            "source": entry.get("source", {}).get("title", "Google News")
        })

    return articles
