import os

from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Read API Key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Recommended fast model for story generation
MODEL_NAME = "llama-3.3-70b-versatile"


def ask_ai(question: str) -> str:
    """
    Sends a prompt to Groq and returns the AI response.

    Args:
        question (str): User question or prompt.

    Returns:
        str: AI generated response.
    """

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a creative AI Story Generator. "
                        "Generate engaging, well-structured stories."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=0.8,
            max_tokens=1024,
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"Error: {str(e)}"