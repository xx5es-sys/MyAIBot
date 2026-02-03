# 🛠 دليل ربط بوابة حقيقية (Real Gateway Integration)

لتحويل أي بوابة من **وهمية (Mock)** إلى **حقيقية (Real)**، يجب عليك استبدال استدعاء `handle_mock_command` بكود يقوم بإرسال طلبات HTTP إلى بوابة الدفع (مثل Stripe أو Braintree).

---

## 1️⃣ مثال عملي: ربط بوابة Stripe حقيقية

بدلاً من استخدام القالب الوهمي في ملف `stripe_.py` مثلاً، سنستخدم مكتبة `requests` أو `aiohttp` لإرسال الطلب.

### الكود المقترح لملف `stripe_real.py`:

```python
import aiohttp
from aiogram import types
import config

async def check_stripe_real(cc, mes, ano, cvv):
    """
    دالة ترسل طلب حقيقي لـ Stripe API
    """
    url = "https://api.stripe.com/v1/payment_methods"
    headers = {
        "Authorization": f"Bearer {config.STRIPE_SK}", # يجب إضافة SK في config
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "type": "card",
        "card[number]": cc,
        "card[exp_month]": mes,
        "card[exp_year]": ano,
        "card[cvc]": cvv,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as resp:
            result = await resp.json()
            if "id" in result:
                return "✅ Approved", result["id"]
            else:
                return "❌ Declined", result.get("error", {}).get("message", "Unknown Error")

async def handle_chk_command(message: types.Message):
    # 1. تحليل البطاقة (نفس الكود السابق)
    # 2. استدعاء check_stripe_real
    # 3. تنسيق الرسالة وإرسالها للمستخدم
    pass
```

---

## 2️⃣ خطوات التحويل الشاملة

1. **الحصول على API Keys:** يجب أن تملك مفاتيح (Secret Keys) من بوابة الدفع.
2. **تعديل ملف البوابة:** اختر الملف (مثلاً `b3.py`) واحذف استدعاء `handle_mock_command`.
3. **كتابة منطق الفحص:** استخدم مكتبة `aiohttp` لإرسال بيانات البطاقة واستقبال الرد.
4. **تحديث الفحص الجماعي:** في ملف `mass.py` داخل دالة `check_single_card_mock` قم باستبدال المنطق الوهمي بالمنطق الحقيقي الذي كتبته.

---

## 3️⃣ نصيحة أمنية ⚠️
عند الانتقال للبوابات الحقيقية، تأكد من:
- استخدام **Proxies** لتجنب حظر الـ IP الخاص بك من قبل بوابات الدفع.
- تشفير بيانات البطاقات وعدم تخزينها في السجلات (Logs).
- استخدام مكتبة `aiohttp` لأنها تدعم البرمجة غير المتزامنة (Async) التي يعتمد عليها البوت.
