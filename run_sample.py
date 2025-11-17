from fetch_news import fetch_from_newsapi
from storage import load_articles, save_articles
from preprocess import clean_html
from timeline import build_candidate_milestones, assemble_timeline

query = "Chandrayaan-3"

print("Loading cached articles (if any)...")
articles = load_articles(query)

if not articles:
    print("No cache found. Fetching fresh articles...")
    articles = fetch_from_newsapi(query, page_size=5)
    save_articles(query, articles)
else:
    print("Loaded articles from cache.")

# Clean
for a in articles:
    a["content"] = clean_html(a.get("content",""))

candidates = build_candidate_milestones(articles)
timeline = assemble_timeline(candidates)

print("\n=== Timeline Output ===")
print(timeline)
