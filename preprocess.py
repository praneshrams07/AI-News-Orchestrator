# preprocess.py
import re
from bs4 import BeautifulSoup
from datetime import datetime

# ---------------------------------------------------
# 1. Clean HTML Content
# ---------------------------------------------------
def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text


# ---------------------------------------------------
# 2. Hard Filtering (Exact keyword relevance)
# ---------------------------------------------------
def filter_articles_by_query(query, articles):
    """
    Strict keyword-based filtering for historical topics.
    Keeps articles only if they contain enough words from the query.
    """
    query_words = query.lower().split()
    filtered = []

    for art in articles:
        content = (art.get("title", "") + " " + art.get("content", "")).lower()
        score = sum(1 for q in query_words if q in content)

        # Keep article if it matches 50% of query words
        if score >= max(1, len(query_words) / 2):
            filtered.append(art)

    return filtered if filtered else articles


# ---------------------------------------------------
# 3. Smart Filtering (No LLM calls — avoids quota usage)
# ---------------------------------------------------
def smart_filter_articles(query, articles):
    """
    Lightweight smart filtering WITHOUT LLM.
    Uses:
    - keyword match
    - year detection
    - event name similarity
    """

    query_l = query.lower()
    query_words = query_l.split()

    def is_relevant(article):
        text = (article.get("title", "") + " " + article.get("content", "")).lower()

        # Strong keyword match
        keyword_hits = sum(1 for w in query_words if w in text)

        # If query contains a year, enforce it
        year = None
        for part in query_words:
            if part.isdigit() and len(part) == 4:
                year = part

        if year and year not in text:
            return False

        # Basic relevance threshold
        return keyword_hits >= 1

    filtered = [a for a in articles if is_relevant(a)]
    return filtered if filtered else articles  # fallback


# ---------------------------------------------------
# 4. GDELT Date Parser
# ---------------------------------------------------
def parse_gdelt_date(dt):
    try:
        return datetime.strptime(dt, "%Y%m%d%H%M%S").strftime("%Y-%m-%d")
    except:
        return dt

