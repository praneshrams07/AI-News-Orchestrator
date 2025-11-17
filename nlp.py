# nlp.py
import spacy
from dateparser import parse as parse_date

nlp = spacy.load("en_core_web_sm")

def extract_entities(text: str):
    doc = nlp(text)
    return [{"text": e.text, "label": e.label_} for e in doc.ents]

def extract_dates_from_text(text: str):
    doc = nlp(text)
    dates = []
    for ent in doc.ents:
        if ent.label_ in ("DATE", "TIME"):
            d = parse_date(ent.text)
            if d:
                dates.append(d.date().isoformat())
    return sorted(list(set(dates)))

def annotate_event_text(text):
    doc = nlp(text)
    ents = [{'text': e.text, 'label': e.label_} for e in doc.ents]
    return ents
