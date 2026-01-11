 # admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import is_admin, CHANNEL_ID
from database import (
    add_content,
    delete_by_title,
    update_title,
    add_or_update_season,
    delete_season
)
from callbacks import alphabet_menu

PENDING = {}  # user_id → action tuple

# ------------------ ADMIN PANEL ------------------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "🛠 Admin Commands\n\n"
        "/addanime\n"
        "/editanime\n"
        "/addseason\n"
        "/deleteseason\n"
        "/deleteanime\n"
        "/stats\n"
        "/help"
    )

# ------------------ ADD ANIME ------------------

async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text
    if "|" not in text:
        await update.message.reply_text(
            "❌ Format:\n/addanime Title | S1=link, S2=link"
        )
        return

    try:
        title_part, seasons_part = text.split("|", 1)
        title = title_part.replace("/addanime", "").strip()

        seasons = []
        for s in seasons_part.split(","):
            k, v = s.split("=")
            seasons.append({
                "season": int("".join(filter(str.isdigit, k))),
                "redirect": v.strip()
            })

        PENDING[update.effective_user.id] = ("addanime", title, seasons)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm:addanime")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
        ])

        await update.message.reply_text(
            f"⚠️ Confirm add:\n<b>{title}</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )

    except Exception:
        await update.message.reply_text("❌ Invalid format")

# ------------------ EDIT ANIME ------------------

async def editanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    body = update.message.text.replace("/editanime", "").strip()
    if "|" not in body:
        await update.message.reply_text(
            "❌ Format:\n/editanime Old Title | New Title"
        )
        return

    old, new = body.split("|", 1)
    PENDING[update.effective_user.id] = ("editanime", old.strip(), new.strip())

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm:editanime")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
    ])

    await update.message.reply_text("⚠️ Confirm edit?", reply_markup=kb)

# ------------------ ADD SEASON ------------------

async def addseason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Format:\n/addseason Title Season link"
        )
        return

    try:
        season = int(context.args[-2])
        link = context.args[-1]
        title = " ".join(context.args[:-2])

        PENDING[update.effective_user.id] = (
            "addseason", title, season, link
        )

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm:addseason")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
        ])

        await update.message.reply_text(
            f"⚠️ Confirm add/update:\n<b>{title}</b>\nSeason {season}",
            reply_markup=kb,
            parse_mode="HTML"
        )

    except ValueError:
        await update.message.reply_text("❌ Season must be a number")

# ------------------ DELETE SEASON ------------------

async def deleteseason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format:\n/deleteseason Title Season"
        )
        return

    try:
        season = int(context.args[-1])
        title = " ".join(context.args[:-1])

        PENDING[update.effective_user.id] = (
            "deleteseason", title, season
        )

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Confirm Delete", callback_data="confirm:deleteseason")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
        ])

        await update.message.reply_text(
            f"⚠️ Confirm delete:\n<b>{title}</b>\nSeason {season}",
            reply_markup=kb,
            parse_mode="HTML"
        )

    except ValueError:
        await update.message.reply_text("❌ Season must be a number")

# ------------------ DELETE ANIME ------------------

async def deleteanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    title = " ".join(context.args)
    if not title:
        return

    PENDING[update.effective_user.id] = ("deleteanime", title)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Confirm Delete", callback_data="confirm:deleteanime")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
    ])

    await update.message.reply_text(
        f"⚠️ Confirm delete:\n<b>{title}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ------------------ CONFIRM HANDLER ------------------

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    await q.answer()

    if uid not in PENDING:
        return

    action = q.data.split(":")[1]
    data = PENDING.pop(uid)

    if action == "cancel":
        await q.edit_message_text("❌ Cancelled")
        return

    if data[0] == "addanime":
        ok = add_content(data[1], data[2])
        await q.edit_message_text("✅ Added" if ok else "⚠️ Already exists")

        msg = await context.bot.send_message(
            CHANNEL_ID,
            "🎬 <b>Browse Movies</b>",
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )
        await context.bot.pin_chat_message(CHANNEL_ID, msg.message_id, True)

    elif data[0] == "editanime":
        ok = update_title(data[1], data[2])
        await q.edit_message_text("✅ Updated" if ok else "❌ Failed")

    elif data[0] == "addseason":
        _, title, season, link = data
        ok = add_or_update_season(title, season, link)
        await q.edit_message_text("✅ Season saved" if ok else "❌ Failed")

    elif data[0] == "deleteseason":
        _, title, season = data
        ok = delete_season(title, season)
        await q.edit_message_text("🗑 Season deleted" if ok else "❌ Failed")

    elif data[0] == "deleteanime":
        ok = delete_by_title(data[1])
        await q.edit_message_text("🗑 Anime deleted" if ok else "❌ Failed")