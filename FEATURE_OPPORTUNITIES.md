# 💡 فرص الميزات الجديدة - Feature Opportunities

هذا المستند يحتوي على اقتراحات لميزات جديدة منسجمة مع طبيعة البوت ومبنية على تحليل الكود الحالي.

---

## 1. نظام سجل الكريدت (Credit History)

### القيمة:
- تتبع كامل لاستهلاك واسترداد الكريدت
- شفافية للمستخدمين
- تحليلات للأدمن

### المتطلبات:
- جدول جديد `credit_transactions`
- API لعرض السجل
- تقارير للأدمن

### المخاطر:
- زيادة حجم البيانات
- تعقيد الاستعلامات

### تقدير الوقت:
**3-5 أيام**

### التغييرات المعمارية:
```python
# models/credit_transaction.py
class CreditTransaction:
    id: int
    user_id: str
    amount: int  # positive = add, negative = consume
    type: str  # "purchase", "consume", "refund", "admin_add"
    reason: str
    balance_after: int
    created_at: datetime
```

### الأوامر الجديدة:
- `/history` - عرض آخر 10 معاملات
- `/history 50` - عرض آخر 50 معاملة

---

## 2. إشعارات انتهاء الاشتراك (Expiry Notifications)

### القيمة:
- تذكير المستخدمين قبل انتهاء الاشتراك
- زيادة معدل التجديد
- تجربة مستخدم أفضل

### المتطلبات:
- Scheduler للإشعارات
- قوالب رسائل
- إعدادات المستخدم

### المخاطر:
- إزعاج المستخدمين
- تحميل على البوت

### تقدير الوقت:
**2-3 أيام**

### التغييرات المعمارية:
```python
# services/notification_service.py
async def check_expiring_subscriptions():
    """
    يُشغّل يومياً لإرسال إشعارات:
    - قبل 7 أيام من الانتهاء
    - قبل يوم واحد
    - عند الانتهاء
    """
    pass
```

---

## 3. باقات الكريدت (Credit Packages)

### القيمة:
- خيارات شراء متنوعة
- خصومات للكميات الكبيرة
- زيادة الإيرادات

### المتطلبات:
- تعريف الباقات
- واجهة اختيار
- معالجة الدفع

### المخاطر:
- تعقيد نظام الدفع
- إدارة الأسعار

### تقدير الوقت:
**3-4 أيام**

### التغييرات المعمارية:
```python
# config/packages.py
CREDIT_PACKAGES = [
    {"id": "starter", "credits": 10, "price": 10, "bonus": 0},
    {"id": "basic", "credits": 50, "price": 45, "bonus": 5},
    {"id": "pro", "credits": 100, "price": 80, "bonus": 20},
    {"id": "unlimited", "credits": -1, "price": 200, "duration_days": 30},
]
```

### الأوامر الجديدة:
- `/packages` - عرض الباقات المتاحة
- `/buy starter` - شراء باقة محددة

---

## 4. إحصائيات المستخدم (User Statistics)

### القيمة:
- رؤية شاملة للاستخدام
- تحفيز المستخدمين
- بيانات للتحليل

### المتطلبات:
- تتبع الاستخدام
- حساب الإحصائيات
- عرض جذاب

### المخاطر:
- تأثير على الأداء
- خصوصية البيانات

### تقدير الوقت:
**4-5 أيام**

### التغييرات المعمارية:
```python
# models/user_stats.py
class UserStats:
    user_id: str
    total_checks: int
    approved_count: int
    declined_count: int
    ccn_count: int
    success_rate: float
    favorite_gateway: str
    last_active: datetime
```

### الأوامر الجديدة:
- `/stats` - إحصائياتي
- `/leaderboard` - أفضل المستخدمين (اختياري)

---

## 5. نظام الإحالة (Referral System)

### القيمة:
- نمو عضوي
- مكافأة المستخدمين النشطين
- بناء مجتمع

### المتطلبات:
- روابط إحالة فريدة
- تتبع الإحالات
- نظام مكافآت

### المخاطر:
- إساءة الاستخدام
- تعقيد النظام

### تقدير الوقت:
**5-7 أيام**

### التغييرات المعمارية:
```python
# models/referral.py
class Referral:
    referrer_id: str
    referred_id: str
    referral_code: str
    reward_given: bool
    created_at: datetime

# config/referral.py
REFERRAL_REWARD = 5  # credits
REFEREE_BONUS = 2    # credits for new user
```

### الأوامر الجديدة:
- `/referral` - الحصول على رابط الإحالة
- `/myreferrals` - عرض الإحالات الناجحة

---

## 6. وضع الصيانة المحسّن (Enhanced Maintenance Mode)

### القيمة:
- تحكم أفضل بالبوت
- إشعار المستخدمين
- جدولة الصيانة

### المتطلبات:
- API للتحكم
- رسائل مخصصة
- استثناءات للأدمن

### المخاطر:
- منخفضة

### تقدير الوقت:
**1-2 يوم**

