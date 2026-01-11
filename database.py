 # database.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ======================================================
# MONGO CONNECTION (SAFE)
# ======================================================

client = MongoClient(
    os.getenv("MONGO_URI"),
    serverSelectionTimeoutMS=5000
)

db = client["bountyflix"]
approved_content_col = db["approved_content"]
stats_col = db["stats"]

try:
    client.admin.command("ping")
    print("MongoDB connected")
except Exception as e:
    print("MongoDB failed:", e)

# ======================================================
# CONTENT HELPERS
# ======================================================

def slugify(title: str) -> str:
    return title.lower().replace(" ", "")

def add_content(title, seasons):
    slug = slugify(title)
    if approved_content_col.find_one({"slug": slug}):
        return False

    approved_content_col.insert_one({
        "title": title,
        "slug": slug,
        "seasons": seasons
    })
    return True

def get_titles_by_letter(letter):
    return list(
        approved_content_col.find(
            {"title": {"$regex": f"^{letter}", "$options": "i"}},
            {"title": 1, "slug": 1}
        ).sort("title", 1)
    )

def get_content_by_slug(slug):
    return approved_content_col.find_one({"slug": slug})

def delete_by_title(title):
    res = approved_content_col.delete_one(
        {"title": {"$regex": f"^{title}$", "$options": "i"}}
    )
    return res.deleted_count > 0

def update_title(old, new):
    old_slug = slugify(old)
    new_slug = slugify(new)

    if approved_content_col.find_one({"slug": new_slug}):
        return False

    res = approved_content_col.update_one(
        {"slug": old_slug},
        {"$set": {"title": new, "slug": new_slug}}
    )
    return res.modified_count > 0

def update_season_link(title, season, link):
    slug = slugify(title)
    res = approved_content_col.update_one(
        {"slug": slug, "seasons.season": season},
        {"$set": {"seasons.$.redirect": link}}
    )
    return res.modified_count > 0

def get_all_titles():
    return list(
        approved_content_col.find({}, {"title": 1}).sort("title", 1)
    )

# ======================================================
# STATS
# ======================================================

def inc_stat(key):
    stats_col.update_one(
        {"_id": "global"},
        {"$inc": {key: 1}},
        upsert=True
    )

def get_stats():
    doc = stats_col.find_one({"_id": "global"})
    return doc or {}