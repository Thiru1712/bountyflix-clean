 # main.py

import os
import time
import threading
from flask import Flask, jsonify

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import CHANNEL_ID, is_admin
from callbacks import (
    alphabet_menu,
    titles_menu,
    seasons_menu,
    download_menu,
)
from admin import (
    admin_panel,
    addanime_submit,
    editanime,
    addseason,
    deleteseason,
    deleteanime,
    confirm_handler,
)
from database import (
    get_content_by_slug,
    inc_stat,
    get_stats,
)

# ======================================================
# FLASK (HEALTH CHECK FOR RENDER)
# ======================================================

app = Flask(__name__)
START_TIME = time.time()

@app.route("/")
def home():
    return "BountyFlix alive 🟢"

@app.route("/health")
def health():
    return jsonify(
        status="ok",
        uptime=int(time.time() - START_TIME)
    )

def run_web():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ======================================================
# COMMANDS
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 <b>Available Movies</b>",
        reply_markup=alphabet_menu(),
        parse_mode="HTML"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admins only")
        return

    await update.message.reply_text(
        """🛠 BountyFlix — Admin Help

/start
Browse movies & anime

/help
Show this help message

/admin
Show admin panel

/addanime Title | S1=link, S2=link
Add a new anime or movie

/editanime Old Title | New Title
Rename an anime/movie

/addseason Title Season link
Add or update a season

/deleteseason Title Season
Delete a season

/deleteanime Title
Delete an anime/movie

/stats
Show bot statistics & uptime
""",
        parse_mode="HTML"
    )

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admins only")
        return

    stats = get_stats()
    uptime = int(time.time() - START_TIME)

    h = uptime // 3600
    m = (uptime % 3600) // 60
    s = uptime % 60

    await update.message.reply_text(
        f"📊 <b>BountyFlix Stats</b>\n\n"
        f"Alphabet clicks: {stats.get('alphabet_clicks', 0)}\n"
        f"Anime clicks: {stats.get('anime_clicks', 0)}\n"
        f"Season clicks: {stats.get('season_clicks', 0)}\n"
        f"Downloads: {stats.get('download_clicks', 0)}\n\n"
        f"⏱ Uptime: {h}h {m}m {s}s",
        parse_mode="HTML"
    )

# ======================================================
# CALLBACK ROUTER
# ======================================================

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    # ---------- CONFIRMATION ----------
    if data.startswith("confirm:"):
        await confirm_handler(update, context)
        return

    # ---------- BACK BUTTON ----------
    if data.startswith("back:"):
        parts = data.split(":")
        if parts[1] == "alphabet":
            await query.edit_message_text(
                "🎬 <b>Available Movies</b>",
                reply_markup=alphabet_menu(),
                parse_mode="HTML"
            )
        elif parts[1] == "titles":
            letter = parts[2]
            await query.edit_message_text(
                f"🔤 <b>{letter}</b>",
                reply_markup=titles_menu(letter),
                parse_mode="HTML"
            )
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
                return

# ======================================================
# BOT START
# ======================================================

def start_bot():
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(CommandHandler("admin", admin_panel))

    application.add_handler(CommandHandler("addanime", addanime_submit))
    application.add_handler(CommandHandler("editanime", editanime))
    application.add_handler(CommandHandler("addseason", addseason))
    application.add_handler(CommandHandler("deleteseason", deleteseason))
    application.add_handler(CommandHandler("deleteanime", deleteanime))

    application.add_handler(CallbackQueryHandler(callback_router))

    application.run_polling()

# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()