import re


def normalize_unicode(text: str) -> str:
    return text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')


def normalize_whitespace(text: str) -> str:
    if not text:
        return ""
    cleaned = normalize_unicode(text)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n +", "\n", cleaned)
    cleaned = re.sub(r" +\n", "\n", cleaned)
    return cleaned.strip()


def clean_resume_text(text: str) -> str:
    cleaned = normalize_whitespace(text)
    cleaned = re.sub(r"\u00a0", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(page|p\.)\s*\d+\b", "", cleaned)
    return cleaned.strip()
