FROM mcr.microsoft.com/devcontainers/python:3.11

# تثبيت متطلبات النظام الإضافية إذا لزم الأمر
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /workspace

# نسخ ملف المتطلبات وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# الأمر الافتراضي عند تشغيل الحاوية
CMD ["python", "main.py"]
