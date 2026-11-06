# -*- coding: utf-8 -*-
"""
Wuthering Waves Arabic - Master Launcher
Starts both the REST API Server (api.py) and the Telegram Bot (wuwa.py) concurrently,
or individually based on arguments.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fallback parser for .env
env_file = Path(".env")
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    val = v.strip().strip('"').strip("'")
                    os.environ.setdefault(k.strip(), val)
    except Exception as e:
        print(f"[!] Error reading .env: {e}")

def print_banner():
    banner = """
============================================================
   🌊 WUTHERING WAVES ARABIC - منصة موجات ووزيرينغ بالعربي 🌊
   Website, REST API & Telegram Mini App
============================================================
    """
    print(banner)

def run_api():
    print("[+] تشغيل سيرفر الـ API على المنفذ 8000...")
    subprocess.run([sys.executable, "api.py"])

def run_bot():
    print("[+] تشغيل بوت التليغرام (wuwa.py)...")
    subprocess.run([sys.executable, "wuwa.py"])

def run_all():
    print("[+] تشغيل الـ API والبوت معاً...")
    api_process = subprocess.Popen([sys.executable, "api.py"])
    
    time.sleep(1.5)
    
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token or bot_token == "your_telegram_bot_token_here":
        print("[-] تنبيه: لم يتم العثور على BOT_TOKEN في ملف .env. تم تشغيل الـ API فقط.")
        print("[*] افتح المتصفح على: http://localhost:8000")
        try:
            api_process.wait()
        except KeyboardInterrupt:
            api_process.terminate()
        return

    print(f"[+] تم التحقق من توكن البوت بنجاح. جاري تشغيل بوت التليغرام...")
    bot_process = subprocess.Popen([sys.executable, "wuwa.py"])
    
    try:
        api_process.wait()
        bot_process.wait()
    except KeyboardInterrupt:
        print("\n[!] جاري إيقاف السيرفرات...")
        api_process.terminate()
        bot_process.terminate()

if __name__ == "__main__":
    print_banner()
    parser = argparse.ArgumentParser(description="Wuthering Waves Arabic Runner")
    parser.add_argument("--mode", choices=["all", "api", "bot"], default="all", help="Launch mode")
    args = parser.parse_args()

    if args.mode == "api":
        run_api()
    elif args.mode == "bot":
        run_bot()
    else:
        run_all()
