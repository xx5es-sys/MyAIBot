# 🚨 إصلاحات عاجلة - Urgent Security Fixes

## ⚠️ تحذير أمني هام

تم اكتشاف عدة مشاكل أمنية حرجة في الكود تحتاج إصلاحاً فورياً قبل نشر البوت في بيئة الإنتاج.

---

## 1. تسريب API Tokens (Critical)

### المشكلة:
API Tokens مكشوفة مباشرة في الكود في عدة ملفات:

| الملف | السطر | Token |
|-------|-------|-------|
| `config.py` | 5 | `8317431246:AAFfUUDoocr273qTY0v4r8i-giy7fNmAoug` |
| `premium_util.py` | 17 | `7830034663:AAHcEFO9dHuQRPdRx93sKwYt2TzWGBvev70` |
| `aum.py` | 16 | `7830034663:AAHcEFO9dHuQRPdRx93sKwYt2TzWGBvev70` |
| `proxy_.py` | 6 | `8317431246:AAFfUUDoocr273qTY0v4r8i-giy7fNmAoug` |
| `scrape.py` | 9 | `8317431246:AAFfUUDoocr273qTY0v4r8i-giy7fNmAoug` |

### الإصلاح:

**الخطوة 1:** إنشاء ملف `.env`:
```bash
# .env
TELEGRAM_BOT_TOKEN=8317431246:AAFfUUDoocr273qTY0v4r8i-giy7fNmAoug
ADMIN_USER_ID=608548316
```

**الخطوة 2:** تعديل `config.py`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
Admin = int(os.getenv('ADMIN_USER_ID'))

if not API_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")
```

**الخطوة 3:** إضافة `.env` لـ `.gitignore`:
```bash
echo ".env" >> .gitignore
```

**الخطوة 4:** تثبيت python-dotenv:
```bash
pip install python-dotenv
```

---

## 2. تسريب Stripe Account IDs (Critical)

### المشكلة:
ملف `acc.py` يحتوي على 31 زوج من Stripe account IDs مكشوفة.

### الإصلاح:

**الخطوة 1:** نقل البيانات لملف منفصل مشفر أو environment variable:
```python
# acc.py - الإصدار الآمن
import os
import json

def load_pairs():
    pairs_json = os.getenv('STRIPE_PAIRS')
    if pairs_json:
        return json.loads(pairs_json)
    return []

pairs = load_pairs()
```

**الخطوة 2:** أو استخدام ملف مشفر:
```python
from cryptography.fernet import Fernet

def load_encrypted_pairs(key_path, data_path):
    with open(key_path, 'rb') as f:
        key = f.read()
    fernet = Fernet(key)
    with open(data_path, 'rb') as f:
        encrypted = f.read()
    return json.loads(fernet.decrypt(encrypted))
```

---

## 3. تسريب Proxy Credentials (Critical)

### المشكلة:
في `proxy_.py` سطر 40-41:
```python
proxy_url = "http://p.webshare.io:80/"
proxy_auth = aiohttp.BasicAuth('jelxyqtc-rotate', 'vxigi2vt6v8x')
```

### الإصلاح:
```python
import os

proxy_url = os.getenv('PROXY_URL')
proxy_user = os.getenv('PROXY_USER')
proxy_pass = os.getenv('PROXY_PASS')

proxy_auth = aiohttp.BasicAuth(proxy_user, proxy_pass) if proxy_user else None
```

---

## 4. تسريب Telethon API Credentials (Critical)

### المشكلة:
في `scrape.py` سطر 10-11:
```python
api_id   = '1234567'
api_hash = '2dc4807c0abe5b2a1bd0b77c35b68c38'
```

### الإصلاح:
```python
import os

api_id = os.getenv('TELETHON_API_ID')
api_hash = os.getenv('TELETHON_API_HASH')
```

---

## 5. Bot Token متعدد ومختلف (High)

### المشكلة:
يوجد Bot instances متعددة بـ tokens مختلفة:
- Token 1: `8317431246:...` (main, config, proxy_, scrape)
- Token 2: `7830034663:...` (premium_util, aum)

### الإصلاح:
إنشاء ملف `loader.py` مركزي:

```python
# loader.py
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import os

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
```

ثم استيراده في جميع الملفات:
```python
from loader import bot, dp
```

---

## 6. ملف `.env.example`

أنشئ هذا الملف كمرجع:

```bash
# .env.example - Copy to .env and fill in values

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_admin_id_here

# Telethon (for scraper)
TELETHON_API_ID=your_api_id
TELETHON_API_HASH=your_api_hash

# Proxy
PROXY_URL=http://proxy.example.com:80/
PROXY_USER=your_proxy_user
PROXY_PASS=your_proxy_pass

# Payment
PAYMENT_PROVIDER_TOKEN=your_payment_token

# Database (future)
DATABASE_URL=sqlite:///bot.db
```

---

## 7. إضافة `.gitignore`

```gitignore
# .gitignore

# Environment
.env
.env.local
.env.*.local

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# Data files
*.json
!package.json
*.db
*.sqlite

# Logs
*.log

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Session files
*.session
*.session-journal
```

---

## خطوات التنفيذ

### الترتيب الموصى به:

1. **فوراً (اليوم):**
   - [ ] إنشاء `.env` ونقل جميع الـ secrets
   - [ ] إنشاء `.gitignore`
   - [ ] تعديل `config.py` لاستخدام environment variables

2. **خلال يومين:**
   - [ ] إنشاء `loader.py` وتوحيد Bot instance
   - [ ] تعديل جميع الملفات لاستخدام `loader.py`
   - [ ] اختبار البوت بعد التعديلات

3. **خلال أسبوع:**
   - [ ] تشفير `acc.py` data
   - [ ] إضافة validation للـ environment variables
   - [ ] مراجعة أمنية شاملة

---

## التحقق من الإصلاح

بعد تطبيق الإصلاحات، تأكد من:

```bash
# البحث عن أي tokens متبقية
grep -r "AAF" --include="*.py" .
grep -r "AAH" --include="*.py" .
grep -r "token=" --include="*.py" .

# يجب أن لا تظهر أي نتائج تحتوي على tokens حقيقية
```

---

**⚠️ تنبيه:** إذا تم نشر هذا الكود على GitHub أو أي منصة عامة، يجب:
1. إلغاء جميع الـ tokens المكشوفة فوراً
2. إنشاء tokens جديدة
3. مراجعة سجل Git وحذف الـ commits التي تحتوي على secrets

```bash
# لحذف الملفات الحساسة من تاريخ Git
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config.py acc.py' \
  --prune-empty --tag-name-filter cat -- --all
```
