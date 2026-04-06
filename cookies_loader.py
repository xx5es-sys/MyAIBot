"""
=================================================================
Cookies Loader - محمل ملفات الـ Cookies للبوابات
=================================================================
يوفر دالة موحدة لتحميل الـ cookies من ملفات النص
بالتنسيق المستخدم في جميع بوابات gateway.zip
"""
import os
import random


def load_cookies(filepath: str) -> dict:
    """
    تحميل مجموعة cookies عشوائية من ملف نصي.
    
    صيغة الملف المدعومة:
        cookies = {
            'key': 'value',
            ...
        }
        cookies = { ... }
    
    يُرجع: dict من الـ cookies المختارة عشوائياً
    """
    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    cookies_list = []
    for block in content.split('cookies = '):
        block = block.strip()
        if block.startswith('{'):
            try:
                end = block.rfind('}') + 1
                parsed = eval(block[:end])  # noqa: S307
                if isinstance(parsed, dict):
                    cookies_list.append(parsed)
            except Exception:
                pass

    if not cookies_list:
        return {}

    return random.choice(cookies_list)


def get_cookies_path(filename: str) -> str:
    """
    إرجاع المسار الكامل لملف cookies بالنسبة لمجلد البوت.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)
