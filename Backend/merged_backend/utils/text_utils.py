import re

def sanitize_text(text: str) -> str:

    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()-]', '', text)

def validate_policy_input(text: str) -> bool:
    
    if not text or len(text.strip()) < 10:
        return False
    return True