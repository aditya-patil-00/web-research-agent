"""
utils.py - Simplified helper functions for the research agent
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment() -> bool:
    """
    Check if required environment variables are set.
    
    Returns:
        Boolean indicating success
    """
    required_vars = ["DEEPINFRA_API_TOKEN", "TAVILY_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("Environment variables validated successfully")
    return True

def generate_cache_key(data: Any) -> str:
    """
    Generate a unique cache key for input data.
    
    Args:
        data: The data to generate a cache key for
        
    Returns:
        A string hash that can be used as a cache key
    """
    if isinstance(data, str):
        str_to_hash = data
    else:
        try:
            str_to_hash = json.dumps(data, sort_keys=True)
        except:
            str_to_hash = str(data)
    
    return hashlib.md5(str_to_hash.encode()).hexdigest()

class SimpleCache:
    """Simple in-memory cache for storing results"""
    
    def __init__(self):
        self.cache = {}
        logger.info("In-memory cache initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """Get an item from the cache."""
        if key in self.cache:
            logger.info(f"Cache hit for {key}")
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Store an item in the cache."""
        self.cache[key] = value
        logger.info(f"Saved to cache: {key}")

def clean_text(text: str, max_length: int = 8000) -> str:
    """
    Clean and truncate text to a maximum length.
    
    Args:
        text: Input text to clean
        max_length: Maximum length to truncate to
        
    Returns:
        Cleaned and truncated text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if necessary
    suffix = "... [Content truncated]"
    if len(text) > max_length:
        # Account for the length of the suffix
        text = text[:max_length - len(suffix)] + suffix
    
    return text

def format_search_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format search results for display.
    
    Args:
        results: Raw search results
        
    Returns:
        Formatted results for display
    """
    formatted = {}
    
    if "title" in results:
        formatted["title"] = results["title"]
    if "url" in results:
        formatted["url"] = results["url"]
    if "content" in results:
        formatted["content"] = clean_text(results["content"], 300)
    
    return formatted