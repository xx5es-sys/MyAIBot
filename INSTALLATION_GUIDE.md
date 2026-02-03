# دليل التثبيت - نظام الكريدت

## 📋 قبل البدء

تأكد من أن لديك:
- ✅ نسخة احتياطية من الملفات القديمة
- ✅ البوت متوقف عن العمل
- ✅ صلاحيات الكتابة على الملفات

---

## 🚀 خطوات التثبيت

### الخطوة 1: النسخ الاحتياطي

```bash
# إنشاء نسخة احتياطية من الملفات القديمة
cp premium_util.py premium_util.py.backup
cp premium.json premium.json.backup
cp config.py config.py.backup
cp mass.py mass.py.backup
cp cmds.py cmds.py.backup
cp admin.py admin.py.backup
```

### الخطوة 2: استبدال الملفات

```bash
# فك ضغط الملفات الجديدة
unzip BOS_credit_system_updated.zip

# استبدال الملفات القديمة
# (الملفات الجديدة ستحل محل القديمة تلقائياً)
```

### الخطوة 3: تحديث premium.json

**إذا كان لديك مستخدمين حاليين:**

قم بتحديث ملف `premium.json` يدوياً لإضافة الحقول الجديدة:

```json
{
  "premium_users": [
    {
      "user_id": "123456789",
      "username": "example_user",
      "credits": 0,              ← أضف هذا
      "unlimited": false,        ← أضف هذا
      "since": "2025-07-26 13:42:14",
      "expires": "2025-08-02 13:42:14",
      "last_chk": "—"            ← أضف هذا
    }
  ]
}
```

**أو استخدم هذا السكريبت:**

```python
import json

# قراءة الملف القديم
with open('premium.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# تحديث كل مستخدم
for user in data.get('premium_users', []):
    user.setdefault('credits', 0)
    user.setdefault('unlimited', False)
    user.setdefault('last_chk', '—')

# حفظ الملف المحدث
with open('premium.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ تم تحديث premium.json بنجاح")
```

### الخطوة 4: التحقق من التبعيات

تأكد من تثبيت المكتبات المطلوبة:

```bash
pip install aiogram aiofiles aiohttp
```

### الخطوة 5: إعادة تشغيل البوت

```bash
python3 main.py
```

---

## 🧪 الاختبار الأولي

### 1. اختبار Admin

```
1. أرسل /start للبوت
2. اضغط على "MY PROFILE"
3. يجب أن تظهر:
   • Status       ADMIN
   • Credits      ∞
   • Validity     Unlimited
```

### 2. اختبار إضافة كريدت

```
1. أرسل /admin
2. اختر "💰 Add Credits"
3. أدخل: 10
4. أدخل user_id لمستخدم اختبار
5. تحقق من أن المستخدم استلم رسالة
```

### 3. اختبار فحص فردي

```
1. كمستخدم لديه 5 كريدت
2. نفّذ أمر فحص فردي (مثلاً /au)
3. أرسل /sup → يجب أن يظهر 4 كريدت
```

### 4. اختبار فحص جماعي

```
1. كمستخدم لديه 3 كريدت
2. ابدأ جلسة Mass
3. ارفع ملف .txt مع 5 بطاقات
4. يجب أن يتوقف بعد 3 بطاقات
5. رسالة: "⛔ نفاد الكريدت. توقفت الجلسة بعد 3 بطاقة."
```

---

## ⚠️ مشاكل شائعة وحلولها

### المشكلة 1: خطأ في استيراد premium_util

**الحل:**
```python
# تأكد من أن premium_util.py في نفس المجلد مع الملفات الأخرى
# تأكد من عدم وجود أخطاء في الملف
python3 -c "import premium_util; print('✅ OK')"
```

### المشكلة 2: خطأ في قراءة premium.json

**الحل:**
```bash
# تحقق من صحة JSON
python3 -m json.tool premium.json
```

### المشكلة 3: لا يتم خصم الكريدت

**الحل:**
```python
# تحقق من أن config.py يستدعي consume_for_single
# تحقق من أن الدالة async
# تحقق من السجلات (logs)
```

### المشكلة 4: خطأ في asyncio.Lock

**الحل:**
```python
# تأكد من أن جميع الدوال التي تستخدم _file_lock هي async
# تأكد من استخدام await عند استدعائها
```

---

## 🔄 الرجوع للنظام القديم

إذا واجهت مشاكل، يمكنك الرجوع للنظام القديم:

```bash
# استعادة النسخ الاحتياطية
cp premium_util.py.backup premium_util.py
cp premium.json.backup premium.json
cp config.py.backup config.py
cp mass.py.backup mass.py
cp cmds.py.backup cmds.py
cp admin.py.backup admin.py

# إعادة تشغيل البوت
python3 main.py
```

---

## 📞 الدعم

إذا واجهت أي مشاكل:

1. راجع ملف `README_CREDIT_SYSTEM.md` للتفاصيل الكاملة
2. تحقق من السجلات (logs) للأخطاء
3. تأكد من أن جميع الملفات محدثة
4. تحقق من صلاحيات الملفات

---

## ✅ قائمة التحقق النهائية

- [ ] تم عمل نسخة احتياطية من جميع الملفات
- [ ] تم استبدال الملفات القديمة بالجديدة
- [ ] تم تحديث premium.json بالحقول الجديدة
- [ ] تم التحقق من التبعيات
- [ ] تم إعادة تشغيل البوت بنجاح
- [ ] تم اختبار Admin
- [ ] تم اختبار إضافة كريدت
- [ ] تم اختبار فحص فردي
- [ ] تم اختبار فحص جماعي
- [ ] تم اختبار Unlimited
- [ ] تم اختبار Refund

---

**ملاحظة مهمة:** بعد التثبيت الناجح، احتفظ بالنسخ الاحتياطية لمدة أسبوع على الأقل للتأكد من استقرار النظام.

---

**تم التطوير بواسطة:** Manus AI  
**التاريخ:** 26 أكتوبر 2025

