import re
import spacy
from transformers import pipeline
from models import PolicyAnalysis

# Load NLP models once
nlp = spacy.load("en_core_web_sm")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# -------------------------
# Policy Analysis
# -------------------------
def analyze_document(text: str) -> PolicyAnalysis:
    analysis = PolicyAnalysis()
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        s_lower = sentence.lower()

        # Mitigation Targets
        if any(word in s_lower for word in ["reduce emissions", "carbon neutral", "renewable", "net zero"]):
            analysis.Mitigation_Targets.append(sentence)

        # Adaptation Strategies
        if any(word in s_lower for word in ["resilience", "adaptation", "coastal protection", "climate-proof"]):
            analysis.Adaptation_Strategies.append(sentence)

        # Finance Commitments
        if any(word in s_lower for word in ["funding", "finance", "investment", "billion", "million usd"]):
            analysis.Finance_Commitments.append(sentence)

        # Legislation / Policies
        if any(word in s_lower for word in ["act", "law", "policy", "framework", "regulation"]):
            analysis.Legislation_Policies.append(sentence)

        # Stakeholders
        if any(word in s_lower for word in ["government", "ministry", "organization", "ngo", "stakeholder"]):
            analysis.Stakeholders.append(sentence)

        # Targets & Timelines
        if re.search(r"\b(20[2-5][0-9])\b", sentence):
            analysis.Targets_Timelines.append(sentence)

        # Sectors Covered
        if any(word in s_lower for word in ["energy", "transport", "agriculture", "forestry", "waste", "industry"]):
            analysis.Sectors_Covered.append(sentence)

        # Monitoring & Reporting
        if any(word in s_lower for word in ["monitoring", "reporting", "verification", "mrv", "tracking progress"]):
            analysis.Monitoring_Reporting.append(sentence)

        # International Cooperation
        if any(word in s_lower for word in ["paris agreement", "unfccc", "bilateral", "international", "cooperation"]):
            analysis.International_Cooperation.append(sentence)

        # Institutional Arrangements
        if any(word in s_lower for word in ["committee", "council", "agency", "authority", "institution"]):
            analysis.Institutional_Arrangements.append(sentence)

        # Social & Community
        if any(word in s_lower for word in ["community", "indigenous", "gender", "health", "vulnerable"]):
            analysis.Social_Community.append(sentence)

        # Technology & Innovation
        if any(word in s_lower for word in ["technology", "innovation", "research", "development", "carbon capture", "hydrogen"]):
            analysis.Technology_Innovation.append(sentence)

    return analysis


# -------------------------
# Summarization
# -------------------------
def summarize_text(text: str, max_length: int = 120, min_length: int = 40) -> str:
    """
    Summarize long text into a concise policy summary.
    """
    # Truncate if text is very long
    text = text[:2000]
    result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return result[0]['summary_text']


# -------------------------
# Named Entity Recognition
# -------------------------
def extract_entities(text: str):
    """
    Extract named entities like Dates, Orgs, Countries, Numbers, etc.
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})
    return entities
