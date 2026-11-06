# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from time_utils import format_countdown_data

DB_PATH = os.getenv("DB_PATH", "genshin_bot.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db(owner_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section TEXT,
        title TEXT,
        name TEXT,
        end_time_asia TEXT,
        end_time_europe TEXT,
        end_time_america TEXT,
        description TEXT,
        image_file_id TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS server_offsets (
        server TEXT PRIMARY KEY,
        offset_hours INTEGER
    )
    """)
    
    conn.commit()
    
    if owner_id:
        cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (owner_id,))
    
    cursor.execute("INSERT OR IGNORE INTO server_offsets (server, offset_hours) VALUES (?, ?)", ('asia', 8))
    cursor.execute("INSERT OR IGNORE INTO server_offsets (server, offset_hours) VALUES (?, ?)", ('europe', 1))
    cursor.execute("INSERT OR IGNORE INTO server_offsets (server, offset_hours) VALUES (?, ?)", ('america', -5))
    conn.commit()
    
    # Check if content table is empty; if so, populate with initial real Wuthering Waves content
    cursor.execute("SELECT COUNT(*) as count FROM content")
    row = cursor.fetchone()
    if row and row['count'] == 0:
        seed_default_wuwa_content(conn)
        
    conn.close()

def seed_default_wuwa_content(conn: sqlite3.Connection):
    """
    Seeds initial realistic Wuthering Waves content with upcoming expiry dates
    so the web UI and countdowns display rich authentic gaming content immediately.
    """
    now = datetime.now(timezone.utc)
    # Set dates relative to now so countdowns are actively ticking
    asia_end_banner = (now + timedelta(days=14, hours=10, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    europe_end_banner = (now + timedelta(days=14, hours=17, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    america_end_banner = (now + timedelta(days=14, hours=23, minutes=45)).strftime("%Y-%m-%d %H:%M:%S")

    asia_end_stygian = (now + timedelta(days=21, hours=8)).strftime("%Y-%m-%d %H:%M:%S")
    europe_end_stygian = (now + timedelta(days=21, hours=15)).strftime("%Y-%m-%d %H:%M:%S")
    america_end_stygian = (now + timedelta(days=21, hours=21)).strftime("%Y-%m-%d %H:%M:%S")

    asia_end_tower = (now + timedelta(days=9, hours=4, minutes=12)).strftime("%Y-%m-%d %H:%M:%S")
    europe_end_tower = (now + timedelta(days=9, hours=11, minutes=12)).strftime("%Y-%m-%d %H:%M:%S")
    america_end_tower = (now + timedelta(days=9, hours=17, minutes=12)).strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.cursor()
    # Banner: Wuthering Waves Current Banner
    cursor.execute("""
        INSERT INTO content (section, title, name, end_time_asia, end_time_europe, end_time_america, description, image_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'banner',
        'بنرات الإصدار الحالي - النصف الأول',
        '',
        asia_end_banner,
        europe_end_banner,
        america_end_banner,
        '',
        None
    ))

    # Stygian / Ship Event
    cursor.execute("""
        INSERT INTO content (section, title, name, end_time_asia, end_time_europe, end_time_america, description, image_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'stygian',
        'السفينة — Stygian Sea',
        'Stygian Sea Expedition',
        asia_end_stygian,
        europe_end_stygian,
        america_end_stygian,
        '',
        None
    ))

    # Tower / Spiral Abyss (Tower of Adversity)
    cursor.execute("""
        INSERT INTO content (section, title, name, end_time_asia, end_time_europe, end_time_america, description, image_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'spiral_abyss',
        'التاور — Tower of Adversity',
        'Tower of Adversity Reset',
        asia_end_tower,
        europe_end_tower,
        america_end_tower,
        '',
        None
    ))

    # Events
    events_data = [
        ("حدث تسجيل الدخول اليومي - هدايا الروفر", (now + timedelta(days=7, hours=12)).strftime("%Y-%m-%d %H:%M:%S")),
        ("محاكاة المعارك التكتيكية (Tactical Hologram)", (now + timedelta(days=12, hours=18)).strftime("%Y-%m-%d %H:%M:%S")),
        ("حدث صيد الصدى المميز (Echo Hunting Rally)", (now + timedelta(days=16, hours=22)).strftime("%Y-%m-%d %H:%M:%S"))
    ]
    for name, end_time in events_data:
        cursor.execute("""
            INSERT INTO content (section, name, end_time_asia)
            VALUES (?, ?, ?)
        """, ('events', name, end_time))

    conn.commit()

def format_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "section": row["section"],
        "title": row["title"] or "",
        "name": row["name"] or "",
        "description": row["description"] or "",
        "image_file_id": row["image_file_id"] or "",
        "servers": {
            "asia": format_countdown_data(row["end_time_asia"]),
            "europe": format_countdown_data(row["end_time_europe"]),
            "america": format_countdown_data(row["end_time_america"])
        }
    }

def get_content_by_section(section: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content WHERE section = ? ORDER BY id DESC LIMIT 1", (section,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return format_row(row)

def get_active_events() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    # Auto-cleanup matching wuwa.py: delete events expired in Asia server
    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("DELETE FROM content WHERE section='events' AND end_time_asia <= ?", (now_str,))
    conn.commit()
    
    cursor.execute("SELECT * FROM content WHERE section='events' ORDER BY end_time_asia ASC")
    rows = cursor.fetchall()
    conn.close()
    
    events = []
    for r in rows:
        events.append({
            "id": r["id"],
            "section": "events",
            "title": r["title"] or "",
            "name": r["name"] or "",
            "description": r["description"] or "",
            "image_file_id": r["image_file_id"] or "",
            "countdown": format_countdown_data(r["end_time_asia"])
        })
    return events

def get_all_content_data() -> Dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    return {
        "timestamp_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "banner": get_content_by_section("banner"),
        "stygian": get_content_by_section("stygian"),
        "spiral_abyss": get_content_by_section("spiral_abyss"),
        "events": get_active_events()
    }

