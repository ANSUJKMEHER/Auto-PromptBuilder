import cohere
from config import COHERE_API_KEY

client = cohere.Client(COHERE_API_KEY)

def generate_prompt(prompt_text, temperature=0.7, max_tokens=300):
    try:
        response = client.chat(
            message=prompt_text,
            temperature=temperature,
            max_tokens=max_tokens,
            model="command-a-03-2025",
            stop_sequences=[]
        )
        return response.text
    except Exception as e:
        return f"❌ Error: {str(e)}"
