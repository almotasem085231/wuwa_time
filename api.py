# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import urllib.parse
import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from aiohttp import web
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(".env")
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

import database
from time_utils import format_countdown_data

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("wuwa_api")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CACHE_DIR = Path("cache/images")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR = Path("web")

# CORS Middleware for aiohttp
@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        response = web.Response(status=200)
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
        except Exception as e:
            logger.error(f"Internal server error: {e}")
            response = web.json_response({"error": "Internal Server Error", "detail": str(e)}, status=500)

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

routes = web.RouteTableDef()

@routes.get("/api/health")
async def health_check(request):
    now_utc = datetime.now(timezone.utc)
    try:
        conn = database.get_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB health check error: {e}")
        db_status = f"error: {str(e)}"

    return web.json_response({
        "status": "ok",
        "database": db_status,
        "utc_time": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "1.0.0",
        "telegram_configured": bool(BOT_TOKEN)
    })

@routes.get("/api/content")
async def get_all_content(request):
    try:
        data = database.get_all_content_data()
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Error fetching all content: {e}")
        return web.json_response({"error": "Failed to fetch content"}, status=500)

@routes.get("/api/content/banner")
async def get_banner(request):
    content = database.get_content_by_section("banner")
    if not content:
        return web.json_response({"error": "Banner content not found"}, status=404)
    return web.json_response(content)

@routes.get("/api/content/stygian")
async def get_stygian(request):
    content = database.get_content_by_section("stygian")
    if not content:
        return web.json_response({"error": "Stygian content not found"}, status=404)
    return web.json_response(content)

@routes.get("/api/content/spiral_abyss")
async def get_spiral_abyss(request):
    content = database.get_content_by_section("spiral_abyss")
    if not content:
        return web.json_response({"error": "Spiral Abyss content not found"}, status=404)
    return web.json_response(content)

@routes.get("/api/content/events")
async def get_events(request):
    try:
        data = database.get_active_events()
        return web.json_response(data)
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return web.json_response({"error": "Failed to fetch events"}, status=500)

def fetch_and_cache_telegram_file(file_id: str) -> Optional[Path]:
    """Downloads file from Telegram Bot API and caches it locally."""
    if not BOT_TOKEN or not file_id:
        return None
    cached_file = CACHE_DIR / f"{file_id}.jpg"
    if cached_file.exists() and cached_file.stat().st_size > 0:
        return cached_file
    try:
        url_get_file = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url_get_file, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get("ok"):
            return None
        file_path_tg = data["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path_tg}"
        img_resp = requests.get(download_url, timeout=15)
        if img_resp.status_code == 200 and len(img_resp.content) > 0:
            with open(cached_file, "wb") as f:
                f.write(img_resp.content)
            logger.info(f"Cached image for file_id {file_id} successfully.")
            return cached_file
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

@routes.get("/api/image/file/{file_id}")
async def get_image_by_file_id(request):
    file_id = request.match_info.get("file_id")
    cached_path = fetch_and_cache_telegram_file(file_id)
    if cached_path and cached_path.exists():
        return web.FileResponse(cached_path, headers={"Cache-Control": "public, max-age=86400"})
    default_img = get_default_section_image("banner")
    return web.FileResponse(default_img, headers={"Cache-Control": "public, max-age=3600"})

@routes.get("/api/image/{section}")
async def get_image_by_section(request):
    section = request.match_info.get("section")
    content = database.get_content_by_section(section)
    file_id = content.get("image_file_id") if content else None
    if file_id:
        cached_path = fetch_and_cache_telegram_file(file_id)
        if cached_path and cached_path.exists():
            return web.FileResponse(cached_path, headers={"Cache-Control": "public, max-age=3600"})
    default_img = get_default_section_image(section)
    return web.FileResponse(default_img, headers={"Cache-Control": "public, max-age=3600"})

@routes.post("/api/auth/verify-telegram")
async def verify_telegram_auth(request):
    if not BOT_TOKEN:
        return web.json_response({"valid": False, "error": "BOT_TOKEN not configured on server"})
    try:
        body = await request.json()
        init_data = body.get("init_data", "")
        if not init_data:
            return web.json_response({"error": "Missing init_data"}, status=400)
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return web.json_response({"valid": False, "error": "Missing hash parameter"})
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        is_valid = hmac.compare_digest(calculated_hash, received_hash)
        user_info = None
        if is_valid and "user" in parsed_data:
            user_info = json.loads(parsed_data["user"])
        return web.json_response({"valid": is_valid, "user": user_info})
    except Exception as e:
        logger.error(f"Error verifying telegram auth: {e}")
        return web.json_response({"valid": False, "error": str(e)})

@routes.get("/")
async def serve_index(request):
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="Wuthering Waves Arabic API is running.")

def create_app():
    database.init_db()
    app = web.Application(middlewares=[cors_middleware])
    app.add_routes(routes)
    
    # Static files
    if WEB_DIR.exists():
        assets_dir = WEB_DIR / "assets"
        css_dir = WEB_DIR / "css"
        js_dir = WEB_DIR / "js"
        if assets_dir.exists():
            app.router.add_static("/assets", assets_dir)
        if css_dir.exists():
            app.router.add_static("/css", css_dir)
        if js_dir.exists():
            app.router.add_static("/js", js_dir)
            
    return app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"🌊 Starting Wuthering Waves Arabic Server on http://{host}:{port}")
    app = create_app()
    web.run_app(app, host=host, port=port, print=None)
