import re

def mask_pii(data: str, visible_chars: int = 4) -> str:
    """Masks Personally Identifiable Information (PII) for HIPAA/ABDM displays."""
    if not data:
        return ""
    if len(data) <= visible_chars:
        return "*" * len(data)
    
    return data[:visible_chars] + "*" * (len(data) - visible_chars)

def mask_email(email: str) -> str:
    """Masks email address like a***@domain.com."""
    if "@" not in email:
        return mask_pii(email)
    name, domain = email.split("@")
    return name[0] + "***@" + domain

def mask_phone(phone: str) -> str:
    """Masks phone number like ******1234."""
    if not phone:
        return ""
    return "*" * (max(0, len(phone) - 4)) + phone[-4:]

def censor_abha(abha: str) -> str:
    """Censor ABHA Identity."""
    return mask_pii(abha, visible_chars=2)
