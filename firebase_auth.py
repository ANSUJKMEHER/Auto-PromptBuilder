import pyrebase
from firebase_config import firebase_config
from datetime import datetime
import traceback

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

def signup(email, password):
    return auth.create_user_with_email_and_password(email, password)

def login(email, password):
    user = auth.sign_in_with_email_and_password(email, password)
    user_info = auth.get_account_info(user['idToken'])
    uid = user_info['users'][0]['localId']
    return {"email": email, "uid": uid}

def log_prompt_to_firebase(email, prompt, response, meta, chain_steps=None, uid=None):
    try:
        user_id = uid if uid else email.replace(".", "_")

        # Timestamp
        timestamp = meta.get("timestamp") or datetime.now().isoformat()

        # Construct data
        data = {
            "email":        email,
            "prompt":       prompt,
            "response":     response,
            "timestamp":    timestamp,
            "role":         meta.get("role"),
            "audience":     meta.get("audience"),
            "tone":         meta.get("tone"),
            "intent":       meta.get("intent"),
            "temperature":  meta.get("temperature"),
            "max_tokens":   meta.get("max_tokens"),
        }

        if meta.get("rating") is not None:
            data["rating"] = meta["rating"]
        if meta.get("feedback"):
            data["feedback"] = meta["feedback"]
        if chain_steps:
            data["chain"] = chain_steps

        # 🔐 Push and get the log key
        result = db.child("logs").child(user_id).push(data)
        return result["name"], timestamp  # 🔁 Return Firebase key and timestamp

    except Exception as e:
        print("[Firebase Log Error]", e)
        traceback.print_exc()
        return None, None  # ❌ Failed

def update_feedback_in_firebase(user_id, log_key, rating=None, feedback=None):
    try:
        updates = {}
        if rating is not None:
            updates["rating"] = rating
        if feedback:
            updates["feedback"] = feedback
        db.child("logs").child(user_id).child(log_key).update(updates)
    except Exception as e:
        print(f"[Firebase Feedback Update Error]: {e}")
        traceback.print_exc()
