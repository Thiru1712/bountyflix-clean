 # main.py

import os
import time
import asyncio
import threading
from flask import Flask, jsonify

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import is_admin
from database import (
    get_content_by_slug,
    inc_stat,
    get_stats,
)
from callbacks import (
    alphabet_menu,
    titles_menu,
    seasons_menu,
    download_menu,
)
from admin import (
    admin_panel,
    addanime_submit,
    admin_callbacks,
)

# ======================================================
# FLASK (HEALTH CHECK)
# ======================================================

app = Flask(__name__)
START_TIME = time.time()

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "uptime": int(time.time() - START_TIME)
    })

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# ======================================================
# SAFE REPLY HELPER (CRITICAL FIX)
# ======================================================

async def safe_reply(update: Update, text: str, **kwargs):
    """
    Replies safely whether command came from:
    - normal message
    - menu button
    - UI command
    """
    if update.message:
        await update.message.reply_text(text, **kwargs)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, **kwargs)

# ======================================================
# COMMAND HANDLERS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(
        update,
        "🎬 <b>Available Movies</b>",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_reply(update, "❌ Admins only")
        return

    await safe_reply(
        update,
        "🛠 <b>Admin Commands</b>\n\n"
        "/start – Browse movies\n"
        "/admin – Admin panel\n"
        "/addanime – Add movie/anime\n"
        "/broadcast – Broadcast message\n"
        "/stats – Bot statistics\n"
        "/help – This help",
        parse_mode="HTML"
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await safe_reply(update, "❌ Admins only")
        return

    stats = get_stats()
    uptime = int(time.time() - START_TIME)

    await safe_reply(
        update,
        f"📊 <b>BountyFlix Stats</b>\n\n"
        f"Alphabet clicks: {stats.get('alphabet_clicks', 0)}\n"
        f"Anime clicks: {stats.get('anime_clicks', 0)}\n"
        f"Season clicks: {stats.get('season_clicks', 0)}\n"
        f"Downloads: {stats.get('download_clicks', 0)}\n\n"
        f"⏱ Uptime: {uptime} seconds",
        parse_mode="HTML"
    )

# ======================================================
# CALLBACK HANDLER
# ======================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ---------- ADMIN CALLBACKS ----------
    if data.startswith("admin:") or data.startswith("delete:"):
        await admin_callbacks(update, context)
        return

    # ---------- USER FLOW ----------
    if data.startswith("letter:"):
        inc_stat("alphabet_clicks")
        letter = data.split(":")[1]
        await query.edit_message_text(
            f"🔤 <b>{letter}</b>",
            reply_markup=titles_menu(letter),
            parse_mode="HTML"
        )

    elif data.startswith("anime:"):
        inc_stat("anime_clicks")
        slug = data.split(":")[1]
        content = get_content_by_slug(slug)
        if not content:
            return
        await query.edit_message_text(
            f"🎬 <b>{content['title']}</b>",
            reply_markup=seasons_menu(slug),
            parse_mode="HTML"
        )

    elif data.startswith("season:"):
        inc_stat("season_clicks")
        _, slug, season = data.split(":")
        await query.edit_message_text(
            "⬇ <b>Select download</b>",
            reply_markup=download_menu(slug, int(season)),
            parse_mode="HTML"
        )

    elif data.startswith("redirect:"):
        inc_stat("download_clicks")
        _, slug, season = data.split(":")
        content = get_content_by_slug(slug)
        if not content:
            return
        for s in content.get("seasons", []):
            if s["season"] == int(season):
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=s["redirect"]
                )

# ======================================================
# BOT RUNNER
# ======================================================

async def bot_main():
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("addanime", addanime_submit))
    application.add_handler(CallbackQueryHandler(callback_handler))

    await application.run_polling()

def start_bot():
    while True:
        try:
            asyncio.run(bot_main())
        except Exception as e:
            print("CRASH:", e)
            time.sleep(5)

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()
