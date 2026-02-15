import asyncio
import requests
import google.generativeai as genai
from groq import Groq
import logging
import json
from typing import Dict, List
from bot.config import Config

logger = logging.getLogger(__name__)

# Initialize APIs with specified models
genai.configure(api_key=Config.GEMINI_API_KEY)
groq_client = Groq(api_key=Config.GROQ_API_KEY)

class SearchEngine:
    """Wrapper for academic search engines"""
    @staticmethod
    async def search(query: str, focus_mode: str = "academic") -> Dict:
        """Perform search across multiple academic engines CONCURRENTLY."""
        
        # Run all search tasks at the same time
        tasks = [
            SearchEngine._search_searxng(query, focus_mode),
            SearchEngine._search_arxiv(query),
            SearchEngine._search_semantic_scholar(query)
        ]
        
        results_list = await asyncio.gather(*tasks)
        
        results = {
            "searxng": results_list[0],
            "arxiv": results_list[1],
            "semantic_scholar": results_list[2]
        }
        
        return {"query": query, "focus_mode": focus_mode, "results": results}

    @staticmethod
    async def _search_searxng(query: str, focus_mode: str) -> List[Dict]:
        """SearXNG search with 30 results"""
        params = {
            "q": query,
            "format": "json",
            "categories": "science",
            "language": "en-US",
            "safesearch": 1,
            "limit": 30
        }
        try:
            response = requests.get("https://searxng.org/search", params=params, timeout=15)
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            logger.error(f"SearXNG Error: {e}")
            return []

    @staticmethod
    async def _search_arxiv(query: str) -> List[Dict]:
        """arXiv search with 30 results"""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": 30,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        try:
            response = requests.get("https://export.arxiv.org/api/query", params=params, timeout=15)
            response.raise_for_status()
            return response.json().get("entries", [])
        except Exception as e:
            logger.error(f"arXiv Error: {e}")
            return []

    @staticmethod
    async def _search_semantic_scholar(query: str) -> List[Dict]:
        """Semantic Scholar search with 30 results"""
        try:
            response = requests.get(
                "https://api.semanticscholar.org/graphql",
                json={"query": f"{{searchPaper(query: \"{query}\", limit: 30){{title url year abstract}}}}"},
                timeout=15
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("searchPaper", [])
        except Exception as e:
            logger.error(f"Semantic Scholar Error: {e}")
            return []

async def query_perplexica(query: str, focus_mode: str = "academic") -> str:
    """Academic research pipeline with 30 results per engine"""
    try:
        search_results = await SearchEngine.search(query, focus_mode)

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
                    3. Proper citations in APA format
                    4. Comprehensive analysis of all sources
                    """
                },
                {"role": "user", "content": query}
            ]
        )

        model = genai.GenerativeModel("gemini-2.5-flash")
        final_response = model.generate_content(
            f"Refine this academic response: {groq_response.choices[0].message.content}\n"
            "Ensure: 1. Proper academic tone 2. Clear structure 3. No hallucinations 4. Correct citations"
        )

        return final_response.text

    except Exception as e:
        logger.error(f"Search Error: {e}")
        return "Sorry, the research service is temporarily unavailable."
