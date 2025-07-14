import pyrebase
from firebase_config import firebase_config
from datetime import datetime

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
    user_id = uid if uid else email.replace(".", "_")


    # Base data payload
    data = {
        "prompt":       prompt,
        "response":     response,
        "timestamp":    datetime.now().isoformat(),
        # pull through any core meta fields
        "role":         meta.get("role"),
        "audience":     meta.get("audience"),
        "tone":         meta.get("tone"),
        "intent":       meta.get("intent"),
        "temperature":  meta.get("temperature"),
        "max_tokens":   meta.get("max_tokens"),
    }

    # Include rating/feedback if provided
    if "rating" in meta:
        data["rating"]   = meta.get("rating")
    if "feedback" in meta:
        data["feedback"] = meta.get("feedback")

    # Include chaining steps if provided
    if chain_steps:
        # chain_steps should be a list of dicts: [{"step":..., "prompt":..., "response":...}, ...]
        data["chain"] = chain_steps

    # Push to Realtime Database under logs/<user_id>
    db.child("logs").child(user_id).push(data)
