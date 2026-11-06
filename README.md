# 🌊 Wuthering Waves Arabic — منصة موجات ووزيرينغ بالعربي

منصة عربية احترافية لمتابعة أخبار ومحتويات لعبة **Wuthering Waves**، تعمل كموقع ويب مستقل وكـ **Telegram Mini App** في نفس الوقت.

---

## الميزات

- ⏱️ **عدادات تنازلية مباشرة** — آسيا / أوروبا / أمريكا بدقة الثانية
- 🃏 **صفحة البنرات** — مع صورة البنر وأسماء الشخصيات والعدادات لكل سيرفر
- 🎉 **صفحة الأحداث** — تُحدَّث تلقائياً وتختفي فور انتهائها
- ⚓ **السفينة (Stygian Sea)** — مع صورة اللعبة الحقيقية وعدادات التجدد
- 🗼 **التاور (Tower of Adversity)** — مع صورة اللعبة الحقيقية وعدادات التجدد
- 💬 **Telegram Mini App** — يعمل مباشرة داخل Telegram مع دعم Back Button والتوسع التلقائي
- 📴 **وضع أوفلاين** — يعرض آخر بيانات محفوظة عند انقطاع الاتصال
- 🔄 **إعادة اتصال تلقائية** — يعيد التحديث فور العودة للاتصال

---

## هيكل المشروع

```
wuthering-waves-arabic/
├── wuwa.py              # 🤖 بوت Telegram الرئيسي (Aiogram 2 / Python)
├── api.py               # 🌐 FastAPI REST API + خدمة الملفات الثابتة
├── database.py          # 🗄️ SQLite database layer
├── time_utils.py        # ⏱️ حساب الوقت للسيرفرات الثلاثة
├── start.py             # 🚀 مشغل موحد (API + Bot)
├── test_system.py       # ✅ اختبارات النظام الكاملة
├── netlify.toml         # ☁️ إعدادات Netlify للنشر
├── termux_start.sh      # 📱 سكريبت تشغيل Termux
├── .env.example         # ⚙️ مثال ملف الإعدادات
├── genshin_bot.db       # 🗃️ قاعدة البيانات SQLite
│
└── web/                 # 🎨 الواجهة الأمامية
    ├── index.html       # صفحة HTML الرئيسية (SPA)
    ├── css/style.css    # نظام التصميم الكامل
    ├── js/
    │   ├── app.js       # المنطق الرئيسي + SPA Router
    │   ├── api.js       # API Client مع Cache ومسح الأوفلاين
    │   ├── countdown.js # محرك العدادات التنازلية
    │   ├── telegram.js  # محول Telegram Mini App SDK
    │   └── i18n.js      # نظام الترجمة عربي/إنجليزي
    └── assets/
        ├── images/
        │   ├── logo.jpeg               # الشعار الرسمي
        │   ├── banner_real.jpg         # خلفية بنرات (من اللعبة)
        │   ├── stygian_real.jpg        # خلفية السفينة (من اللعبة)
        │   ├── tower_real.jpg          # خلفية التاور (من اللعبة)
        │   ├── hero_bg.jpg             # خلفية Hero Section
        │   └── characters/            # صور الشخصيات الحقيقية
        │       ├── camellya.png
        │       ├── jinhsi.png
        │       ├── shorekeeper.png
        │       ├── changli.png
        │       ├── carlotta.png
        │       ├── yinlin.png
        │       ├── rover.png
        │       └── verina.png
        └── icons/
            ├── element_havoc.png       # أيقونات العناصر
            ├── element_spectro.png
            ├── element_fusion.png
            ├── element_glacio.png
            ├── element_electro.png
            ├── element_aero.png
            ├── weapon_sword.webp       # أيقونات الأسلحة
            ├── weapon_broadblade.webp
            ├── weapon_rectifier.webp
            ├── weapon_pistol.webp
            └── weapon_gauntlet.webp
```

---

## التشغيل المحلي

### المتطلبات
- Python 3.10+
- المكتبات: `fastapi uvicorn aiogram requests`

```bash
pip install fastapi uvicorn aiogram requests
```

### إنشاء ملف `.env`
```bash
cp .env.example .env
# عدّل القيم بمحرر النصوص
```

```env
BOT_TOKEN=your_telegram_bot_token_here
WEB_APP_URL=https://your-netlify-site.netlify.app
```

