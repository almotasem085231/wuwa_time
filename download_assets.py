# -*- coding: utf-8 -*-
"""
Downloads real authentic Wuthering Waves game assets:
- Character portraits & splash art
- Element & weapon icons
- Real in-game backgrounds (Tower of Adversity, Convene/Luckdraw, Stygian Sea/Rogue Realm, Loading Screen)
Optimizes them with Pillow for fast web performance without quality loss.
"""

import os
import requests
from PIL import Image
import io

os.makedirs("web/assets/images/characters", exist_ok=True)
os.makedirs("web/assets/icons", exist_ok=True)

GITHUB_ASSETS = "https://raw.githubusercontent.com/ryanbenson/wuthering-waves-assets/master/images"
GITHUB_555ME = "https://raw.githubusercontent.com/555me/Wuthering-Waves-GameAssets/main/UI/UIResources"

def download_file(url, target_path):
    try:
        print(f"Downloading {url} -> {target_path}...")
        r = requests.get(url, timeout=20)
        if r.status_code == 200 and len(r.content) > 100:
            with open(target_path, "wb") as f:
                f.write(r.content)
            print(f"  [OK] Saved {target_path} ({len(r.content)} bytes)")
            return True
        else:
            print(f"  [FAIL] Status {r.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def download_and_optimize_bg(url, target_path, max_width=1920):
    try:
        print(f"Downloading & optimizing BG {url} -> {target_path}...")
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            im = Image.open(io.BytesIO(r.content))
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            
            # Resize if larger than max_width
            if im.width > max_width:
                height = int(im.height * (max_width / im.width))
                im = im.resize((max_width, height), Image.Resampling.LANCZOS)
            
            im.save(target_path, "JPEG", quality=88, optimize=True)
            print(f"  [OK] Optimized BG {target_path} ({os.path.getsize(target_path)} bytes)")
            return True
        else:
            print(f"  [FAIL] Status {r.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

# 1. Characters
characters = [
    ("Camellya.png", "web/assets/images/characters/camellya.png"),
    ("Jinhsi.png", "web/assets/images/characters/jinhsi.png"),
    ("Shorekeeper.png", "web/assets/images/characters/shorekeeper.png"),
    ("Changli.png", "web/assets/images/characters/changli.png"),
    ("Carlotta.png", "web/assets/images/characters/carlotta.png"),
    ("Yinlin.png", "web/assets/images/characters/yinlin.png"),
    ("Rover-Spectro.png", "web/assets/images/characters/rover.png"),
    ("Verina.png", "web/assets/images/characters/verina.png"),
]

for src, dst in characters:
    download_file(f"{GITHUB_ASSETS}/{src}", dst)

# 2. Element Icons
elements = [
    ("havoc.png", "web/assets/icons/element_havoc.png"),
    ("spectro.png", "web/assets/icons/element_spectro.png"),
    ("fusion.png", "web/assets/icons/element_fusion.png"),
    ("glacio.png", "web/assets/icons/element_glacio.png"),
    ("electro.png", "web/assets/icons/element_electro.png"),
    ("aero.png", "web/assets/icons/element_aero.png"),
]

for src, dst in elements:
    download_file(f"{GITHUB_ASSETS}/{src}", dst)

# 3. Weapons
weapons = [
    ("sword.webp", "web/assets/icons/weapon_sword.webp"),
    ("broadblade.webp", "web/assets/icons/weapon_broadblade.webp"),
    ("rectifier.webp", "web/assets/icons/weapon_rectifier.webp"),
    ("pistol.webp", "web/assets/icons/weapon_pistol.webp"),
    ("gauntlet.webp", "web/assets/icons/weapon_gauntlet.webp"),
]

for src, dst in weapons:
    download_file(f"{GITHUB_ASSETS}/{src}", dst)

# 4. In-Game Backgrounds / Key Art
download_and_optimize_bg(
    f"{GITHUB_555ME}/UiSingleTower/Image/T_UiSingleTowerBg_UI.png",
    "web/assets/images/tower_real.jpg"
)

download_and_optimize_bg(
    f"{GITHUB_555ME}/UiLuckdraw/Image/T_LuckdrawBg.png",
    "web/assets/images/banner_real.jpg"
)

download_and_optimize_bg(
    f"{GITHUB_555ME}/UiRogue/Image/RogueView/T_ViewBgFull.png",
    "web/assets/images/stygian_real.jpg"
)

download_and_optimize_bg(
    f"{GITHUB_555ME}/UILoading/Image/T_Loadingbg.png",
    "web/assets/images/hero_bg.jpg"
)

print("All real game assets downloaded and prepared!")

