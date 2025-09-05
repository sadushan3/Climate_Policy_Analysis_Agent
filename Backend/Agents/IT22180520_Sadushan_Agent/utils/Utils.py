import re

def sanitize_text(text: str) -> str:
    """ Remove unwanted characters to prevent injection """
    return re.sub(r'[^a-zA-Z0-9\s.,;:!?()-]', '', text)

def validate_policy_input(text: str) -> bool:
    """ Ensure policy input is not empty or malicious """
    if not text or len(text.strip()) < 10:
        return False
    return True