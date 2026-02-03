# O.T Bot - UI/UX Changes Documentation

## Overview
تم تطبيق مواصفات UI/UX الجديدة على البوت بشكل جراحي مع الحفاظ على منطق العمل الأساسي.

---

## Modified Files

### 1. `cmds.py` - Complete Rewrite
الملف الرئيسي للواجهة والتنقل.

**التغييرات:**
- Banner ثابت لجميع الشاشات (`BANNER_URL`)
- شاشة `/start` الجديدة مع أزرار MY PROFILE, ABOUT, EXIT
- شاشة MY PROFILE مع معلومات المستخدم والاشتراك
- شاشة ABOUT مع معلومات البوت
- شاشة `/cmds` كمركز رئيسي مع GATEWAYS, TOOLS, EXIT
- قسم GATEWAYS مع AUTH, CHARGE, LOOKUP
- قسم TOOLS مع CC GENERATOR, CC SCRAPER
- HOME يعود دائماً إلى `/cmds`
- EXIT يعرض "See you later 🙂" بدون أزرار

### 2. `main.py` - Updated
نقطة الدخول الرئيسية.

**التغييرات:**
- حذف أوامر `/help`, `/menu`, `/command`, `/commands`
- إبقاء `/cmds` فقط كمركز الأوامر
- إضافة `/sup` كـ alias لشاشة MY PROFILE
- إضافة Premium gating لجميع البوابات
- تسجيل البوابات الجديدة:
  - AUTH: `/au`, `/ba`, `/sq`
  - CHARGE: `/Pv`, `/Sh`, `/az`, `/sc`
  - LOOKUP: `/vbv`, `/G3`, `/GP`, `/BP`
- حذف أمر `/mass`

### 3. `mass.py` - Complete Rewrite
نظام الفحص الجماعي.

**التغييرات:**
- لا يوجد أمر `/mass`
- الفحص يبدأ فقط عند رفع ملف `.txt`
- بعد الرفع: اختيار نوع البوابة (AUTH/CHARGE/LOOKUP)
- ثم اختيار بوابة محددة لبدء الفحص
- Premium gating: FREE users يُرفضون
- CANCEL يعود إلى `/cmds`
- ملخص بعد اكتمال الفحص مع زر HOME

---

## Screen Flows

### /start Screen
```
[BANNER IMAGE]

🌅Hello  𓏺 {first_name}

I'm 𝗢.𝗧↯. A Multi Functional Bot With Many Tools and Checker Gateways.
Press /cmds To Know My Features

Buttons:
[MY PROFILE]   [ABOUT]
[EXIT]
```

### MY PROFILE Screen
```
[BANNER IMAGE]

み O.T Bot — User Information
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
UID        : {user_id}
Name       : {first_name}
Username   : @{username}
Profile    : tg://user?id={user_id}

Subscription Information
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
Status     : {ADMIN | UNLIMITED | PREMIUM | FREE}
Credits    : {∞ | N | 0}
Validity   : {MM/DD/YYYY UTC | Unlimited | No Subscription}
Last Check : {HH:MM » MM/DD/YYYY UTC | —}

┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• /Buy VIP Subscription to Unlock All Features.
• DeveBy ↝O.T

Buttons:
[HOME]
```

### /cmds Screen
```
[BANNER IMAGE]

𝗢.𝗧 Bot — Commands Overview
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
Gateways
•  Auth
•  Charge
•  LookUp

Tools
• CC Generator
• CC Scraper

┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
↯   Click Below to View Full Details  ↯

Buttons:
[GATEWAYS]   [TOOLS]
[EXIT]
```

### GATEWAYS Overview
```
[BANNER IMAGE]

Overview Section of 𝗢.𝗧 Bot

•  Auth     ⌁  3 Gates
•  Charge   ⌁  4 Gates
•  LookUp   ⌁  4 Gates

↯  Check Below to View Available Gates.

Buttons:
[AUTH]   [CHARGE]
[LOOKUP]
[HOME]
```

### Mass Flow (Upload .txt)
```
[BANNER IMAGE]

𝗢.𝗧 Bot — File Uploaded
┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉

Your file has been received successfully.

• File name   ⌁  {file_name}
• Total lines ⌁  {total_lines}
• Valid items ⌁  {valid_items}

┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
↯  Select Gate Type To Continue  ↯

Buttons:
[AUTH]   [CHARGE]
[LOOKUP]
[CANCEL]
```

---

## Gateway Commands

### AUTH (3 Gates)
| Command | Name | Status |
|---------|------|--------|
| `/au` | Stripe Auth | PREMIUM |
| `/ba` | Braintree Auth | PREMIUM |
| `/sq` | Square Auth | PREMIUM |

### CHARGE (4 Gates)
| Command | Name | Status |
|---------|------|--------|
| `/Pv` | PayPal CVV | PREMIUM |
| `/Sh` | Square Charge | PREMIUM |
| `/az` | Azathoth (Authorize.Net) | PREMIUM |
| `/sc` | Stripe Charge | PREMIUM |

### LOOKUP (4 Gates)
| Command | Name | Status |
|---------|------|--------|
| `/vbv` | Verify Secure (Braintree 3DS) | PREMIUM |
| `/G3` | Global 3DS | PREMIUM |
| `/GP` | Global Passed | PREMIUM |
| `/BP` | Verify Passed | PREMIUM |

---

## Premium Gating

- **FREE users**: يُرفض الوصول مع رسالة توجيه إلى `/buy`
- **PREMIUM users**: يمكنهم استخدام جميع البوابات (يُخصم كريدت)
- **UNLIMITED users**: وصول غير محدود
- **ADMIN**: وصول كامل بدون قيود

---

## Removed Features

1. ❌ أمر `/mass` - الفحص الجماعي يبدأ فقط برفع ملف
2. ❌ أوامر `/help`, `/menu`, `/command`, `/commands`
3. ❌ زر Mass في شاشة `/cmds`

---

## Notes

- جميع الشاشات تستخدم نفس Banner الثابت
- يُفضل استخدام `edit_media` بدلاً من إرسال رسائل جديدة
- Admin panel لم يُعدل (خارج النطاق)
