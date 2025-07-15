# team_manager.py

from firebase_auth import db

def get_team_id_from_email(email):
    """Generate a team ID based on user's email domain."""
    return email.split("@")[-1].replace(".", "_")

def save_to_team_shared_prompts(email, prompt_data):
    """Save a prompt (single or chained) to the team's shared space."""
    team_id = get_team_id_from_email(email)
    db.child("teams").child(team_id).child("shared_prompts").push(prompt_data)

def load_team_shared_prompts(email):
    """Load shared prompts for the team based on email domain."""
    team_id = get_team_id_from_email(email)
    try:
        result = db.child("teams").child(team_id).child("shared_prompts").get()
        if result.each():
            return [item.val() for item in result.each()]
        else:
            return []
    except Exception as e:
        return f"Error loading team prompts: {e}"
