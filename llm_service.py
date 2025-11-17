# llm_service.py (FINAL PATCHED VERSION — NO genai.configure HERE)

import json
import re
import time
from typing import List, Dict, Any
import google.generativeai as genai   # configured in app.py, NOT here
import streamlit as st
import google.generativeai as genai

api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)



GENIE_MODEL = "models/gemini-2.5-flash"


# ---------------------------------------------------
# Retry wrapper (for rate limits)
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
                    rate_error = any(x in msg for x in ["quota", "429", "rate", "resourceexhausted"])
                    if not rate_error or attempt == max_retries - 1:
                        raise
                    time.sleep(wait)
                    wait *= backoff_factor
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------
# Helper: truncate long texts
# ---------------------------------------------------
def _normalize_text(text: str, max_len=32000):
    if not text:
        return ""
    text = text.strip()
    return text[:max_len]


# ---------------------------------------------------
# Helper: clean timeline array from messy LLM output
# ---------------------------------------------------
def clean_timeline_json(raw_text: str) -> List[Dict[str, Any]]:
    if not raw_text:
        return []

    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    cleaned = cleaned.replace("YYYY-MM-DD", "").replace('"YYYY-MM-DD"', "")

    # Try to extract array
    arr_match = re.search(r'(\[[\s\S]*?\])', cleaned, flags=re.DOTALL)
    if not arr_match:
        return []

    try:
        arr = json.loads(arr_match.group(1))
    except:
        return []

    timeline = []
    for item in arr:
        if not isinstance(item, dict):
            continue

        event = item.get("event") or item.get("description") or ""
        date = item.get("date") or item.get("publishedAt") or "Unknown"

        event = event.strip()
        date = date.strip()
        date = re.sub(r'[^0-9\-]', "-", date)[:10]

        if event:
            timeline.append({"date": date, "event": event})

    return timeline


# ---------------------------------------------------
# 1) BATCH TIMELINE + SUMMARY
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_timeline_and_summary(articles: List[Dict[str, Any]], query: str = "") -> Dict[str, Any]:

    # compact for prompt stability
    compact = []
    for a in articles[:20]:
        compact.append({
            "title": _normalize_text(a.get("title", ""))[:250],
            "publishedAt": a.get("publishedAt", ""),
            "source": a.get("source", ""),
            "url": a.get("url", ""),
            "content": _normalize_text(a.get("content", ""), max_len=1500),
        })

    payload = json.dumps(compact, ensure_ascii=False, indent=2)

    prompt = f"""
You are an expert event reconstruction analyst.

Given a set of articles about a single topic, do two things:

1. Construct a **chronological timeline** from beginning to end.
   - Output JSON array named "timeline"
   - Format each item as: {{"date":"YYYY-MM-DD","event":"one-sentence"}}
   - Best-effort date if missing, else use "Unknown"

2. Write a **single detailed paragraph summary** (3–6 sentences)
   describing the overall flow, causes, progression, turning points,
   and final outcome of the event.

Return ONLY a JSON object with keys "timeline" and "summary".

QUERY = "{query}"

ARTICLES JSON:
{payload}
"""

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    text = resp.text or ""

    # Extract JSON object
    obj_match = re.search(r'(\{[\s\S]*\})', text, flags=re.DOTALL)
    if obj_match:
        try:
            parsed = json.loads(obj_match.group(1))
            timeline_raw = parsed.get("timeline", [])
            summary = parsed.get("summary", "")
            timeline_clean = clean_timeline_json(json.dumps(timeline_raw))
            return {
                "timeline": timeline_clean,
                "summary": summary.strip()
            }
        except:
            pass

    # fallback: try only array + find summary
    timeline = clean_timeline_json(text)
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    summary = paragraphs[-1] if paragraphs else ""

    return {
        "timeline": timeline,
        "summary": summary.strip()
    }


# ---------------------------------------------------
# 2) BATCH CREDIBILITY CHECK
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_evaluate_link_authenticity(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not articles:
        return []

    compact = []
    for a in articles[:30]:
        compact.append({
            "title": _normalize_text(a.get("title", ""))[:150],
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "publishedAt": a.get("publishedAt", ""),
            "snippet": _normalize_text(a.get("content", ""), max_len=800)
        })
    payload = json.dumps(compact, ensure_ascii=False, indent=2)

    prompt = f"""
You are a news credibility analyst.

For each item in the array, output:
{{
  "url": "<same>",
  "credibility_score": 0.0-1.0,
  "authenticity_label": "credible" | "questionable" | "misleading",
  "bias_label": "neutral" | "left" | "right" | "sensational" | "unknown",
  "reasoning": "one sentence"
}}

Return ONLY a JSON array in the same order.

ARTICLES:
{payload}
"""

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    raw = resp.text or ""

    try:
        arr = json.loads(re.search(r'(\[[\s\S]*\])', raw).group(1))
        return arr
    except:
        pass

    # fallback defaults
    res = []
    for a in articles[:30]:
        res.append({
            "url": a.get("url", ""),
            "credibility_score": 0.6,
            "authenticity_label": "unknown",
            "bias_label": "unknown",
            "reasoning": "Model parsing failed."
        })
    return res


# ---------------------------------------------------
# 3) BATCH FACT CONSISTENCY CHECK
# ---------------------------------------------------
@retry_on_rate_limit()
def batch_check_discrepancies(timeline: List[Dict[str, Any]], articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not timeline:
        return []

    t_json = json.dumps(timeline, ensure_ascii=False, indent=2)

    a_compact = []
    for a in articles[:30]:
        a_compact.append({
            "title": _normalize_text(a.get("title", ""))[:200],
            "url": a.get("url", ""),
            "source": a.get("source", ""),
            "publishedAt": a.get("publishedAt", ""),
            "snippet": _normalize_text(a.get("content", ""), max_len=800)
        })
    a_json = json.dumps(a_compact, ensure_ascii=False, indent=2)

    prompt = f"""
You are a cross-source fact consistency evaluator.

Given:

TIMELINE:
{t_json}

ARTICLES:
{a_json}

For each timeline event, determine:
- is_consistent (true/false)
- agreement_points (list)
- discrepancies (list)
- severity: "low" | "medium" | "high"

Return ONLY a JSON array in the same order as the timeline.
"""

    model = genai.GenerativeModel(GENIE_MODEL)
    resp = model.generate_content(prompt)
    raw = resp.text or ""

    try:
        arr = json.loads(re.search(r'(\[[\s\S]*\])', raw).group(1))
        return arr
    except:
        pass

    # fallback
    output = []
    for t in timeline:
        output.append({
            "date": t.get("date"),
            "event": t.get("event"),
            "is_consistent": False,
            "agreement_points": [],
            "discrepancies": ["Unable to analyze due to parsing error."],
            "severity": "medium"
        })
    return output








