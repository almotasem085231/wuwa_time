# -*- coding: utf-8 -*-
"""
Wuthering Waves Arabic - Master Launcher
Starts both the REST API Server (aiohttp) and the Telegram Bot concurrently,
or individually based on arguments.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path

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
    
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token or bot_token == "your_telegram_bot_token_here":
        print("[-] تنبيه: لم يتم تعيين BOT_TOKEN في ملف .env. تم تشغيل الـ API فقط.")
        print("[*] افتح المتصفح على: http://localhost:8000")
        try:
            api_process.wait()
        except KeyboardInterrupt:
            api_process.terminate()
        return

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
