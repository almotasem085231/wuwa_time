# -*- coding: utf-8 -*-
import os
import hmac
import hashlib
import urllib.parse
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import requests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback parser if python-dotenv is not installed
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

app = FastAPI(
    title="Wuthering Waves Arabic API",
    description="REST API for Wuthering Waves Arabic Website & Telegram Mini App",
    version="1.0.0"
)

# Enable CORS for Netlify, Telegram WebView, localhost, and tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to ensure DB is initialized
@app.on_event("startup")
def on_startup():
    database.init_db()
    logger.info("Wuthering Waves Arabic API started successfully.")

@app.get("/api/health")
def health_check():
    now_utc = datetime.now(timezone.utc)
    try:
        conn = database.get_connection()
        conn.execute("SELECT 1")
        conn.close()
        db_status = "connected"
    except Exception as e:
        logger.error(f"DB health check error: {e}")
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "database": db_status,
        "utc_time": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "version": "1.0.0",
        "telegram_configured": bool(BOT_TOKEN)
    }

@app.get("/api/content")
def get_all_content():
    try:
        return database.get_all_content_data()
    except Exception as e:
        logger.error(f"Error fetching all content: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch content")

@app.get("/api/content/banner")
def get_banner():
    content = database.get_content_by_section("banner")
    if not content:
        raise HTTPException(status_code=404, detail="Banner content not found")
    return content

@app.get("/api/content/stygian")
def get_stygian():
    content = database.get_content_by_section("stygian")
    if not content:
        raise HTTPException(status_code=404, detail="Stygian content not found")
    return content

@app.get("/api/content/spiral_abyss")
def get_spiral_abyss():
    content = database.get_content_by_section("spiral_abyss")
    if not content:
        raise HTTPException(status_code=404, detail="Spiral Abyss content not found")
    return content

@app.get("/api/content/events")
def get_events():
    try:
        return database.get_active_events()
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch events")

def fetch_and_cache_telegram_file(file_id: str) -> Optional[Path]:
    """
    Downloads file from Telegram Bot API and caches it locally.
    Returns the Path to the cached file if successful, otherwise None.
    """
    if not BOT_TOKEN or not file_id:
        return None
    
    # Check if already cached
    cached_file = CACHE_DIR / f"{file_id}.jpg"
    if cached_file.exists() and cached_file.stat().st_size > 0:
        return cached_file
    
    try:
        url_get_file = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        resp = requests.get(url_get_file, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Telegram getFile failed with status {resp.status_code}")
            return None
        
        data = resp.json()
        if not data.get("ok"):
            logger.warning(f"Telegram getFile response not ok: {data}")
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
    """Returns local fallback real game image for given section"""
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

@app.get("/api/image/file/{file_id}")
def get_image_by_file_id(file_id: str):
    cached_path = fetch_and_cache_telegram_file(file_id)
    if cached_path and cached_path.exists():
        return FileResponse(
            cached_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}
        )
    # If not found or failed, return default real banner
    default_img = get_default_section_image("banner")
    return FileResponse(default_img, media_type="image/jpeg")

@app.get("/api/image/{section}")
def get_image_by_section(section: str):
    # Lookup in database
    content = database.get_content_by_section(section)
    file_id = content.get("image_file_id") if content else None
    
    if file_id:
        cached_path = fetch_and_cache_telegram_file(file_id)
        if cached_path and cached_path.exists():
            return FileResponse(
                cached_path,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"}
            )
            
    # Default high-res official game visual
    default_img = get_default_section_image(section)
    media_type = "image/jpeg" if default_img.suffix in [".jpg", ".jpeg"] else "image/png"
    return FileResponse(default_img, media_type=media_type)

@app.post("/api/auth/verify-telegram")
async def verify_telegram_auth(request: Request):
    """
    Validates Telegram WebApp initData string securely using HMAC-SHA256
    as required by Telegram Mini Apps specification.
    """
    if not BOT_TOKEN:
        return {"valid": False, "error": "BOT_TOKEN not configured on server"}
    
    body = await request.json()
    init_data = body.get("init_data", "")
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing init_data")
        
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return {"valid": False, "error": "Missing hash parameter"}
        
        # Build check string sorted alphabetically
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        # Secret key: HMAC-SHA256 of bot token with key "WebAppData"
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        is_valid = hmac.compare_digest(calculated_hash, received_hash)
        
        user_info = None
        if is_valid and "user" in parsed_data:
            user_info = json.loads(parsed_data["user"])
            
        return {
            "valid": is_valid,
            "user": user_info
        }
    except Exception as e:
        logger.error(f"Error verifying telegram auth: {e}")
        return {"valid": False, "error": str(e)}

# Serve static web frontend if directory exists
if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory="web/assets"), name="assets")
    app.mount("/css", StaticFiles(directory="web/css"), name="css")
    app.mount("/js", StaticFiles(directory="web/js"), name="js")
    
    @app.get("/")
    def serve_index():
        return FileResponse(WEB_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Wuthering Waves Arabic API on {host}:{port}")
    uvicorn.run("api:app", host=host, port=port, reload=False)
