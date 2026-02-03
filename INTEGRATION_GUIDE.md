# دليل دمج البوابات الوهمية

## الملفات المُنشأة

### 1. `mock_single.py` - بوابة الفحص الفردي الوهمية
- **الأمر:** `/chk CC|MM|YYYY|CVV`
- **الوظيفة:** فحص بطاقة واحدة وإرجاع نتيجة وهمية

### 2. `mock_mass.py` - بوابة الفحص الجماعي الوهمية
- **الأمر:** `/mass`
- **الوظيفة:** فحص ملف يحتوي على بطاقات متعددة

---

## خطوات الدمج في main.py

### الخطوة 1: إضافة الاستيرادات

أضف في بداية ملف `main.py`:

```python
# استيراد البوابات الوهمية
from mock_single import register_handlers as register_mock_single
from mock_mass import register_handlers as register_mock_mass
```

### الخطوة 2: تسجيل الـ Handlers

أضف قبل سطر `executor.start_polling()`:

```python
# تسجيل البوابات الوهمية
register_mock_single(dp)
register_mock_mass(dp)
```

---

## مثال كامل للدمج

```python
# main.py

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

# الإعدادات
from config import API_TOKEN

# البوابات الوهمية
from mock_single import register_handlers as register_mock_single
from mock_mass import register_handlers as register_mock_mass

# إنشاء البوت
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# تسجيل البوابات الوهمية
register_mock_single(dp)
register_mock_mass(dp)

# ... باقي الـ handlers ...

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
```

---

## الاستخدام

### الفحص الفردي (`/chk`)

```
/chk 4111111111111111|12|2025|123
```

**النتيجة:**
```
𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅

𝐂𝐚𝐫𝐝 ⇾ 4111111111111111|12|2025|123
𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ Mock Gateway $0.00
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ Payment Approved

𝐈𝐧𝐟𝐨 ⇾ VISA - CLASSIC - CREDIT
𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ Mock Bank International
𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ United States 🇺🇸

𝐓𝐨𝐨𝐤 ⇾ 2.35 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ User {Free}
```

### الفحص الجماعي (`/mass`)

1. أرسل `/mass`
2. أرسل ملف `.txt` يحتوي على:
   ```
   4111111111111111|12|2025|123
   5500000000000004|06|2026|456
   340000000000009|09|2027|789
   ```
3. اختر البوابة من القائمة
4. انتظر النتائج

---

## التخصيص

### تغيير اسم الأمر

في `mock_single.py`:
```python
# غيّر 'chk' إلى الأمر المطلوب
dp.register_message_handler(handle_mock_single_command, commands=['ad'])
```

### تغيير النتائج الوهمية

في كلا الملفين، عدّل قائمة `MOCK_RESULTS`:
```python
MOCK_RESULTS = [
    {"status": "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅", "response": "Payment Approved", "weight": 10},
    # أضف أو عدّل النتائج هنا
]
```

### تغيير التأخير

في `mock_single.py`:
```python
MIN_DELAY = 1.5  # الحد الأدنى بالثواني
MAX_DELAY = 3.5  # الحد الأقصى بالثواني
```

في `mock_mass.py`:
```python
DELAY_PER_CARD = 0.5  # التأخير بين كل بطاقة
```

---

## إضافة التحقق من الصلاحيات

لإضافة التحقق من الصلاحيات (Premium/Admin)، عدّل في `mock_single.py`:

```python
from config import Admin, is_premium, can_use_b3

async def handle_mock_single_command(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # التحقق من الصلاحيات
    if user_id == Admin:
        user_status = "Owner"
    elif await is_premium(str(user_id)):
        user_status = "Premium"
    else:
        user_status = "Free"
    
    # التحقق من إمكانية الاستخدام
    if not await can_use_b3(chat_id, user_id):
        await message.reply("Please wait 30 seconds before using this command again.")
        return
    
    # ... باقي الكود
```

---

## ملاحظات مهمة

1. **هذه بوابات وهمية للاختبار فقط** - لا يوجد أي فحص حقيقي
2. **لا تستخدم في الإنتاج** - النتائج عشوائية بالكامل
3. **لا يوجد اتصال خارجي** - كل شيء يعمل محلياً
4. **آمنة للاستخدام** - لا تحتوي على أي منطق دفع حقيقي

---

## استكشاف الأخطاء

### الأمر لا يعمل
- تأكد من تسجيل الـ handler في `main.py`
- تأكد من استخدام `MemoryStorage` في الـ Dispatcher

### خطأ في FSM
- تأكد من إضافة `storage=MemoryStorage()` عند إنشاء الـ Dispatcher

### الملف لا يُقرأ
- تأكد من أن الملف بصيغة `.txt`
- تأكد من أن الترميز UTF-8
