import json
import os
from firebase_auth import db  # 👈 import your db from firebase_auth

def load_templates(user_id=None):
    templates = {}

    # 1. 🔍 Load from Firebase if user_id is provided
    if user_id:
        try:
            firebase_templates = db.child("templates").child(user_id).get()
            if firebase_templates.each():
                for item in firebase_templates.each():
                    templates[item.key()] = item.val()
        except Exception as e:
            print("Error loading templates from Firebase:", e)

    # 2. 📁 Also load from local directory (optional)
    for file in os.listdir("templates"):
        if file.endswith(".json"):
            with open(os.path.join("templates", file), "r") as f:
                templates[file.split(".")[0]] = json.load(f)

    return templates
#template_manager.py
