import re

def sanitize_text(text: str) -> str:
    """
    Remove special characters from text while preserving essential punctuation.
    """
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()-]', '', text)

def validate_policy_input(text: str) -> bool:
    """
    Validate if the policy text input meets minimum requirements.
    """
    if not text or len(text.strip()) < 10:
        return False
    return True