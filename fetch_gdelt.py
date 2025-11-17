# fetch_gdelt.py
import requests
from datetime import datetime
import logging

# optional: configure logging to file or stdout
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

GDELT_DOC_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def _safe_json(resp):
    try:
        return resp.json()
    except ValueError:
        # not valid json
        return None

def fetch_from_gdelt(keyword, max_results=12, timeout=20):
    """
    Fetch news from GDELT v2 (artlist mode).
    Returns list of article dicts: title, publishedAt, content, url, source
    If anything goes wrong returns [] (empty list).
    """

    params = {
        "query": keyword,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_results,
        "sort": "date"
    }

    try:
        resp = requests.get(GDELT_DOC_URL, params=params, timeout=timeout)
    except requests.RequestException as e:
        logging.error("Network error when calling GDELT: %s", e)
        return []

    logging.info("GDELT status: %s URL: %s", resp.status_code, resp.url)

    # Quick checks for non-200 responses
    if resp.status_code != 200:
        logging.error("GDELT returned non-200 status: %s", resp.status_code)
        # log a short snippet of body for debugging
        text = resp.text or ""
        logging.error("GDELT body (first 1000 chars): %s", text[:1000])
        return []

    data = _safe_json(resp)
    if not data:
        logging.error("GDELT response not JSON. Body (first 2000 chars):\n%s", resp.text[:2000])
        return []

    # GDELT's artlist response should include 'articles'
    articles = data.get("articles") or data.get("articleslist") or data.get("data") or None
    if not articles:
        # If schema unknown, try to inspect keys for potential list
        logging.warning("GDELT JSON keys: %s", list(data.keys()))
        # fallback: attempt to find any list in top-level values with dict items that look like articles
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                articles = v
                break

    if not articles:
        logging.error("No 'articles' found in GDELT response.")
        return []

    results = []
    for art in articles[:max_results]:
        # GDELT fields vary; be defensive
        title = art.get("title") or art.get("seentitle") or art.get("title_full") or ""
        published = art.get("seendate") or art.get("date") or art.get("published") or ""
        excerpt = art.get("excerpt") or art.get("body") or art.get("snippet") or ""
        url = art.get("url") or art.get("sourceurl") or ""
        domain = art.get("domain") or art.get("domainname") or ""

        results.append({
            "title": title,
            "publishedAt": published,
            "content": excerpt,
            "url": url,
            "source": domain
        })

    return results

