# محاكاة تفاعلية مفصلة: سيناريوهات المشرف وإدارة الائتمانات

هذا التقرير يقدم محاكاة تفصيلية لكل تفاعل (أمر، زر، رد) للمشرف في بوت فحص البطاقات، مع التركيز على إدارة الاشتراكات والائتمانات.

## 1. لوحة تحكم المشرف (الأمر: /admin)

| الخطوة | الإجراء (المشرف) | الزر/الأمر | الرد (البوت) | الدالة/الحالة | التفاصيل الدقيقة |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. الدخول** | إرسال الأمر | `/admin` | **الرد:** `Admin Menu:` مع أزرار الإدارة. | `admin_commands` / `AdminActions.authorized` | يتم التحقق من `message.from_user.id == Admin` قبل عرض القائمة. |
| **2. عرض المستخدمين** | الضغط على زر | **👥 View Premium Users** | **تحديث الرسالة:** قائمة مفصلة بجميع المستخدمين المميزين. | `view_premium_users` | يتم قراءة `premium.json` وعرض حالة كل مستخدم (♾️ UNLIMITED، 💰 CREDIT PREMIUM، ⏰ TIME-BASED). |

## 2. إدارة الائتمانات (Add Credits)

| الخطوة | الإجراء (المشرف) | الإدخال | الرد (البوت) | الدالة/الحالة | التفاصيل الدقيقة |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. بدء الإضافة** | الضغط على زر | **💰 Add Credits** | **الرد:** `Enter the amount of credits to add:` | `process_add_credits` / `AdminActions.waiting_for_credits_amount` | |
| **2. إدخال الكمية** | إرسال | `100` | **الرد:** `Enter the user ID to add credits to:` | `process_credits_amount` / `AdminActions.waiting_for_credits_user_id` | يتم تخزين الكمية في حالة FSM. |
| **3. إدخال المعرف** | إرسال | `123456789` | **الرد:** `✅ Added 100 credits to user @username (ID: 123456789)` | `process_credits_user_id` | يتم تحديث ملف `premium.json` وإرسال إشعار للمستخدم. |

## 3. إدارة الاشتراك غير المحدود (Set Unlimited)

| الخطوة | الإجراء (المشرف) | الإدخال | الرد (البوت) | الدالة/الحالة | التفاصيل الدقيقة |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. بدء الإعداد** | الضغط على زر | **♾️ Set Unlimited** | **الرد:** `Enter the user ID to set as Unlimited...` | `process_set_unlimited` / `AdminActions.waiting_for_unlimited_user_id` | |
| **2. منح غير محدود** | إرسال | `987654321` | **الرد:** `✅ User @username (ID: 987654321) has been set as Unlimited ♾️` | `process_unlimited_user_id` | يتم تعيين `unlimited: True` في `premium.json` وتصفير الائتمانات. |
| **3. إزالة غير محدود** | إرسال | `remove 987654321` | **الرد:** `✅ User @username (ID: 987654321) has been removed from Limited` | `process_unlimited_user_id` | يتم تعيين `unlimited: False` في `premium.json`. |

## 4. إدارة الاشتراك الزمني (Add Time-Based Premium)

| الخطوة | الإجراء (المشرف) | الإدخال | الرد (البوت) | الدالة/الحالة | التفاصيل الدقيقة |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. بدء الإضافة** | الضغط على زر | **⏰ Add Time-Based Premium** | **الرد:** `Please send the subscription duration in number of minutes or days or hours.` | `process_add_premium` / `AdminActions.waiting_for_duration` | |
| **2. إدخال المدة** | إرسال | `7 days` | **الرد:** `Enter the user ID to add to premium.` | `process_duration` / `AdminActions.waiting_for_user_id` | يتم حساب `timedelta` وتخزينها في حالة FSM. |
| **3. إدخال المعرف** | إرسال | `112233445` | **الرد:** `User @username added successfully to premium. ... Subscription will expire on: [Date]` | `add_premium_user` | يتم حساب تاريخ الانتهاء وتحديث `expires` في `premium.json`. |

## 5. إزالة المستخدم المميز (Remove Premium User)

| الخطوة | الإجراء (المشرف) | الإدخال | الرد (البوت) | الدالة/الحالة | التفاصيل الدقيقة |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. بدء الإزالة** | الضغط على زر | **❌ Remove Premium User** | **الرد:** `Please send the user ID to remove from premium.` | `remove_premium_user` / `AdminActions.waiting_for_user_id_remove` | |
| **2. إدخال المعرف** | إرسال | `112233445` | **الرد:** `User @username (ID: 112233445) has been removed from premium.` | `process_remove_premium` | يتم إزالة سجل المستخدم بالكامل من قائمة `premium_users` في `premium.json`. |

---
*تم إعداد هذا التقرير بناءً على تحليل الكود المصدري لملف `admin.py`.*
