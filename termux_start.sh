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

# التأكد من تثبيت الحزم المطلوبة
echo "[1/4] التحقق من بيئة بايثون والمكتبات..."
if ! command -v python &> /dev/null; then
    echo "[+] تثبيت Python..."
    pkg update -y && pkg install -y python
fi

echo "[2/4] تثبيت مكتبات المشروع (aiohttp, requests, python-dotenv, aiogram)..."
pip install aiohttp requests python-dotenv aiogram==2.25.2 --quiet

# فحص ملف الإعدادات
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

# تشغيل المشغل الموحد
echo "[4/4] تشغيل البوت والـ API معاً..."
python start.py
