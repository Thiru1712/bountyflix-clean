  # callbacks.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import (
    get_titles_by_letter,
    get_content_by_slug
)

# ======================================================
# ALPHABET MENU
# ======================================================

def alphabet_menu():
    letters = [chr(i) for i in range(ord("A"), ord("Z") + 1)]
    keyboard = []

    row = []
    for l in letters:
        row.append(InlineKeyboardButton(l, callback_data=f"letter:{l}"))
        if len(row) == 6:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

# ======================================================
# TITLES MENU (A → Anime list)
# ======================================================

def titles_menu(letter):
    titles = get_titles_by_letter(letter)
    keyboard = []

    for t in titles:
        keyboard.append([
            InlineKeyboardButton(
                t["title"],
                callback_data=f"anime:{t['slug']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅ Back", callback_data="back:alphabet")
    ])

    return InlineKeyboardMarkup(keyboard)

# ======================================================
# SEASONS MENU
# ======================================================

def seasons_menu(slug):
    content = get_content_by_slug(slug)
    keyboard = []

    for s in content.get("seasons", []):
        keyboard.append([
            InlineKeyboardButton(
                f"Season {s['season']}",
                callback_data=f"season:{slug}:{s['season']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data=f"back:titles:{content['title'][0].upper()}"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

# ======================================================
# DOWNLOAD MENU
# ======================================================

def download_menu(slug, season):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬇ Download",
                callback_data=f"redirect:{slug}:{season}"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅ Back",
                callback_data=f"anime:{slug}"
            )
        ]
    ])