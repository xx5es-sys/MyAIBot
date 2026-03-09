FROM mcr.microsoft.com/devcontainers/python:3.11

# تثبيت متطلبات النظام الأساسية
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /workspace

# نسخ ملف المتطلبات وتثبيت المكتبات تلقائياً أثناء بناء الحاوية
# نستخدم --no-cache-dir لضمان الحصول على أحدث النسخ وتوفير المساحة
COPY requirements.txt .
RUN pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt
