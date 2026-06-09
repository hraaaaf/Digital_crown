import re
from typing import Any

def anonymize_text(text: str) -> str:
    if not isinstance(text, str):
        return text
        
    # Masquer les numéros de dossiers (ex: P-123456)
    text = re.sub(r'\bP-\d+\b', '[DOSSIER]', text, flags=re.IGNORECASE)
    
    # Masquer les téléphones (marocains ou autres)
    text = re.sub(r'(?:(?:\+|00)212|0)\s*[5-7](?:\s*\d{2}){4}', '[TELEPHONE]', text)
    
    # Masquer les emails
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL]', text)
    
    # Masquer les noms après certains préfixes
    text = re.sub(r'(Patient|Mr|Mme|M\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', r'\1 [NOM]', text)
    
    return text

def anonymize_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {k: anonymize_payload(v) for k, v in payload.items()}
    elif isinstance(payload, list):
        return [anonymize_payload(i) for i in payload]
    elif isinstance(payload, str):
        return anonymize_text(payload)
    else:
        return payload
