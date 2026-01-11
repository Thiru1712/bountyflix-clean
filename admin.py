 # admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import is_admin, CHANNEL_ID
from database import (
    add_content,
    delete_by_title,
    update_title,
    update_season_link
)
from callbacks import alphabet_menu

PENDING = {}  # user_id → action data

# ------------------ ADMIN PANEL ------------------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    await update.message.reply_text(
        "🛠 Admin Commands\n\n"
        "/addanime Title | S1=link\n"
        "/editanime Old | New\n"
        "/editanime Title | S1=newlink\n"
        "/deleteanime Title"
    )

# ------------------ ADD ANIME (CONFIRM) ------------------

async def addanime_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text
    if "|" not in text:
        await update.message.reply_text("❌ Format:\n/addanime Title | S1=link")
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

        PENDING[update.effective_user.id] = ("add", title, seasons)

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data="confirm:add")],
            [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
        ])

        await update.message.reply_text(
            f"⚠️ Confirm add:\n<b>{title}</b>",
            reply_markup=kb,
            parse_mode="HTML"
        )

    except Exception:
        await update.message.reply_text("❌ Invalid format")

# ------------------ DELETE (CONFIRM) ------------------

async def deleteanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    title = " ".join(context.args)
    if not title:
        return

    PENDING[update.effective_user.id] = ("delete", title)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗑 Confirm Delete", callback_data="confirm:delete")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
    ])

    await update.message.reply_text(
        f"⚠️ Delete <b>{title}</b>?",
        reply_markup=kb,
        parse_mode="HTML"
    )

# ------------------ EDIT ------------------

async def editanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    body = update.message.text.replace("/editanime", "").strip()
    if "|" not in body:
        return

    left, right = body.split("|", 1)
    PENDING[update.effective_user.id] = ("edit", left.strip(), right.strip())

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏ Confirm Edit", callback_data="confirm:edit")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm:cancel")]
    ])

    await update.message.reply_text("⚠️ Confirm edit?", reply_markup=kb)

# ------------------ CONFIRM CALLBACK ------------------

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

    if data[0] == "add":
        ok = add_content(data[1], data[2])
        await q.edit_message_text("✅ Added" if ok else "⚠️ Already exists")

        # auto-pin menu
        msg = await context.bot.send_message(
            CHANNEL_ID,
            "🎬 <b>Browse Movies</b>",
            reply_markup=alphabet_menu(),
            parse_mode="HTML"
        )
        await context.bot.pin_chat_message(CHANNEL_ID, msg.message_id, True)

    elif data[0] == "delete":
        ok = delete_by_title(data[1])
        await q.edit_message_text("🗑 Deleted" if ok else "❌ Not found")

    elif data[0] == "edit":
        old, new = data[1], data[2]
        if new.lower().startswith("s"):
            season = int("".join(filter(str.isdigit, new)))
            link = new.split("=", 1)[1]
            ok = update_season_link(old, season, link)
        else:
            ok = update_title(old, new)

        await q.edit_message_text("✅ Updated" if ok else "❌ Failed")