# timeline.py
from collections import defaultdict
from dateutil import parser

def build_candidate_milestones(articles):
    import re
    triggers = ['announce','launch','land','arrive','confirm','reach','declare','resign','investigate','file','deploy']
    candidates = []
    for a in articles:
        content = a.get("content","") or ""
        sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', content) if s.strip()]
        for s in sents:
            if any(k in s.lower() for k in triggers):
                candidates.append({"sentence": s, "publishedAt": a.get("publishedAt"), "source": a.get("source"), "url": a.get("url")})
    return candidates

def assemble_timeline(candidates):
    by_date = defaultdict(list)
    for c in candidates:
        try:
            d = parser.isoparse(c.get("publishedAt")).date().isoformat()
        except Exception:
            d = "unknown"
        by_date[d].append(c)
    timeline = []
    for d in sorted([k for k in by_date.keys() if k != "unknown"]):
        timeline.append({"date": d, "events": by_date[d]})
    if "unknown" in by_date:
        timeline.append({"date": "unknown", "events": by_date["unknown"]})
    return timeline
