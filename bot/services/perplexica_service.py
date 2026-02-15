import asyncio
import requests
from groq import Groq
import logging
import json
from typing import Dict, List
from bot.config import Config

logger = logging.getLogger(__name__)

# Initialize Groq client only (no Gemini)
groq_client = Groq(api_key=Config.GROQ_API_KEY)

class SearchEngine:
    """Wrapper for academic search engines - DuckDuckGo only"""
    @staticmethod
    async def search(query: str, focus_mode: str = "academic") -> Dict:
        """Perform search using only DuckDuckGo"""
        results = {
            "duckduckgo": await SearchEngine._search_duckduckgo(query, focus_mode)
        }
        return {"query": query, "focus_mode": focus_mode, "results": results}

    @staticmethod
    async def _search_duckduckgo(query: str, focus_mode: str) -> List[Dict]:
        """DuckDuckGo search with 30 results"""
        try:
            # Use the official DuckDuckGo API
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1
                },
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Add main result
            if data.get('Abstract'):
                results.append({
                    "title": data.get('Heading', 'Result'),
                    "url": data.get('AbstractURL', ''),
                    "description": data.get('Abstract', '')
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:29]:  # Limit to 29 more results
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        "title": topic.get('Text', 'Result'),
                        "url": topic.get('FirstURL', ''),
                        "description": topic.get('Result', '')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo Error: {e}")
            return []

async def query_perplexica(query: str, focus_mode: str = "academic") -> str:
    """Academic research pipeline using only DuckDuckGo and Groq"""
    try:
        search_results = await SearchEngine.search(query, focus_mode)

        # Use only Groq for both initial response and refinement
        groq_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": f"""
                    You are an academic assistant specializing in {focus_mode}.
                    Use ONLY these sources: {json.dumps(search_results, indent=2)}.
                    Format your response with:
                    1. Clear headings
                    2. Bullet points for key concepts
                    3. Proper citations where applicable
                    4. Comprehensive analysis of the information found
                    """
                },
                {"role": "user", "content": query}
            ]
        )

        # Get the initial response
        initial_response = groq_response.choices[0].message.content

        # Use Groq again for refinement (instead of Gemini)
        refinement_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Refine this academic response. Ensure: 1. Proper academic tone 2. Clear structure 3. No hallucinations 4. Correct citations"
                },
                {"role": "user", "content": initial_response}
            ]
        )

        return refinement_response.choices[0].message.content

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return "Sorry, the research service is temporarily unavailable."
