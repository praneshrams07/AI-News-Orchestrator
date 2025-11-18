# llm_service.py (FINAL — Streamlit Deploy Safe, .env + secrets supported)

import json
import re
import time
import os
from typing import List, Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv


# ---------------------------------------------------
# Load .env (local only)
# ---------------------------------------------------
load_dotenv()


# ---------------------------------------------------
# Load API Key (Streamlit Cloud → .env fallback)
# ---------------------------------------------------
def load_gemini_key():
    """
    Load GEMINI_API_KEY safely for both Streamlit Cloud and local dev.
    NOTE: Do NOT use streamlit inside this file (safe-import rule).
    """
    key = None

    # 1) Try Streamlit secrets (inside app.py)
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY", None)
    except:
        pass

    # 2) Local .env
    if not key:
        key = os.getenv("GEMINI_API_KEY")

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY missing. "
            "Add it to Streamlit secrets OR create a .env file."
        )

    return key


API_KEY = load_gemini_key()
genai.configure(api_key=API_KEY)


GENIE_MODEL = "models/gemini-2.0-flash"


# ---------------------------------------------------
# Retry wrapper
# ---------------------------------------------------
def retry_on_rate_limit(max_retries=5, backoff_factor=1.6, initial_wait=1.0):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            wait = initial_wait
            for attempt in range(max_retries):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    msg = str(e).lower()
                    is_rate = any(x in msg for x in ["quota", "429", "rate", "resourceexhausted"])
                    if attempt == max_retries - 1 or not is_rate:
                        raise
                    time.sleep(wait)
                    wait *= backoff_factor
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------
# Helpers
# ---------------------------------------------------
def _normalize_text(text: str, max_len=32000):
    if not text:
        return ""
    return text.strip()[:max_len]


def clean_timeline_json(raw: str) -> List[Dict[str, Any]]:
    if not raw:
        return []

    cleaned = raw.replace("```json", "").replace("```", "")
    arr_match = re.search(r"(\[[\s\S]*?\])", cleaned)

    if not arr_match:
        return []

    try:
        arr = json.loads(arr_match.group(1))
    except:
        return []

    final = []
    for item in arr:
        if not isinstance(item, dict):
            continue

        date = item.get("date", "Unknown")
        event = item.get("event", "").strip()
        date = re.sub(r"[^0-9\-]", "-", date)[:10]

        if event:
            final.append({"date": date, "event": event})

    return final


# ---------------------------------------------------
# 1) TIMELINE + SUMMARY (batch)
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_timeline_and_summary(articles: List[Dict[str, Any]], query: str = "") -> Dict[str, Any]:

    compact = []
    for a in articles[:20]:
        compact.append({
            "title": _normalize_text(a.get("title", "")),
            "publishedAt": a.get("publishedAt", ""),
            "source": a.get("source", ""),
            "url": a.get("url", ""),
            "content": _normalize_text(a.get("content", ""), max_len=1500),
        })

    payload = json.dumps(compact, ensure_ascii=False, indent=2)

    prompt = f"""
You are an expert event analyst.

1) Build a chronological JSON timeline:
   Format: {{"date":"YYYY-MM-DD","event":"..."}}

2) Write a 3–6 sentence detailed summary paragraph.

Return ONLY:
{{
 "timeline": [...],
 "summary": "..."
}}

QUERY = "{query}"

ARTICLES:
{payload}
    """

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    text = resp.text or ""

    obj_match = re.search(r"(\{[\s\S]*\})", text)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(1))
            raw_tl = json.dumps(parsed.get("timeline", []))
            cleaned_tl = clean_timeline_json(raw_tl)
            summary = parsed.get("summary", "").strip()
            return {"timeline": cleaned_tl, "summary": summary}
        except:
            pass

    # fallback
    return {
        "timeline": clean_timeline_json(text),
        "summary": text.strip()
    }


# ---------------------------------------------------
# 2) LINK CREDIBILITY (batch)
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_evaluate_link_authenticity(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    compact = []
    for a in articles[:30]:
        compact.append({
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "publishedAt": a.get("publishedAt", ""),
            "snippet": _normalize_text(a.get("content", ""), max_len=800)
        })

    payload = json.dumps(compact, ensure_ascii=False, indent=2)

    prompt = f"""
For each article return JSON:
{{
  "url": "...",
  "credibility_score": 0.0-1.0,
  "authenticity_label": "...",
  "bias_label": "...",
  "reasoning": "..."
}}
Return ONLY a JSON array.
ARTICLES:
{payload}
"""

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    raw = resp.text or ""

    try:
        return json.loads(re.search(r"(\[[\s\S]*\])", raw).group(1))
    except:
        pass

    # fallback neutral
    return [
        {
            "url": a.get("url", ""),
            "credibility_score": 0.6,
            "authenticity_label": "unknown",
            "bias_label": "unknown",
            "reasoning": "Parsing failed."
        }
        for a in articles[:30]
    ]


# ---------------------------------------------------
# 3) DISCREPANCY CHECK
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_check_discrepancies(timeline, articles):

    t_json = json.dumps(timeline, indent=2, ensure_ascii=False)
    a_json = json.dumps([
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "publishedAt": a.get("publishedAt", ""),
            "snippet": _normalize_text(a.get("content", ""), max_len=800)
        }
        for a in articles[:30]
    ], indent=2, ensure_ascii=False)

    prompt = f"""
For each timeline event return:
- is_consistent
- agreement_points
- discrepancies
- severity
Return ONLY a JSON array.
TIMELINE:
{t_json}
ARTICLES:
{a_json}
"""

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    raw = resp.text or ""

    try:
        return json.loads(re.search(r"(\[[\s\S]*\])", raw).group(1))
    except:
        pass

    return [
        {
            "date": t.get("date"),
            "event": t.get("event"),
            "is_consistent": False,
            "agreement_points": [],
            "discrepancies": ["Parsing error"],
            "severity": "medium"
        }
        for t in timeline
    ]