### التغييرات المعمارية:
```python
# middlewares/maintenance.py
class EnhancedMaintenanceMiddleware:
    def __init__(self):
        self.enabled = False
        self.message = "Bot under maintenance"
        self.estimated_end = None
        self.allowed_users = []  # Admin IDs
```

### الأوامر الجديدة:
- `/maintenance on "رسالة مخصصة"` - تفعيل
- `/maintenance off` - إيقاف
- `/maintenance status` - الحالة

---

## 7. نظام التذاكر (Ticket System)

### القيمة:
- دعم فني منظم
- تتبع المشاكل
- تحسين الخدمة

### المتطلبات:
- إنشاء تذاكر
- إدارة الحالات
- إشعارات

### المخاطر:
- عبء إضافي على الأدمن
- تعقيد النظام

### تقدير الوقت:
**5-7 أيام**

### التغييرات المعمارية:
```python
# models/ticket.py
class Ticket:
    id: int
    user_id: str
    subject: str
    status: str  # "open", "in_progress", "resolved", "closed"
    priority: str  # "low", "medium", "high"
    messages: List[TicketMessage]
    created_at: datetime
    updated_at: datetime
```

### الأوامر الجديدة:
- `/ticket "المشكلة"` - فتح تذكرة
- `/mytickets` - تذاكري
- `/ticket 123 reply "الرد"` - الرد على تذكرة

---

## 8. تكامل BIN Lookup حقيقي (Real BIN Lookup)

### القيمة:
- معلومات دقيقة عن البطاقات
- تحسين تجربة المستخدم
- بيانات موثوقة

### المتطلبات:
- API خارجي (binlist.net أو مشابه)
- Caching
- Rate limiting

### المخاطر:
- تكلفة API
- اعتماد على خدمة خارجية

### تقدير الوقت:
**2-3 أيام**

### التغييرات المعمارية:
```python
# services/bin_lookup.py
import aiohttp
from functools import lru_cache

class BINLookupService:
    BASE_URL = "https://lookup.binlist.net/"
    
    @lru_cache(maxsize=1000)
    async def lookup(self, bin: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}{bin}") as resp:
                return await resp.json()
```

---

## 9. تصدير النتائج (Export Results)

### القيمة:
- حفظ نتائج الفحص
- تحليل لاحق
- مشاركة سهلة

### المتطلبات:
- تنسيقات متعددة (TXT, CSV, JSON)
- فلترة النتائج
- ضغط الملفات

### المخاطر:
- حجم الملفات
- أمان البيانات

### تقدير الوقت:
**2-3 أيام**

### التغييرات المعمارية:
```python
# services/export_service.py
class ExportService:
    async def export_mass_results(
        self, 
        session_id: int, 
        format: str = "txt",
        filter: str = "all"  # "all", "live", "dead", "ccn"
    ) -> bytes:
        pass
```

### الأوامر الجديدة:
- `/export live` - تصدير البطاقات الحية
- `/export all csv` - تصدير الكل بصيغة CSV

---

## 10. جدولة الفحص (Scheduled Checks)

### القيمة:
- فحص تلقائي
- توفير الوقت
- مراقبة مستمرة

### المتطلبات:
- جدولة المهام
- إشعارات بالنتائج
- إدارة الجداول

### المخاطر:
- استهلاك الموارد
- تعقيد النظام

### تقدير الوقت:
**5-7 أيام**

### التغييرات المعمارية:
```python
# models/scheduled_check.py
class ScheduledCheck:
    id: int
    user_id: str
    cards: List[str]
    gateway: str
    schedule: str  # cron expression
    last_run: datetime
    next_run: datetime
    enabled: bool
```

### الأوامر الجديدة:
- `/schedule daily 09:00 b3` - جدولة فحص يومي
- `/myschedules` - عرض الجداول
- `/schedule delete 1` - حذف جدول

---

## ترتيب الأولويات المقترح

| الأولوية | الميزة | السبب |
|----------|--------|-------|
| 1 | Credit History | شفافية وثقة |
| 2 | Expiry Notifications | زيادة التجديد |
| 3 | Credit Packages | زيادة الإيرادات |
| 4 | User Statistics | تحفيز المستخدمين |
| 5 | Real BIN Lookup | تحسين الجودة |
| 6 | Export Results | طلب شائع |
| 7 | Enhanced Maintenance | تحكم أفضل |
| 8 | Referral System | نمو عضوي |
| 9 | Ticket System | دعم منظم |
| 10 | Scheduled Checks | ميزة متقدمة |

---

## ملاحظات التنفيذ

### قبل البدء بأي ميزة:
1. ✅ إصلاح المشاكل الأمنية أولاً
2. ✅ إعادة الهيكلة المعمارية
3. ✅ إضافة الاختبارات الأساسية

### لكل ميزة:
1. 📝 كتابة User Story
2. 🎨 تصميم الواجهة
3. 💻 التنفيذ
4. 🧪 الاختبار
5. 📚 التوثيق
6. 🚀 النشر

---

**نهاية المستند**
