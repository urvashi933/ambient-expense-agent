import re

def scrub_pii(text: str) -> str:
    """Scrub SSNs, Credit Card numbers, Phone Numbers, and Emails from text."""
    if not text:
        return text
    
    # SSN: XXX-XX-XXXX or XXXXXXXXX
    text = re.sub(r'\b(?:\d[ -]*?){9}\b', '[REDACTED_SSN]', text)
    
    # Credit Card: 13-19 digits
    text = re.sub(r'\b(?:\d[ -]*?){13,19}\b', '[REDACTED_CC]', text)
    
    # US Phone Numbers
    text = re.sub(r'\b(?:\+?1[-. ]?)?\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})\b', '[REDACTED_PHONE]', text)
    
    # Emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[REDACTED_EMAIL]', text)
    
    return text

def detect_prompt_injection(text: str) -> bool:
    """Detect advanced prompt injection attempts using regex and keywords."""
    if not text:
        return False
    lower_text = text.lower()
    
    injection_patterns = [
        r'ignore (all )?(previous )?instructions',
        r'auto-approve',
        r'bypass (all )?(rules|instructions)',
        r'forget (all )?(previous )?instructions',
        r'system prompt',
        r'you are now',
        r'print (all )?(previous )?instructions',
        r'override (all )?(previous )?instructions',
        r'disregard',
        r'new instructions',
        r'act as',
        r'jailbreak',
        r'dan ', # Do anything now
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, lower_text):
            return True
            
    return False

def security_checkpoint(ctx, prompt: str):
    """Node function that scrubs PII and checks for prompt injection."""
    if not isinstance(prompt, str):
        prompt = str(prompt) if prompt else ""
        
    clean_desc = scrub_pii(prompt)
    is_injection = detect_prompt_injection(clean_desc)
    
    ctx.state["prompt"] = prompt
    ctx.state["clean_description"] = clean_desc
    ctx.state["security_flag"] = is_injection
    return clean_desc

