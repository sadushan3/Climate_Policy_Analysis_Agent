from models.models import PolicyAnalysis
from typing import List, Dict, Tuple
import re

class PolicySection:
    def __init__(self):
        self.title = ""
        self.content = ""
        self.keywords = set()
        self.topics = []
        self.climate_factors = {
            'temperature_impact': 0.0,  # -1 to 1 scale
            'humidity_impact': 0.0,     # -1 to 1 scale
            'wind_impact': 0.0,         # -1 to 1 scale
            'affected_regions': set()    # Set of locations mentioned
        }

class ExtractedPolicies:
    def __init__(self):
        self.policy1: PolicySection = PolicySection()
        self.policy2: PolicySection = PolicySection()
        self.shared_keywords: List[str] = []
        self.analysis: PolicyAnalysis = PolicyAnalysis()

async def split_into_policies(text: str, nlp) -> ExtractedPolicies:
    """
    Split a document into two distinct policy sections and analyze them.
    """
    result = ExtractedPolicies()
    sections = text.split('\n\n')  # Split by double newline to separate major sections
    
    # Find sections that look like policy statements
    policy_sections = []
    for section in sections:
        if any(keyword in section.lower() for keyword in [
            'policy', 'regulation', 'law', 'act', 'strategy', 'plan',
            'framework', 'guidance', 'directive', 'measure']):
            policy_sections.append(section)
    
    # If we found policy sections, use them; otherwise split the text in half
    if len(policy_sections) >= 2:
        result.policy1.content = policy_sections[0]
        result.policy2.content = '\n'.join(policy_sections[1:])
    else:
        # Split text roughly in half at sentence boundary
        sentences = re.split(r'(?<=[.!?])\s+', text)
        mid = len(sentences) // 2
        result.policy1.content = ' '.join(sentences[:mid])
        result.policy2.content = ' '.join(sentences[mid:])
    
    # Extract keywords and topics for each policy
    for policy in [result.policy1, result.policy2]:
        doc = nlp(policy.content)
        # Extract key phrases and entities
        policy.keywords = {token.text.lower() for token in doc if not token.is_stop and token.is_alpha}
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'GPE', 'DATE', 'MONEY']:
                policy.keywords.add(ent.text.lower())
    
    # Find shared keywords
    result.shared_keywords = list(result.policy1.keywords & result.policy2.keywords)
    
    # Analyze climate impacts for each policy
    for policy in [result.policy1, result.policy2]:
        # Extract temperature impact
        if any(word in policy.content.lower() for word in ['temperature', 'warming', 'heat', 'cooling', 'thermal']):
            temp_indicators = sum(1 for word in ['increase', 'rise', 'higher', 'hot'] if word in policy.content.lower())
            temp_indicators -= sum(1 for word in ['decrease', 'reduce', 'lower', 'cool'] if word in policy.content.lower())
            policy.climate_factors['temperature_impact'] = max(min(temp_indicators / 3, 1.0), -1.0)

        # Extract humidity impact
        if any(word in policy.content.lower() for word in ['humidity', 'moisture', 'precipitation', 'rainfall']):
            humid_indicators = sum(1 for word in ['increase', 'more', 'higher', 'wet'] if word in policy.content.lower())
            humid_indicators -= sum(1 for word in ['decrease', 'less', 'lower', 'dry'] if word in policy.content.lower())
            policy.climate_factors['humidity_impact'] = max(min(humid_indicators / 3, 1.0), -1.0)

        # Extract wind impact
        if any(word in policy.content.lower() for word in ['wind', 'breeze', 'gust', 'storm']):
            wind_indicators = sum(1 for word in ['increase', 'strong', 'higher', 'severe'] if word in policy.content.lower())
            wind_indicators -= sum(1 for word in ['decrease', 'weak', 'lower', 'mild'] if word in policy.content.lower())
            policy.climate_factors['wind_impact'] = max(min(wind_indicators / 3, 1.0), -1.0)

        # Extract affected regions
        doc = nlp(policy.content)
        for ent in doc.ents:
            if ent.label_ == 'GPE':  # Geographical/Political Entity
                policy.climate_factors['affected_regions'].add(ent.text)
    
    # Analyze the complete document
    result.analysis = await analyze_document(text, nlp)
    
    return result

async def analyze_document(text: str, nlp) -> PolicyAnalysis:
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

async def summarize_text(text: str, summarizer, max_length: int = 120, min_length: int = 40) -> str:
    """
    Summarize long text into a concise policy summary.
    """
    # Truncate if text is very long
    text = text[:4000]  # Allow longer input for better context
    result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return result[0]['summary_text']

async def extract_entities(text: str, nlp) -> list:
    """
    Extract named entities like Dates, Orgs, Countries, Numbers, etc.
    """
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})
    return entities