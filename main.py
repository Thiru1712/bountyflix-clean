 # main.py

import os, time, threading
from flask import Flask, jsonify
from datetime import timedelta

from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler
)

from callbacks import *
from admin import *
from database import *
from config import CHANNEL_ID, is_admin

app = Flask(__name__)
START = time.time()

@app.route("/")
def home():
    return "BountyFlix alive"

@app.route("/health")
def health():
    return jsonify(uptime=int(time.time() - START))

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# ------------------ MAINTENANCE ------------------

async def maintenance_job(ctx):
    try:
        client.admin.command("ping")
        print("🟢 Mongo OK")
    except Exception as e:
        print("🔴 Mongo fail", e)

async def autopin_job(ctx):
    try:
        msg = await ctx.bot.send_message(
            CHANNEL_ID,
            "🎬 <b>Browse Movies</b>",
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )
        await ctx.bot.pin_chat_message(CHANNEL_ID, msg.message_id, True)
    except:
        pass

# ------------------ CALLBACK ROUTER ------------------

async def callback_router(update, context):
    data = update.callback_query.data

    if data.startswith("confirm:"):
        await confirm_handler(update, context)
        return

    if data.startswith("back:"):
        if data == "back:alphabet":
            await update.callback_query.edit_message_text(
                "🎬 Available Movies",
                reply_markup=alphabet_menu()
            )
        else:
            _, _, l = data.split(":")
            await update.callback_query.edit_message_text(
                l,
                reply_markup=titles_menu(l)
            )
        return

    if data.startswith("letter:"):
        inc_stat("alphabet_clicks")
        l = data.split(":")[1]
        await update.callback_query.edit_message_text(
            l, reply_markup=titles_menu(l)
        )

    elif data.startswith("anime:"):
        inc_stat("anime_clicks")
        slug = data.split(":")[1]
        c = get_content_by_slug(slug)
        await update.callback_query.edit_message_text(
            c["title"], reply_markup=seasons_menu(slug)
        )

    elif data.startswith("season:"):
        inc_stat("season_clicks")
        _, slug, s = data.split(":")
        await update.callback_query.edit_message_text(
            "⬇ Download", reply_markup=download_menu(slug, int(s))
        )

    elif data.startswith("redirect:"):
        inc_stat("download_clicks")
        _, slug, s = data.split(":")
        c = get_content_by_slug(slug)
        for x in c["seasons"]:
            if x["season"] == int(s):
                await context.bot.send_message(
                    update.effective_user.id,
                    x["redirect"]
                )

# ------------------ BOT START ------------------

def start_bot():
    appb = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    appb.add_handler(CommandHandler("start", start))
    appb.add_handler(CommandHandler("help", admin_panel))
    appb.add_handler(CommandHandler("admin", admin_panel))
    appb.add_handler(CommandHandler("addanime", addanime_submit))
    appb.add_handler(CommandHandler("editanime", editanime))
    appb.add_handler(CommandHandler("deleteanime", deleteanime))
    appb.add_handler(CallbackQueryHandler(callback_router))

    appb.job_queue.run_repeating(maintenance_job, timedelta(minutes=5))
    appb.job_queue.run_repeating(autopin_job, timedelta(hours=6))

    appb.run_polling()

async def start(update, context):
    await update.message.reply_text(
        "🎬 Available Movies",
        reply_markup=alphabet_menu()
    )

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    start_bot()