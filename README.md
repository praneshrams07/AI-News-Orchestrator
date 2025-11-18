# 📰 AI News Orchestrator (Google News + GDELT + Wikipedia + Gemini)
# Stereamlit link: https://ai-news-orchestrator-xzdtr696dydbwzuwxmdqff.streamlit.app/

An end-to-end AI-powered news reconstruction system that fetches articles from multiple sources, builds a chronological timeline, generates a detailed summary, evaluates article credibility, and checks for cross-source factual consistency — all inside a clean Streamlit interface.

---

## 🚀 Features

* 🔎 Multi-source news fetching (Google News RSS → GDELT → NewsAPI → Wikipedia fallback)
* 🧠 AI Timeline Reconstruction (Gemini 2.5 Flash)
* 📝 Detailed Summary Paragraph (3–6 sentences)
* 📊 Credibility Scoring & Bias Detection
* ⚠️ Cross-Source Fact Consistency Checker
* 🚀 Batched LLM Calls (2–3x faster, fewer rate limits)
* 🎨 Clean & modern Streamlit UI
* 🔐 Safe secret management via `.streamlit/secrets.toml`

---

## 🏗️ Project Structure
```
AI-News-Orchestrator/│├── app.py                        → Main Streamlit UI├── llm_service.py                → Batched Gemini logic├── fetch_google_news.py          → Google News RSS scraper├── fetch_gdelt.py                → GDELT news fetcher├── fetch_wikipedia.py            → Wikipedia fetcher├── fetch_news.py                 → NewsAPI fallback│├── preprocess.py                 → HTML cleaner, date parser, filters├── nlp.py                        → Entity extraction (NER-lite)├── discrepancies.py              → Cross-source fact checker│├── requirements.txt              → Python dependencies├── .streamlit/│   └── secrets.toml              → API keys for Streamlit Cloud└── README.md
---
```
## ⚙️ Setup Instructions

### 1️⃣ Clone the repository
```bash
git clone [https://github.com/](https://github.com/)<your-username>/AI-News-Orchestrator.git
cd AI-News-Orchestrator
```
### 2️⃣ Create & activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```
### 3️⃣ Install dependencies
```Bash
pip install -r requirements.txt
```
### 4️⃣ API Key SetupLocal Environment
```Bash
export  GEMINI_API_KEY="your-api-key"
```
Streamlit Cloud (.streamlit/secrets.toml)Create the folder:
```Bash
mkdir -p .streamlit
```

Create the file and paste your key:Ini, TOML# .streamlit/secrets.toml
```Bash
GEMINI_API_KEY = "your-api-key"
```

### 5️⃣ Run the App Locally
```Bash
streamlit run app.py
```
## 🧠 How It Works (Pipeline)

**USER QUERY**
$\downarrow$
**NEWS FETCHING PIPELINE:**
Google News $\to$ GDELT $\to$ NewsAPI $\to$ Wikipedia
$\downarrow$
**PREPROCESSING** (clean HTML, fix dates, text normalization)
$\downarrow$
**LLM SERVICES (batched):**
- Timeline reconstruction
- Detailed summary generation
- Credibility scoring for each article
- Discrepancy analysis across sources
$\downarrow$
**STREAMLIT UI RENDERING**

### Example Output

> **Query:** “ICC Women's World Cup 2025”

- **📅 Chronological Timeline**
    - 2025-10-05 $\to$ Opening match
    - 2025-10-13 $\to$ Major group-stage win
    - 2025-11-03 $\to$ India wins the World Cup

- **📝 Detailed Summary**
    - A 5-sentence cohesive summary that describes how the tournament began, progressed through semis, turning points, standout players, and India's final victory.

- **🔍 Authenticity Score**
    - 0.83 — High Confidence

---

## 🧰 Built With

- Python
- Streamlit
- Google Gemini 2.5 Flash
- Google News RSS
- GDELT Project
- NewsAPI
- Wikipedia API
- BeautifulSoup4
- Requests

---

## 🚀 Deployment (Streamlit Cloud)

- 1.  Push your repo to **GitHub**.
- 2.  Open: `https://share.streamlit.io`
- 3.  Select your **repository**.
- 4.  Set main file $\to$ **`app.py`**
- 5.  Add secrets in Settings $\to$ **Secrets** (for `GEMINI_API_KEY`).
- 6.  Deploy 🎉

---

## ✨ Author
**Praneshram S**
