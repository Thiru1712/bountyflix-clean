 # admin.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import is_admin, CHANNEL_ID
from database import (
    add_content,
    delete_by_title,
    update_title,
    update_season_link,
    get_all_titles
)
from callbacks import alphabet_menu

# ======================================================
# ADMIN PANEL
# ======================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admins only")
        return

    keyboard = [
        [InlineKeyboardButton("➕ Add Anime", callback_data="admin:add")],
        [InlineKeyboardButton("✏ Edit Anime", callback_data="admin:edit")],
        [InlineKeyboardButton("🗑 Delete Anime", callback_data="admin:delete")]
    ]

    await update.message.reply_text(
        "🛠 <b>Admin Panel</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ======================================================
# ADD ANIME
# ======================================================

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

        if not title:
            raise ValueError

        seasons = []
        for s in seasons_part.split(","):
            key, link = s.split("=")
            season_no = int("".join(filter(str.isdigit, key)))
            seasons.append({
                "season": season_no,
                "redirect": link.strip()
            })

        added = add_content(title, seasons)

        if not added:
            await update.message.reply_text("⚠️ Anime already exists")
            return

        await update.message.reply_text("✅ Movie added successfully")

        # Auto-pin alphabet menu
        try:
            msg = await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text="🎬 <b>Browse Movies</b>",
                reply_markup=alphabet_menu(),
                parse_mode="HTML"
            )
            await context.bot.pin_chat_message(
                chat_id=CHANNEL_ID,
                message_id=msg.message_id,
                disable_notification=True
            )
        except:
            pass

    except Exception:
        await update.message.reply_text(
            "❌ Format error\n/addanime Title | S1=link, S2=link"
        )

# ======================================================
# DELETE ANIME
# ======================================================

async def deleteanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Usage:\n/deleteanime Title")
        return

    title = " ".join(context.args)
    deleted = delete_by_title(title)

    if deleted:
        await update.message.reply_text("🗑 Anime deleted")
    else:
        await update.message.reply_text("❌ Anime not found")

# ======================================================
# EDIT ANIME (TITLE / LINK)
# ======================================================

async def editanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /editanime old_title | new_title
    /editanime Title | S1=new_link
    """
    if not is_admin(update.effective_user.id):
        return

    if "|" not in update.message.text:
        await update.message.reply_text(
            "❌ Format:\n/editanime Old | New  OR  /editanime Title | S1=newlink"
        )
        return

    left, right = update.message.text.replace("/editanime", "").split("|", 1)
    left = left.strip()
    right = right.strip()

    if right.lower().startswith("s"):
        season = int("".join(filter(str.isdigit, right)))
        link = right.split("=", 1)[1]
        ok = update_season_link(left, season, link)
    else:
        ok = update_title(left, right)

    if ok:
        await update.message.reply_text("✅ Updated successfully")
    else:
        await update.message.reply_text("❌ Update failed")