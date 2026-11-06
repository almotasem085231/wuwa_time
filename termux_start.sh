#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Wuthering Waves Arabic - Termux Quick Launcher
# سكربت تشغيل المنصة التلقائي على هواتف الأندرويد عبر Termux
# ==============================================================================

set -e

echo ""
echo "============================================================"
echo "   🌊 تشغيل Wuthering Waves Arabic على هاتف Android (Termux) 🌊"
echo "============================================================"
echo ""

# 1. تثبيت بايثون وحزمة aiohttp الجاهزة من Termux لتفادي أخطاء بايثون 3.13
echo "[1/4] التحقق من بيئة بايثون وحزم Termux المسبقة الصنع..."
pkg update -y || true
pkg install -y python python-aiohttp || true

# 2. تثبيت باقي الحزم دون إعادة بناء aiohttp القديمة
echo "[2/4] تثبيت مكتبات المشروع (requests, python-dotenv, aiogram)..."
pip install requests python-dotenv Babel magic-filter certifi --quiet
pip install --no-deps aiogram==2.25.2 --quiet

# 3. فحص ملف الإعدادات
echo "[3/4] التحقق من ملف الإعدادات .env..."
if [ ! -f .env ]; then
    echo "[!] ملف .env غير موجود. يتم إنشاء نسخة من .env.example..."
    cp .env.example .env
    echo "[*] تذكير: يمكنك تعديل ملف .env وكتابة BOT_TOKEN الخاص بك."
fi

# فحص وتثبيت Cloudflare Tunnel إن رغب المستخدم
if ! command -v cloudflared &> /dev/null; then
    echo "[*] نصيحة: لتوصيل السيرفر بالإنترنت مجاناً، يمكنك تثبيت cloudflared:"
    echo "    pkg install cloudflared"
    echo "    cloudflared tunnel --url http://localhost:8000"
fi

# 4. تشغيل المشغل الموحد
echo "[4/4] تشغيل البوت والـ API معاً..."
python start.py
