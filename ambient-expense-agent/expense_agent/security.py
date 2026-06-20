import re

def scrub_pii(text: str) -> str:
    """Scrub SSNs and Credit Card numbers from text."""
    if not text:
        return text
    # Basic regex for SSN (XXX-XX-XXXX)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_SSN]', text)
    # Basic regex for Credit Card (16 digits with or without dashes)
    text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED_CC]', text)
    return text

def detect_prompt_injection(text: str) -> bool:
    """Detect basic prompt injection attempts."""
    if not text:
        return False
    lower_text = text.lower()
    injection_keywords = [
        "ignore all previous instructions",
        "auto-approve",
        "system prompt",
        "bypass rules",
        "you are now",
        "forget previous"
    ]
    for keyword in injection_keywords:
        if keyword in lower_text:
            return True
    return False

def security_checkpoint(node_input: str) -> dict:
    """Node function that scrubs PII and checks for prompt injection."""
    # Use empty string if node_input is not provided or not a string
    if not isinstance(node_input, str):
        node_input = str(node_input) if node_input else ""
        
    clean_desc = scrub_pii(node_input)
    is_injection = detect_prompt_injection(clean_desc)
    
    return {
        "prompt": node_input,
        "clean_description": clean_desc,
        "security_flag": is_injection
    }