### تشغيل API + الموقع
```bash
python start.py --mode api
# افتح: http://localhost:8000
```

### تشغيل البوت فقط
```bash
python start.py --mode bot
```

### تشغيل الكل (API + Bot)
```bash
python start.py
```

### تشغيل الاختبارات
```bash
python test_system.py
# يجب أن تنجح جميع الاختبارات السبعة
```

---

## التشغيل على Termux (Android)

```bash
bash termux_start.sh
```

أو يدوياً:
```bash
cd ~/wuwa
source venv/bin/activate
python start.py
```

---

## النشر على Netlify

الواجهة الأمامية تعمل كموقع ثابت على Netlify:

1. اربط المستودع بـ Netlify
2. اضبط **Publish directory**: `web`
3. لا حاجة لأمر Build
4. أضف متغير البيئة: `API_BASE_URL` ← رابط API الخاص بك على Termux أو ngrok

```
// في index.html أو عبر Netlify environment variable:
window.API_BASE_URL = "https://your-termux-tunnel.ngrok.io/api";
```

---

## قاعدة البيانات

### مخطط الجدول الرئيسي (`content`)

| العمود | النوع | الوصف |
|--------|-------|-------|
| `id` | INTEGER | معرف فريد |
| `section` | TEXT | `banner` / `stygian` / `spiral_abyss` / `events` |
| `title` | TEXT | عنوان المحتوى بالعربية |
| `name` | TEXT | أسماء الشخصيات أو العنوان الإنجليزي |
| `end_time_asia` | TEXT | وقت انتهاء سيرفر آسيا (UTC) |
| `end_time_europe` | TEXT | وقت انتهاء سيرفر أوروبا (UTC) |
| `end_time_america` | TEXT | وقت انتهاء سيرفر أمريكا (UTC) |
| `description` | TEXT | وصف المحتوى |
| `image_file_id` | TEXT | معرف الصورة على Telegram |

### حساب التوقيت (يطابق وظيفة البوت تماماً)
- **آسيا**: UTC+8 ← تُخزن القيمة المُدخلة كـ UTC (بطرح 8 ساعات)
- **أوروبا**: UTC+1 ← بطرح ساعة واحدة
- **أمريكا**: UTC-5 ← بإضافة 5 ساعات

---

## أوامر البوت

| الأمر | الوصف |
|-------|-------|
| `/start` | رسالة ترحيب |
| `/banner` | معلومات البنر الحالي |
| `/stygian` | معلومات السفينة |
| `/tower` | معلومات التاور |
| `/events` | الأحداث النشطة |
| `/setbanner` | تحديث البنر (للمشرف) |
| `/setstygian` | تحديث السفينة (للمشرف) |
| `/settower` | تحديث التاور (للمشرف) |
| `/addevent` | إضافة حدث (للمشرف) |
| `/delevents` | حذف الأحداث المنتهية (للمشرف) |

---

## نقاط نهاية API

| المسار | الوصف |
|--------|-------|
| `GET /api/health` | حالة الخادم وقاعدة البيانات |
| `GET /api/content` | كل المحتوى (banner + stygian + tower + events) |
| `GET /api/content/banner` | بيانات البنر الحالي |
| `GET /api/content/stygian` | بيانات حدث السفينة |
| `GET /api/content/spiral_abyss` | بيانات التاور |
| `GET /api/content/events` | الأحداث النشطة |
| `GET /api/image/banner` | صورة البنر (من Telegram أو fallback) |
| `GET /api/image/stygian` | صورة السفينة |
| `GET /api/image/spiral_abyss` | صورة التاور |
| `POST /api/auth/verify-telegram` | التحقق من initData الـ Mini App |

---

## ملاحظات التقنية

- **Framework**: FastAPI + Uvicorn (Python)
- **Database**: SQLite (`genshin_bot.db`)
- **Bot Library**: Aiogram 2.x
- **Frontend**: Vanilla JS (ES Modules) — بدون frameworks خارجية
- **Fonts**: IBM Plex Sans Arabic + Tajawal (Google Fonts)
- **Icons**: Lucide SVG (inline)
- **Game Assets**: صور رسمية من Kuro Games — غير تجارية

---

> صور الشخصيات والخلفيات ملكية **Kuro Games** — هذا مشروع مجتمعي غير رسمي وغير تجاري.
