# محاكاة تفاعلية: سيناريوهات المشرف وإدارة الائتمانات

هذا القسم يوضح محاكاة تفاعلية لجميع الأوامر والأزرار المتاحة للمشرف (Admin) لإدارة الاشتراكات والائتمانات.

## 1. لوحة تحكم المشرف (الأمر: /admin)

**السيناريو:** المشرف يرسل الأمر `/admin` للوصول إلى لوحة التحكم.

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. الدخول** | إرسال الأمر `/admin` | **الرد:** `Admin Menu:` مع أزرار الإدارة. | `admin_commands` |
| **2. الأزرار المتاحة** | - | **الأزرار:** `⏰ Add Time-Based Premium`، `💰 Add Credits`، `♾️ Set Unlimited`، `👥 View Premium Users`، `❌ Remove Premium User`. | `admin_commands` |

## 2. إدارة الائتمانات (Credits)

**السيناريو:** المشرف يضيف 100 ائتمان للمستخدم (ID: 123456789).

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. بدء الإضافة** | الضغط على زر **💰 Add Credits** | **الرد:** `Enter the amount of credits to add:` | `process_add_credits` |
| **2. إدخال الكمية** | إرسال `100` | **الرد:** `Enter the user ID to add credits to:` | `process_credits_amount` |
| **3. إدخال المعرف** | إرسال `123456789` | **الرد:** `✅ Added 100 credits to user @username (ID: 123456789)` | `process_credits_user_id` |
| **4. إشعار المستخدم** | - | **رسالة للمستخدم (123456789):** `🎉 You have received 100 credits!` | `bot.send_message` (ضمن `process_credits_user_id`) |

## 3. إدارة الاشتراك غير المحدود (Unlimited)

**السيناريو أ:** المشرف يمنح المستخدم (ID: 987654321) اشتراكًا غير محدود.

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. بدء الإعداد** | الضغط على زر **♾️ Set Unlimited** | **الرد:** `Enter the user ID to set as Unlimited (or send 'remove USER_ID' to remove unlimited):` | `process_set_unlimited` |
| **2. إدخال المعرف** | إرسال `987654321` | **الرد:** `✅ User @username (ID: 987654321) has been set as Unlimited ♾️` | `process_unlimited_user_id` |
| **3. إشعار المستخدم** | - | **رسالة للمستخدم (987654321):** `🎉 Congratulations! You now have Unlimited access!` | `bot.send_message` (ضمن `process_unlimited_user_id`) |

**السيناريو ب:** المشرف يزيل الاشتراك غير المحدود من المستخدم (ID: 987654321).

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. إزالة** | إرسال `remove 987654321` | **الرد:** `✅ User @username (ID: 987654321) has been removed from Limited` | `process_unlimited_user_id` |

## 4. إدارة الاشتراك الزمني (Time-Based Premium)

**السيناريو:** المشرف يضيف اشتراكًا زمنيًا لمدة 7 أيام للمستخدم (ID: 112233445).

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. بدء الإضافة** | الضغط على زر **⏰ Add Time-Based Premium** | **الرد:** `Please send the subscription duration in number of minutes or days or hours.` | `process_add_premium` |
| **2. إدخال المدة** | إرسال `7 days` | **الرد:** `Enter the user ID to add to premium.` | `process_duration` |
| **3. إدخال المعرف** | إرسال `112233445` | **الرد:** `User @username added successfully to premium. ... Subscription will expire on: [Date]` | `add_premium_user` |

## 5. عرض وإزالة المستخدمين المميزين

| الخطوة | الإجراء (المشرف) | الرد (البوت) | الدالة المرتبطة |
| :--- | :--- | :--- | :--- |
| **1. عرض المستخدمين** | الضغط على زر **👥 View Premium Users** | **تحديث الرسالة:** قائمة مفصلة بجميع المستخدمين المميزين (الحالة، الائتمانات، تاريخ الانتهاء، الوقت المتبقي). | `view_premium_users` |
| **2. إزالة مستخدم** | الضغط على زر **❌ Remove Premium User** | **الرد:** `Please send the user ID to remove from premium.` | `remove_premium_user` |
| **3. تأكيد الإزالة** | إرسال `112233445` | **الرد:** `User @username (ID: 112233445) has been removed from premium.` | `process_remove_premium` |

---
*تم إعداد هذا التقرير بناءً على تحليل الكود المصدري لملف `admin.py`.*
