  # callbacks.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_titles_by_letter, get_content_by_slug

def alphabet_menu():
    letters = [chr(i) for i in range(65, 91)]
    rows, row = [], []

    for l in letters:
        row.append(InlineKeyboardButton(l, callback_data=f"letter:{l}"))
        if len(row) == 6:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    return InlineKeyboardMarkup(rows)

def titles_menu(letter):
    titles = get_titles_by_letter(letter)
    kb = [[InlineKeyboardButton(t["title"], callback_data=f"anime:{t['slug']}")]
          for t in titles]

    kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:alphabet")])
    return InlineKeyboardMarkup(kb)

def seasons_menu(slug):
    content = get_content_by_slug(slug)
    kb = []

    for s in content.get("seasons", []):
        kb.append([
            InlineKeyboardButton(
                f"Season {s['season']}",
                callback_data=f"season:{slug}:{s['season']}"
            )
        ])

    kb.append([
        InlineKeyboardButton(
            "⬅ Back",
            callback_data=f"back:titles:{content['title'][0].upper()}"
        )
    ])

    return InlineKeyboardMarkup(kb)

def download_menu(slug, season):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇ Download", callback_data=f"redirect:{slug}:{season}")],
        [InlineKeyboardButton("⬅ Back", callback_data=f"anime:{slug}")]
    ])