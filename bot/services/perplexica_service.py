import asyncio
import requests
from groq import Groq
import logging
import json
from typing import Dict, List
from bot.config import Config

logger = logging.getLogger(__name__)

# Initialize Groq client only
groq_client = Groq(api_key=Config.GROQ_API_KEY)

class SearchEngine:
    """Wrapper for academic search engines - using a more reliable method"""
    @staticmethod
    async def search(query: str, focus_mode: str = "academic") -> Dict:
        """Perform search using a more reliable method"""
        # For now, we'll use Groq to generate a response without external search
        # This avoids the DuckDuckGo API issues entirely
        return {"query": query, "focus_mode": focus_mode, "results": []}

async def query_perplexica(query: str, focus_mode: str = "academic") -> str:
    """Academic research pipeline using only Groq (no external search for now)"""
    try:
        # Use only Groq for the response
        groq_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are an expert on Nigerian University Admission and academic subjects.
                    Provide accurate, concise information based on your knowledge.
                    Format your response with:
                    1. Clear headings
                    2. Bullet points for key concepts
                    3. Proper structure for the requested information
                    """
                },
                {"role": "user", "content": query}
            ]
        )

        return groq_response.choices[0].message.content

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return "Sorry, the research service is temporarily unavailable."
