import os
import asyncio
import aiohttp
import feedparser
from deep_translator import GoogleTranslator
from aiohttp import web

from sources import RSS_FEEDS
from utils import clean_text, make_hash, is_short

BOT_TOKEN     = os.environ["BOT_TOKEN"]
TARGET        = os.environ.get("TARGET_CHANNEL", "@WorldNewsLi")
POLL_INTERVAL = 30  # seconds

# Persistent in-memory dedup cache
_seen: set[str] = set()

# ─────────────────────────────────────────────────────────────────────────────
# Translation helper
# ─────────────────────────────────────────────────────────────────────────────
def translate(text: str, dest: str) -> str:
    try:
        return GoogleTranslator(source="auto", target=dest).translate(text) or text
    except Exception:
        return text

# ─────────────────────────────────────────────────────────────────────────────
# Telegram sender (no python-telegram-bot dependency – pure HTTP)
# ─────────────────────────────────────────────────────────────────────────────
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def send_message(session: aiohttp.ClientSession, text: str) -> bool:
    payload = {
        "chat_id": TARGET,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with session.post(f"{TG_API}/sendMessage", json=payload, timeout=15) as r:
            data = await r.json()
            if not data.get("ok"):
                print(f"[TG ERR] {data}")
            return data.get("ok", False)
    except Exception as e:
        print(f"[SEND ERR] {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# Priority / emoji detector
# ─────────────────────────────────────────────────────────────────────────────
BREAKING_KW = ["عاجل", "breaking", "urgent", "exclusive", "عاجلة", "حصري",
               "غارة", "انفجار", "اغتيال", "قصف", "هجوم", "سقوط", "اعتقال"]

def priority_emoji(text: str) -> str:
    t = text.lower()
    if any(k in t for k in BREAKING_KW):
        return "🚨 عاجل | BREAKING"
    return "📰 أخبار | News"

# ─────────────────────────────────────────────────────────────────────────────
# Main poller
# ─────────────────────────────────────────────────────────────────────────────
async def poll_all(session: aiohttp.ClientSession) -> None:
    for source_name, url in RSS_FEEDS.items():
        try:
            async with session.get(url, timeout=12) as resp:
                if resp.status != 200:
                    continue
                raw = await resp.text(errors="replace")
            feed = feedparser.parse(raw)
            for entry in feed.entries[:3]:  # top-3 per source
                title   = clean_text(getattr(entry, "title",   ""))
                summary = clean_text(getattr(entry, "summary", ""))
                full    = f"{title}. {summary}" if summary and summary != title else title

                if is_short(full):
                    continue

                h = make_hash(full)
                if h in _seen:
                    continue
                _seen.add(h)
                if len(_seen) > 5000:
                    _seen.clear()

                # Translate
                ar = translate(full, "ar")
                en = translate(full, "en")

                badge = priority_emoji(full)

                caption = (
                    f"{badge}\n\n"
                    f"🇮🇶 <b>{ar}</b>\n\n"
                    f"🇺🇸 {en}\n\n"
                    f"📡 المصدر: {source_name}\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"🌍 الأخبار العالمية | World News\n"
                    f"🔗 t.me/{TARGET.replace('@', '')}"
                )
                await send_message(session, caption)
                await asyncio.sleep(1.5)  # small gap between messages

        except asyncio.TimeoutError:
            print(f"[TIMEOUT] {source_name}")
        except Exception as e:
            print(f"[ERR] {source_name}: {e}")

async def polling_loop() -> None:
    print(f"[BOT] Starting RSS-only loop (interval={POLL_INTERVAL}s)")
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            print("[BOT] Polling all feeds...")
            await poll_all(session)
            print(f"[BOT] Sleeping {POLL_INTERVAL}s...")
            await asyncio.sleep(POLL_INTERVAL)

# ─────────────────────────────────────────────────────────────────────────────
# Health-check HTTP server (required by Railway)
# ─────────────────────────────────────────────────────────────────────────────
async def health(_):
    return web.Response(text="RSS News Bot – Running")

async def start_server() -> None:
    app = web.Application()
    app.router.add_get("/", health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    await web.TCPSite(runner, "0.0.0.0", port).start()
    print(f"[HTTP] Health-check listening on :{port}")

# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
async def main() -> None:
    await asyncio.gather(
        start_server(),
        polling_loop(),
    )

if __name__ == "__main__":
    asyncio.run(main())
Pressing key...Clicking...Stopping...

Stop Agent
