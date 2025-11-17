import re

def expand_query_dynamically(query: str):
    """
    Dynamically expands user queries to maximize NewsAPI relevance.
    Works for ANY topic without hardcoding keywords.
    """

    q = query.strip()

    # 1) Remove problematic year-only searches
    m = re.findall(r"\b(19\d{2}|20\d{2})\b", q)
    year = m[0] if m else None

    # 2) Break query into keywords
    keywords = re.findall(r"[A-Za-z0-9]+", q)

    # Too short query → return as is
    if len(keywords) <= 1:
        return q

    # 3) Build (keyword1 OR keyword2 OR keyword3...) structure
    keyword_or = " OR ".join([f'"{k}"' for k in keywords])

    # 4) If year is present, add it as required
    if year:
        expanded = f"({keyword_or}) AND {year}"
    else:
        expanded = f"({keyword_or})"

    return expanded
