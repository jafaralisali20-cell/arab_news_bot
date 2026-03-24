import re
import hashlib

def clean_text(text: str) -> str:
      """Remove all URLs, HTML tags, and extra whitespace from news text."""
      if not text:
                return ""
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', text)
    # Remove all URLs (http, https, t.me, www)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'www\.\S+', '', text)
    text = re.sub(r't\.me/\S+', '', text)
    # Remove @mentions
    text = re.sub(r'@\w+', '', text)
    # Remove HTML entities
    text = re.sub(r'&\w+;', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def make_hash(text: str) -> str:
      """Returns an MD5 hash of the cleaned text."""
    return hashlib.md5(text.encode()).hexdigest()

def is_short(text: str, min_chars: int = 30) -> bool:
      """Returns True if the text is too short to be a real news item."""
    return len(text.strip()) < min_chars
