import os

# ─── OpenAI (if you plan to support it later) ───
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ─── Cohere API Key ─────────────────────────────
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "RlQjCIFvOkgZr3JT2mUiEe33MMB8ZyTY6TVaxrzO")

# ─── Apply to environment (optional; for local testing) ───
os.environ["COHERE_API_KEY"] = COHERE_API_KEY
# os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
