# --------------------------------------
# app.py — AI News Orchestrator (No Cache)
# --------------------------------------
import streamlit as st
import json, re

from fetch_news import fetch_from_newsapi
from fetch_gdelt import fetch_from_gdelt
from fetch_google_news import fetch_google_news
from fetch_wikipedia import fetch_wikipedia_page

from preprocess import clean_html, parse_gdelt_date, smart_filter_articles
from nlp import annotate_event_text

from llm_service import (
    batch_timeline_and_summary,
    batch_evaluate_link_authenticity,
    batch_check_discrepancies
)


# --------------------------------------
# NO-CACHE MODE (overwrite load/save)
# --------------------------------------
def load_articles(query):
    return None   # ALWAYS fetch fresh

def save_articles(query, articles):
    pass  # Do nothing (disabled cache)


# --------------------------------------
# YEAR DETECTION
# --------------------------------------
def extract_year(query):
    years = re.findall(r"\b(19\d{2}|20\d{2})\b", query)
    return int(years[0]) if years else None


# --------------------------------------
# RENDER SUMMARY CARD
# --------------------------------------
def render_summary_card(query, articles):
    st.title("📰 AI News Orchestrator — Summary Card")
    st.write(f"### Topic: **{query}**")

    # Use max 20 articles for LLM stability
    articles_llm = articles[:20]

    # ---------------------------
    # 1️⃣ TIMELINE + SUMMARY (Batch)
    # ---------------------------
    st.info("⏳ Building timeline + summary...")
    try:
        result = batch_timeline_and_summary(articles_llm, query=query)
        timeline = result.get("timeline", [])
        summary = result.get("summary", "")
    except Exception as e:
        st.error(f"Timeline/summary generation failed: {e}")
        timeline, summary = [], "Summary unavailable."

    # ---------------------------
    # 2️⃣ AUTHENTICITY (Batch)
    # ---------------------------
    st.info("⏳ Evaluating credibility...")
    try:
        auth_results = batch_evaluate_link_authenticity(articles_llm)
    except Exception as e:
        st.warning(f"Credibility scoring failed: {e}")
        auth_results = []

    auth_map = {r.get("url",""): r for r in auth_results}

    per_link_scores = []
    for a in articles_llm:
        r = auth_map.get(a.get("url",""), {})
        score = float(r.get("credibility_score", 0.6))
        per_link_scores.append(score)

    overall_score = sum(per_link_scores)/len(per_link_scores) if per_link_scores else 0.6


    # ---------------------------
    # 3️⃣ TIMELINE RENDERING
    # ---------------------------
    st.markdown("## 🧠 Timeline and Summary")
    st.markdown("### 📅 Chronological Timeline")

    grouped = {}
    for t in timeline:
        date = t.get("date", "Unknown")
        grouped.setdefault(date, []).append(t.get("event",""))

    for date in sorted(grouped.keys()):
        st.markdown(f"#### 📌 **{date}**")
        for ev in grouped[date]:
            st.markdown(f"- {ev}")
        st.write("")


    # ---------------------------
    # 4️⃣ SUMMARY BOX
    # ---------------------------
    st.markdown("### 📝 Detailed Summary")
    st.markdown(
        f"""
        <div style="
            padding:18px;
            background:#eef2ff;
            border-radius:10px;
            font-size:16px;
            line-height:1.7;
        ">
            {summary}
        </div>
        """,
        unsafe_allow_html=True
    )


    # ---------------------------
    # 5️⃣ DISCREPANCY CHECK (Batch)
    # ---------------------------
    st.markdown("---")
    st.markdown("## ⚠️ Fact Consistency Checker")

    st.info("⏳ Checking inconsistencies across sources...")
    try:
        discrepancies = batch_check_discrepancies(timeline, articles_llm)
    except Exception as e:
        st.warning(f"Discrepancy analysis failed: {e}")
        discrepancies = []

    for item in discrepancies:
        title = item.get("event","")[:60]
        with st.expander(f"Check: {title}..."):
            st.write("### Consistent?", item.get("is_consistent"))
            
            if item.get("agreement_points"):
                st.success("Agreement Across Sources:")
                for p in item["agreement_points"]:
                    st.write(f"- {p}")

            if item.get("discrepancies"):
                st.error("Conflicting Claims:")
                for p in item["discrepancies"]:
                    st.write(f"- {p}")

            st.write("**Severity:**", item.get("severity","N/A"))


    # ---------------------------
    # 6️⃣ SOURCES LIST
    # ---------------------------
    st.markdown("---")
    st.markdown("## 🔗 Sources Used")

    for idx, art in enumerate(articles_llm):
        score = per_link_scores[idx]
        st.markdown(
            f"""
            <div style="padding:10px; margin-bottom:8px; border:1px solid #ddd; border-radius:6px;">
                <b>{art.get('title','')}</b><br>
                <small>{art.get('source','')} — {art.get('publishedAt','')}</small><br>
                <a href="{art.get('url','')}" target="_blank">Open Article</a><br><br>
                <b>Credibility Score:</b> {score:.2f}
            </div>
            """,
            unsafe_allow_html=True
        )


    # ---------------------------
    # 7️⃣ OVERALL SCORE
    # ---------------------------
    st.markdown("---")
    st.markdown("## 🔍 Overall Authenticity Score")
    st.metric("Event Authenticity", f"{overall_score:.2f}")

    if overall_score >= 0.8:
        st.success("High Confidence")
    elif overall_score >= 0.6:
        st.warning("Moderate Confidence")
    else:
        st.error("Low Confidence")


# --------------------------------------
# MAIN APP UI
# --------------------------------------
st.set_page_config(page_title="AI News Orchestrator", layout="wide")
st.title("📰 AI News Orchestrator")
st.write("Generate timeline + summary + authenticity + fact-check consistency.")


query = st.text_input("Enter an event or topic:", "Chandrayaan-3")


if st.button("Generate Summary Card"):

    # No cache: always fetch fresh
    articles = None

    year = extract_year(query)

    if year and year <= 2021:
        st.info("Using Wikipedia for historical events...")
        try:
            articles = fetch_wikipedia_page(query)
        except Exception as e:
            st.error(f"Wikipedia error: {e}")
            st.stop()
    else:
        st.info("Searching Google News…")
        articles = fetch_google_news(query, max_results=15)

        if not articles:
            st.warning("Google News empty → trying GDELT…")
            articles = fetch_from_gdelt(query, max_results=12)

        if not articles:
            st.warning("GDELT failed → trying NewsAPI…")
            articles = fetch_from_newsapi(query, page_size=10)

    if not articles:
        st.error("No articles found from any source.")
        st.stop()


    # CLEAN + NORMALIZE
    for a in articles:
        a["content"] = clean_html(a.get("content","") or "")
        a["entities"] = annotate_event_text(a["content"])
        if len(a.get("publishedAt","")) == 14:
            a["publishedAt"] = parse_gdelt_date(a["publishedAt"])

    # SMART FILTER
    articles = smart_filter_articles(query, articles)

    # RENDER
    render_summary_card(query, articles)








