import logging
from groq import Groq
from bot.config import Config

logger = logging.getLogger(__name__)

groq_client = Groq(api_key=Config.GROQ_API_KEY)

def get_system_prompt(focus_mode: str) -> str:
    if focus_mode == "academic":
        return (
            "You are a helpful and highly intelligent AI academic tutor. Your goal is to teach, not just give answers. "
            "Be conversational. Ask clarifying questions if needed. Use analogies. Break down complex topics into simple steps. "
            "Always maintain a supportive and encouraging tone."
        )
    return "You are a helpful and precise AI research assistant."

async def query_perplexica(query: str, focus_mode: str = "academic", history: list = None) -> str:
    if history is None:
        history = []
        
    system_prompt = get_system_prompt(focus_mode)
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": query})

    try:
        groq_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return groq_response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return "Sorry, I encountered an error with the AI service. Please try again later."
