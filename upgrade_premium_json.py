#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
سكريبت ترقية premium.json من النظام القديم إلى نظام الكريدت
يضيف الحقول الجديدة: credits, unlimited, last_chk
"""

import json
import os
import shutil
from datetime import datetime

def upgrade_premium_json(filename='premium.json'):
    """
    ترقية ملف premium.json إلى النظام الجديد
    """
    
    # التحقق من وجود الملف
    if not os.path.exists(filename):
        print(f"❌ الملف {filename} غير موجود")
        return False
    
    # إنشاء نسخة احتياطية
    backup_filename = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filename, backup_filename)
    print(f"✅ تم إنشاء نسخة احتياطية: {backup_filename}")
    
    try:
        # قراءة الملف
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📖 تم قراءة الملف بنجاح")
        
        # التحقق من الهيكل
        if 'premium_users' not in data:
            data['premium_users'] = []
        
        # تحديث كل مستخدم
        updated_count = 0
        for user in data['premium_users']:
            modified = False
            
            # إضافة credits إذا لم يكن موجوداً
            if 'credits' not in user:
                user['credits'] = 0
                modified = True
            
            # إضافة unlimited إذا لم يكن موجوداً
            if 'unlimited' not in user:
                user['unlimited'] = False
                modified = True
            
            # إضافة last_chk إذا لم يكن موجوداً
            if 'last_chk' not in user:
                user['last_chk'] = '—'
                modified = True
            
            # التأكد من وجود الحقول الأساسية
            user.setdefault('user_id', '—')
            user.setdefault('username', '—')
            user.setdefault('since', '—')
            user.setdefault('expires', '—')
            
            if modified:
                updated_count += 1
        
        # حفظ الملف المحدث
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ تم تحديث {updated_count} مستخدم")
        print(f"✅ تم حفظ الملف المحدث: {filename}")
        
        # عرض ملخص
        print("\n📊 ملخص الترقية:")
        print(f"   - إجمالي المستخدمين: {len(data['premium_users'])}")
        print(f"   - المستخدمين المحدثين: {updated_count}")
        
        # عرض عينة من البيانات
        if data['premium_users']:
            print("\n📝 عينة من البيانات المحدثة:")
            sample = data['premium_users'][0]
            print(f"   User ID: {sample.get('user_id')}")
            print(f"   Username: {sample.get('username')}")
            print(f"   Credits: {sample.get('credits')}")
            print(f"   Unlimited: {sample.get('unlimited')}")
            print(f"   Last Check: {sample.get('last_chk')}")
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في قراءة JSON: {e}")
        print(f"   استعادة النسخة الاحتياطية...")
        shutil.copy2(backup_filename, filename)
        return False
    
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
        print(f"   استعادة النسخة الاحتياطية...")
        shutil.copy2(backup_filename, filename)
        return False

def validate_premium_json(filename='premium.json'):
    """
    التحقق من صحة ملف premium.json بعد الترقية
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n🔍 التحقق من صحة الملف...")
        
        # التحقق من الهيكل الأساسي
        if 'premium_users' not in data:
            print("❌ الحقل 'premium_users' غير موجود")
            return False
        
        # التحقق من كل مستخدم
        required_fields = ['user_id', 'username', 'credits', 'unlimited', 'since', 'expires', 'last_chk']
        errors = []
        
        for i, user in enumerate(data['premium_users']):
            for field in required_fields:
                if field not in user:
                    errors.append(f"المستخدم {i}: الحقل '{field}' غير موجود")
            
            # التحقق من أنواع البيانات
            if not isinstance(user.get('credits', 0), int):
                errors.append(f"المستخدم {i}: 'credits' يجب أن يكون رقماً")
            
            if not isinstance(user.get('unlimited', False), bool):
                errors.append(f"المستخدم {i}: 'unlimited' يجب أن يكون true/false")
            
            # التحقق من القيم السالبة
            if user.get('credits', 0) < 0:
                errors.append(f"المستخدم {i}: 'credits' لا يمكن أن يكون سالباً")
        
        if errors:
            print("❌ تم العثور على أخطاء:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ الملف صحيح ومطابق للمواصفات")
        return True
    
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 سكريبت ترقية premium.json إلى نظام الكريدت")
    print("=" * 60)
    print()
    
    # الترقية
    success = upgrade_premium_json('premium.json')
    
    if success:
        # التحقق
        validate_premium_json('premium.json')
        print()
        print("=" * 60)
        print("✅ تمت الترقية بنجاح!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ فشلت الترقية. تم استعادة النسخة الاحتياطية.")
        print("=" * 60)

