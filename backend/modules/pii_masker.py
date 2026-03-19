import re
from typing import Dict, Any

class PIIMasker:
    """Utility class to mask sensitive Indian PII data before passing to external LLMs."""

    PAN_PATTERN = re.compile(r'[A-Z]{5}[0-9]{4}[A-Z]{1}')
    GSTIN_PATTERN = re.compile(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}')
    AADHAAR_PATTERN = re.compile(r'\d{4}\s?\d{4}\s?\d{4}')
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_PATTERN = re.compile(r'(\+91[\-\s]?)?[6789]\d{9}')

    @classmethod
    def mask_text(cls, text: str) -> str:
        """Replace all identified PII with placeholder strings."""
        if not text or not isinstance(text, str):
            return text
        text = cls.PAN_PATTERN.sub('[MASKED_PAN]', text)
        text = cls.GSTIN_PATTERN.sub('[MASKED_GSTIN]', text)
        text = cls.AADHAAR_PATTERN.sub('[MASKED_AADHAAR]', text)
        text = cls.EMAIL_PATTERN.sub('[MASKED_EMAIL]', text)
        text = cls.PHONE_PATTERN.sub('[MASKED_PHONE]', text)
        return text

    @classmethod
    def mask_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask strings inside a dictionary payload."""
        masked_data = {}
        for k, v in data.items():
            if isinstance(v, str):
                masked_data[k] = cls.mask_text(v)
            elif isinstance(v, dict):
                masked_data[k] = cls.mask_dict(v)
            elif isinstance(v, list):
                masked_data[k] = [cls.mask_dict(i) if isinstance(i, dict) else cls.mask_text(i) if isinstance(i, str) else i for i in v]
            else:
                masked_data[k] = v
        return masked_data
