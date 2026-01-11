 # database.py

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(
    os.getenv("MONGO_URI"),
    serverSelectionTimeoutMS=5000
)

db = client["bountyflix"]
approved = db["approved_content"]
stats = db["stats"]

try:
    client.admin.command("ping")
    print("MongoDB connected")
except Exception as e:
    print("MongoDB error:", e)

# ------------------ helpers ------------------

def slugify(title):
    return title.lower().replace(" ", "")

def exists(title):
    return approved.find_one({"slug": slugify(title)}) is not None

def add_content(title, seasons):
    slug = slugify(title)
    if approved.find_one({"slug": slug}):
        return False

    approved.insert_one({
        "title": title,
        "slug": slug,
        "seasons": seasons
    })
    return True

def delete_by_title(title):
    res = approved.delete_one({"slug": slugify(title)})
    return res.deleted_count > 0

def update_title(old, new):
    if exists(new):
        return False

    res = approved.update_one(
        {"slug": slugify(old)},
        {"$set": {"title": new, "slug": slugify(new)}}
    )
    return res.modified_count > 0

def update_season_link(title, season, link):
    res = approved.update_one(
        {"slug": slugify(title), "seasons.season": season},
        {"$set": {"seasons.$.redirect": link}}
    )
    return res.modified_count > 0

def get_titles_by_letter(letter):
    return list(
        approved.find(
            {"title": {"$regex": f"^{letter}", "$options": "i"}},
            {"title": 1, "slug": 1}
        ).sort("title", 1)
    )

def get_content_by_slug(slug):
    return approved.find_one({"slug": slug})

# ------------------ stats ------------------

def inc_stat(key):
    stats.update_one({"_id": "global"}, {"$inc": {key: 1}}, upsert=True)

def get_stats():
    return stats.find_one({"_id": "global"}) or {}