 # database.py

import os, sys
from datetime import datetime
from pymongo import MongoClient, ASCENDING
from bson import ObjectId

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅ MongoDB connected")
except Exception as e:
    print("❌ MongoDB failed:", e)
    sys.exit(1)

db = client["telegram_bot"]

approved_content_col = db["approved_content"]
pending_content_col = db["pending_content"]
stats_col = db["stats"]

approved_content_col.create_index([("slug", ASCENDING)], unique=True)

# ---------- HELPERS ----------

def normalize_slug(text: str) -> str:
    return text.strip().lower().replace(" ", "_")

# ---------- CONTENT ----------

def get_letters_available():
    return sorted(approved_content_col.distinct("letter"))

def get_titles_by_letter(letter):
    return list(
        approved_content_col.find(
            {"letter": letter.upper()},
            {"_id": 1, "title": 1, "slug": 1}
        ).sort("title", 1)
    )

def get_content_by_slug(slug):
    return approved_content_col.find_one({"slug": slug})

def submit_pending_content(title, seasons, user_id):
    doc = {
        "title": title,
        "slug": normalize_slug(title),
        "letter": title[0].upper(),
        "seasons": seasons,
        "created_by": user_id,
        "created_at": datetime.utcnow()
    }
    try:
        approved_content_col.insert_one(doc)
    except Exception:
        return None
    return doc

# ---------- ADMIN MANAGEMENT ----------

def get_all_movies():
    return list(
        approved_content_col.find({}, {"_id": 1, "title": 1}).sort("title", 1)
    )

def delete_movie(movie_id):
    return approved_content_col.delete_one({"_id": ObjectId(movie_id)})

# ---------- ANALYTICS ----------

def inc_stat(key):
    stats_col.update_one(
        {"_id": "global"},
        {"$inc": {key: 1}},
        upsert=True
    )

def get_stats():
    return stats_col.find_one({"_id": "global"}) or {}
