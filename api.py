# -*- coding: utf-8 -*-
"""
Wuthering Waves Arabic - Zero-Dependency REST API & Static Server
Runs natively on Python 3 using built-in ThreadingHTTPServer.
Requires ZERO external web frameworks (no fastapi, no uvicorn, no aiohttp compilation needed).
"""

import os
import sys
import hmac
import hashlib
import urllib.parse
import json
import mimetypes
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import requests

# --- Robust .env loading (always runs first) ---
def _load_env():
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and v:
                        os.environ[k] = v  # Always overwrite to pick up latest
        except Exception as e:
            print(f"[WARN] .env load error: {e}")
    # Also try python-dotenv as secondary
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
    except ImportError:
        pass

_load_env()

import database
from time_utils import format_countdown_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wuwa_api")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if BOT_TOKEN:
    logger.info(f"BOT_TOKEN loaded: ...{BOT_TOKEN[-6:]}")
else:
    logger.warning("BOT_TOKEN is NOT set! Images from Telegram will NOT work.")
CACHE_DIR = Path("cache/images")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR = Path("web")

def fetch_and_cache_telegram_file(file_id: str) -> Optional[Path]:
    """Downloads file from Telegram Bot API and caches it locally."""
    if not BOT_TOKEN:
        logger.warning(f"Cannot fetch image: BOT_TOKEN is empty!")
        return None
    if not file_id or not file_id.strip():
        logger.warning(f"Cannot fetch image: file_id is empty!")
        return None
    file_id = file_id.strip()
    cached_file = CACHE_DIR / f"{file_id}.jpg"
    if cached_file.exists() and cached_file.stat().st_size > 0:
        return cached_file
    try:
        url_get_file = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url_get_file, timeout=10)
        if resp.status_code != 200:
            logger.error(f"Telegram getFile failed: status={resp.status_code}, file_id={file_id[:20]}")
            return None
        data = resp.json()
        if not data.get("ok"):
            logger.error(f"Telegram getFile not ok: {data.get('description')}, file_id={file_id[:20]}")
            return None
        file_path_tg = data["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_tg}"
        img_resp = requests.get(download_url, timeout=15)
        if img_resp.status_code == 200 and len(img_resp.content) > 0:
            with open(cached_file, "wb") as f:
                f.write(img_resp.content)
            logger.info(f"Cached image for file_id={file_id[:20]}... size={len(img_resp.content)} bytes")
            return cached_file
        else:
            logger.error(f"Image download failed: status={img_resp.status_code}")
    except Exception as e:
        logger.error(f"Exception caching Telegram image: {e}")
    return None

def get_default_section_image(section: str) -> Path:
    mapping = {
        "banner": WEB_DIR / "assets" / "images" / "banner_real.jpg",
        "stygian": WEB_DIR / "assets" / "images" / "stygian_real.jpg",
        "spiral_abyss": WEB_DIR / "assets" / "images" / "tower_real.jpg",
        "events": WEB_DIR / "assets" / "images" / "hero_bg.jpg",
    }
    path = mapping.get(section, WEB_DIR / "assets" / "images" / "banner_real.jpg")
    if not path.exists():
        return WEB_DIR / "assets" / "images" / "banner_real.jpg"
    return path


class WuWaApiHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Global CORS headers
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, file_path: Path, max_age: int = 3600):
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File Not Found")
            return
        
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", f"public, max-age={max_age}")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            logger.error(f"Error serving file {file_path}: {e}")
            self.send_error(500, "Error serving file")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        # API Endpoints
        if path == "/api/health":
            now_utc = datetime.now(timezone.utc)
            try:
                conn = database.get_connection()
                conn.execute("SELECT 1")
                conn.close()
                db_status = "connected"
            except Exception as e:
                db_status = f"error: {str(e)}"

            return self.send_json({
                "status": "ok",
                "database": db_status,
                "utc_time": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": "1.0.0",
                "telegram_configured": bool(BOT_TOKEN)
            })

        if path == "/api/debug":
            # Shows DB image_file_ids and BOT_TOKEN status (safe: hides token)
            try:
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT section, image_file_id FROM content WHERE section IN ('banner','stygian','spiral_abyss') ORDER BY id DESC")
                rows = cursor.fetchall()
                conn.close()
                sections_info = {r["section"]: {"file_id_set": bool(r["image_file_id"] and r["image_file_id"].strip()), "file_id_len": len(r["image_file_id"] or "")} for r in rows}
            except Exception as e:
                sections_info = {"error": str(e)}
            return self.send_json({
                "bot_token_configured": bool(BOT_TOKEN),
                "bot_token_tail": f"...{BOT_TOKEN[-6:]}" if BOT_TOKEN else "NOT SET",
                "sections": sections_info,
                "cache_files": [f.name for f in CACHE_DIR.iterdir() if f.is_file()] if CACHE_DIR.exists() else []
            })

        if path == "/api/content":
            try:
                data = database.get_all_content_data()
                return self.send_json(data)
            except Exception as e:
                logger.error(f"Error fetching content: {e}")
                return self.send_json({"error": "Failed to fetch content"}, status=500)

        if path == "/api/content/banner":
            content = database.get_content_by_section("banner")
            if not content:
                return self.send_json({"error": "Banner content not found"}, status=404)
            return self.send_json(content)

        if path == "/api/content/stygian":
            content = database.get_content_by_section("stygian")
            if not content:
                return self.send_json({"error": "Stygian content not found"}, status=404)
            return self.send_json(content)

        if path == "/api/content/spiral_abyss":
            content = database.get_content_by_section("spiral_abyss")
            if not content:
                return self.send_json({"error": "Spiral Abyss content not found"}, status=404)
            return self.send_json(content)

        if path == "/api/content/events":
            try:
                data = database.get_active_events()
                return self.send_json(data)
            except Exception as e:
                logger.error(f"Error fetching events: {e}")
                return self.send_json({"error": "Failed to fetch events"}, status=500)

        if path.startswith("/api/image/file/"):
            file_id = path.replace("/api/image/file/", "").strip()
            cached_path = fetch_and_cache_telegram_file(file_id)
            if cached_path and cached_path.exists():
                return self.send_file_response(cached_path, max_age=86400)
            return self.send_file_response(get_default_section_image("banner"), max_age=3600)

        if path.startswith("/api/image/"):
            section = path.replace("/api/image/", "").strip()
            content = database.get_content_by_section(section)
            file_id = content.get("image_file_id") if content else None
            if file_id:
                cached_path = fetch_and_cache_telegram_file(file_id)
                if cached_path and cached_path.exists():
                    return self.send_file_response(cached_path, max_age=3600)
            return self.send_file_response(get_default_section_image(section), max_age=3600)

        # Static files serving from /web directory
        if path == "/" or path == "/index.html":
            return self.send_file_response(WEB_DIR / "index.html", max_age=60)

        # Assets, css, js
        rel_path = path.lstrip("/")
        target_file = WEB_DIR / rel_path
        if target_file.exists() and target_file.is_file():
            return self.send_file_response(target_file, max_age=3600)

        # Fallback to index.html for SPA routes
        if (WEB_DIR / "index.html").exists():
            return self.send_file_response(WEB_DIR / "index.html", max_age=60)

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/auth/verify-telegram":
            if not BOT_TOKEN:
                return self.send_json({"valid": False, "error": "BOT_TOKEN not configured on server"})

            content_len = int(self.headers.get("Content-Length", 0))
            if content_len == 0:
                return self.send_json({"error": "Missing body"}, status=400)

            try:
                body_raw = self.rfile.read(content_len).decode("utf-8")
                body = json.loads(body_raw)
                init_data = body.get("init_data", "")
                if not init_data:
                    return self.send_json({"error": "Missing init_data"}, status=400)

                parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
                received_hash = parsed_data.pop("hash", None)
                if not received_hash:
                    return self.send_json({"valid": False, "error": "Missing hash parameter"})

                data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
                secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
                calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
                is_valid = hmac.compare_digest(calculated_hash, received_hash)

                user_info = None
                if is_valid and "user" in parsed_data:
                    user_info = json.loads(parsed_data["user"])

                return self.send_json({"valid": is_valid, "user": user_info})
            except Exception as e:
                logger.error(f"Error verifying telegram auth: {e}")
                return self.send_json({"valid": False, "error": str(e)})

        self.send_error(404, "Not Found")


class ThreadedServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(host: str = "0.0.0.0", port: int = 8000):
    database.init_db()
    server_address = (host, port)
    try:
        httpd = ThreadedServer(server_address, WuWaApiHandler)
    except Exception:
        # Fallback to 127.0.0.1 if 0.0.0.0 is restricted by local Windows firewall
        httpd = ThreadedServer(("127.0.0.1", port), WuWaApiHandler)
    print(f"🌊 Wuthering Waves Arabic Server running on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    run_server(host=host, port=port)
