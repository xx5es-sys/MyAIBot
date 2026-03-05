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
    
    # Replace dots
    text = text.replace("•", DOT_ANCHOR)
    
    return text
