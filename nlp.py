# nlp.py — Streamlit-safe lightweight NER

from transformers import pipeline
from dateparser import parse as parse_date

# Load lightweight NER model (works on Streamlit Cloud)
ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")

def extract_entities(text: str):
    if not text:
        return []
    result = ner(text)
    return [{"text": ent["word"], "label": ent["entity_group"]} for ent in result]

def extract_dates_from_text(text: str):
    if not text:
        return []
    result = ner(text)
    dates = []
    for ent in result:
        if ent["entity_group"] in ("DATE", "TIME"):
            d = parse_date(ent["word"])
            if d:
                dates.append(d.date().isoformat())
    return sorted(list(set(dates)))

def annotate_event_text(text):
    if not text:
        return []
    result = ner(text)
    return [{"text": ent["word"], "label": ent["entity_group"]} for ent in result]

