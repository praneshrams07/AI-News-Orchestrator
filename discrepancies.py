# discrepancies.py
import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def clean_json(raw):
    """
    Clean Gemini output and return parsed JSON.
    """
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except:
        return {}


def check_event_discrepancies(event_item, articles):
    """
    Use Gemini to determine if multiple articles contain inconsistent facts
    about the same event.
    """

    prompt = (
        "You are an expert analyst comparing information across news articles.\n"
        "Determine whether different sources agree or conflict on this event.\n\n"
        "EVENT:\n"
        f"{event_item}\n\n"
        "ARTICLES:\n"
        f"{articles}\n\n"
        "TASK:\n"
        "Identify factual consistency or contradictions. Compare:\n"
        "- Numbers (e.g., death tolls, prices, counts)\n"
        "- Dates reported\n"
        "- Claims about outcomes\n"
        "- Differing descriptions of the same event\n\n"
        "Return ONLY VALID JSON in this format:\n"
        "{\n"
        "  \"is_consistent\": true | false,\n"
        "  \"discrepancies\": [\"list of mismatches\"],\n"
        "  \"agreement_points\": [\"list of common facts\"],\n"
        "  \"severity\": \"low\" | \"medium\" | \"high\"\n"
        "}\n"
        "Return JSON only."
    )

    model = genai.GenerativeModel("models/gemini-2.5-flash")

    response = model.generate_content(prompt)
    return response.text or "{}"


