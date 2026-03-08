import re

BOT_LINK = "http://t.me/IgnisXBot"
BRAND_ANCHOR = f'<a href="{BOT_LINK}">𝖨𝖦𝖭𝖨𝖲𝖷</a>'
DOT_ANCHOR = f'<a href="{BOT_LINK}">•</a>'

def apply_branding(text: str) -> str:
    if not text:
        return text
    
    # Replace bot names
    patterns = [
        r"O\.tbot",
        r"O\.T Bot",
        r"O\.TBOT",
        r"𝗢\.𝗧",
        r"O\.T"
    ]
    for pattern in patterns:
        text = re.sub(pattern, BRAND_ANCHOR, text, flags=re.IGNORECASE)
    
    # Replace standalone dots (•) that are NOT already inside <a> tags
    # Split text by <a ...>...</a> segments to avoid replacing inside them
    parts = re.split(r'(<a\s[^>]*>.*?</a>)', text)
    for i, part in enumerate(parts):
        # Only replace in non-anchor parts
        if not part.startswith('<a '):
            parts[i] = part.replace("•", DOT_ANCHOR)
    text = ''.join(parts)
    
    return text
