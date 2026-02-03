# دليل البوابات الوهمية (Mock Gateways)

## نظرة عامة

هذه بوابات وهمية للاختبار فقط - لا يوجد أي فحص حقيقي أو اتصال خارجي.
المدخلات تُعامل كنصوص تجريبية فقط، والتحقق شكلي للصيغة فقط.

---

## الملفات

### 1. `mock_gateways_single.py` - البوابات المفردة

**الأوامر المتاحة:**

| الأمر | البوابة | النوع |
|-------|---------|-------|
| `/au` | Braintree Auth | AUTH |
| `/st` | Stripe Auth | AUTH |
| `/sq` | Square Auth | AUTH |
| `/vbv` | Braintree VBV | VBV |
| `/3D` | Bassed V2 / 3D | 3DS |
| `/pp` | PayPal Charge | CHARGE |
| `/SH` | Stripe Charge | CHARGE |

**الاستخدام:**
```
/au 4111111111111111|12|2025|123
/st 5500000000000004|06|26|456
/3D 340000000000009|09|2027|789
```

**التدفق 1:1:**
1. استقبال المُدخل من نفس رسالة الأمر
2. التحقق الشكلي من الصيغة (4 فقرات مفصولة بـ `|`)
3. إذا خاطئة: إرسال رسالة Usage
4. إذا صحيحة:
   - إرسال `𝐏𝐫𝐨𝐜𝐞𝐬𝐬𝐢𝐧𝐠 ...`
   - تأخير وهمي async
   - اختيار نتيجة عشوائية
   - تعديل الرسالة بالنتيجة النهائية

---

### 2. `mock_gateways_mass.py` - الفحص الجماعي

**الاستخدام (بدون أمر `/mass`):**
1. أرسل ملف `.txt` مباشرة
2. البوت يتحقق من الملف ويستخرج الأسطر الصالحة
3. يعرض قائمة البوابات/أنواع الفحص للاختيار
4. عند الاختيار يبدأ المعالجة مع تحديث Progress
5. في النهاية يرسل Summary نهائي

**صيغة الملف:**
```
4111111111111111|12|2025|123
5500000000000004|06|26|456
340000000000009|09|2027|789
```

**البوابات المتاحة للجماعي:**
- AUTH: Braintree Auth, Stripe Auth, Square Auth
- VBV/3DS: Braintree VBV, Bassed V2 / 3D
- CHARGE: PayPal Charge, Stripe Charge

---

## الدمج في main.py

### الخطوة 1: الاستيرادات

```python
# استيراد البوابات الوهمية
from mock_gateways_single import register_handlers as register_single_gateways
from mock_gateways_mass import register_handlers as register_mass_gateways
```

### الخطوة 2: التسجيل

```python
# تسجيل البوابات الوهمية (قبل start_polling)
register_single_gateways(dp)
register_mass_gateways(dp)
```

### مثال كامل:

```python
# main.py

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import API_TOKEN

# البوابات الوهمية
from mock_gateways_single import register_handlers as register_single_gateways
from mock_gateways_mass import register_handlers as register_mass_gateways

# إنشاء البوت
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# تسجيل البوابات الوهمية
register_single_gateways(dp)
register_mass_gateways(dp)

# ... باقي الـ handlers ...

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
```

---

## شكل النتيجة النهائية

### الفحص المفرد:

```
𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅

𝐂𝐚𝐫𝐝 ⇾ 4111111111111111|12|2025|123
𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ⇾ Braintree Auth $0.00
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ⇾ Payment Approved
𝐑𝐢𝐬𝐤 ⇾ Low

𝐈𝐧𝐟𝐨 ⇾ VISA - CLASSIC - CREDIT
𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ JPMORGAN CHASE BANK N.A.
𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ United States 🇺🇸

𝐓𝐨𝐨𝐤 ⇾ 2.35 𝘀𝗲𝗰𝗼𝗻𝗱𝘀
𝐑𝐞𝐪𝐮𝐞𝐬𝐭𝐞𝐝 𝐛𝐲 ⇾ User {Free}
```

### الفحص الجماعي (Progress):

```
⏳ جاري الفحص...

📊 التقدم: [▓▓▓▓▓░░░░░] 50.0%
📝 المعالجة: 25/50

✅ Live: 5
❌ Dead: 12
♻️ CCN: 3
🔄 Retry: 2
⚠️ Error: 3

🔹 Gateway: Braintree Auth
```

### الفحص الجماعي (Summary):

```
✅ اكتمل الفحص الجماعي

📊 Summary:
├ Total: 50
├ ✅ Live: 5
├ ❌ Dead: 25
├ ♻️ CCN: 8
├ 🔄 Retry: 7
└ ⚠️ Error: 5

⏱ Time: 15.23s
🔹 Gateway: Braintree Auth

✅ Live (5):
4111111111111111|12|2025|123
5500000000000004|06|26|456
...
```

---

## ملاحظات مهمة

1. **هذه بوابات وهمية للاختبار فقط**
2. **لا يوجد أي اتصال خارجي أو فحص حقيقي**
3. **المدخلات تُعامل كنصوص تجريبية فقط**
4. **التحقق المطلوب هو تحقق شكلي للصيغة فقط**
5. **معلومات BIN حقيقية من API خارجي**

---

## التخصيص

### تغيير النتائج الوهمية:

```python
MOCK_RESULTS = [
    {"status": "𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅", "response": "Payment Approved", "risk": "Low", "weight": 10},
    # أضف أو عدّل النتائج هنا
]
```

### تغيير التأخير:

```python
# في mock_gateways_single.py
MIN_DELAY = 1.5  # الحد الأدنى
MAX_DELAY = 3.5  # الحد الأقصى

# في mock_gateways_mass.py
DELAY_PER_CARD = 0.3  # التأخير بين كل سطر
```

### إضافة بوابة جديدة:

```python
# في mock_gateways_single.py
GATEWAYS_CONFIG = {
    # ... البوابات الموجودة ...
    "new_cmd": {
        "name": "New Gateway",
        "type": "AUTH",
        "amount": "$0.00",
        "command": "new_cmd"
    }
}

# أضف handler جديد
async def handle_new_command(message: types.Message):
    await handle_single_gateway_command(message, "new_cmd")

# سجّل في register_handlers
dp.register_message_handler(handle_new_command, commands=['new_cmd'])
```
