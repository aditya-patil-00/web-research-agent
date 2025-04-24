"""
tools.py - Core tools for the research agent updated to use open source models
"""

import os
import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.chat_models import ChatOpenAI
import torch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check for GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

# Initialize the model using OpenAI-compatible API
try:
    model = ChatOpenAI(
        model="meta-llama/Meta-Llama-3-70B-Instruct",
        temperature=0.1,
        max_tokens=2048,
        openai_api_key=os.getenv("DEEPINFRA_API_TOKEN"),
        openai_api_base="https://api.deepinfra.com/v1/openai",
    )
    logger.info("Initialized Llama 3 70B model")
except Exception as e:
    logger.error(f"Failed to initialize Llama model: {e}")
    logger.info("Please ensure you have set the DEEPINFRA_API_TOKEN environment variable")
    raise e

# Initialize search tool
tavily_search = TavilySearchResults(max_results=5)

class SubQuestion(BaseModel):
    """Model for a sub-question."""
    question: str = Field(description="The sub-question text")
    reasoning: str = Field(description="Reasoning why this sub-question is relevant")

class QueryAnalysis(BaseModel):
    """Model for query analysis output."""
    sub_questions: List[SubQuestion] = Field(description="List of sub-questions")
    search_queries: List[str] = Field(description="Optimized search queries for each sub-question")

def analyze_query(query: str) -> Dict[str, Any]:
    """
    Analyze a complex query and break it down into sub-questions.
    
    Args:
        query: The main research query
        
    Returns:
        Dictionary containing sub-questions and search queries
    """
    logger.info(f"Analyzing query: {query}")
    
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert at breaking down complex research questions into simpler components.
        Given a main research query, you need to:
        
        1. Identify 3-5 key sub-questions that would help answer the main query
        2. For each sub-question, provide brief reasoning on why it's relevant
        3. Create an optimized search query for each sub-question that would yield good search results
        
        Output in this exact format with no other text:
        SUB-QUESTIONS:
        1. [First sub-question]
        - Reasoning: [Why this sub-question is relevant]
        - Search query: [Optimized search query]
        
        2. [Second sub-question]
        - Reasoning: [Why this sub-question is relevant]
        - Search query: [Optimized search query]
        
        [and so on...]
        """),
        ("human", "{query}")
    ])
    
    chain = analysis_prompt | model | StrOutputParser()
    
    try:
        result = chain.invoke({"query": query})
        logger.info("Query analyzed successfully")
        
        # Parse the structured text format
        sub_questions = []
        search_queries = []
        
        lines = result.strip().split('\n')
        current_question = None
        current_reasoning = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for numbered questions
            if line[0].isdigit() and '. ' in line:
                if current_question is not None and current_reasoning is not None:
                    sub_questions.append({
                        "question": current_question, 
                        "reasoning": current_reasoning
                    })
                
                current_question = line.split('. ', 1)[1].strip()
                current_reasoning = None
            
            # Check for reasoning
            elif '- Reasoning:' in line:
                current_reasoning = line.split('- Reasoning:', 1)[1].strip()
            
            # Check for search query
            elif '- Search query:' in line:
                search_query = line.split('- Search query:', 1)[1].strip()
                search_queries.append(search_query)
        
        # Add the last question
        if current_question is not None and current_reasoning is not None:
            sub_questions.append({
                "question": current_question, 
                "reasoning": current_reasoning
            })
        
        # If parsing didn't go as expected, create a simple structure
        if not sub_questions or len(sub_questions) != len(search_queries):
            logger.warning("Parsing failed, using a simplified approach")
            
            # Extract questions using a simpler method - look for numbered items
            sub_questions = []
            search_queries = []
            
            for line in lines:
                line = line.strip()
                if line and line[0].isdigit() and '. ' in line:
                    question = line.split('. ', 1)[1].strip()
                    sub_questions.append({"question": question, "reasoning": ""})
                    search_queries.append(question)
            
            # If still nothing, just split the query
            if not sub_questions:
                sub_questions = [{"question": query, "reasoning": ""}]
                search_queries = [query]
        
        logger.info(f"Identified {len(sub_questions)} sub-questions")
        return {
            "sub_questions": sub_questions,
            "search_queries": search_queries
        }
        
    except Exception as e:
        logger.error(f"Error in query analysis: {e}")
        # Fallback to simpler analysis
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", "Split this query into 3 search queries, one per line:"),
            ("human", "{query}")
        ])
        fallback_chain = fallback_prompt | model | StrOutputParser()
        result = fallback_chain.invoke({"query": query})
        search_queries = [line.strip() for line in result.split('\n') if line.strip()]
        
        # Ensure we have at least one query
        if not search_queries:
            search_queries = [query]
            
        return {
            "sub_questions": [{"question": q, "reasoning": ""} for q in search_queries],
            "search_queries": search_queries
        }

def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a web search using Tavily API.
    
    Args:
        query: The search query
        num_results: Number of results to return
        
    Returns:
        List of search results with URLs and snippets
    """
    logger.info(f"Searching web for: {query}")
    
    try:
        search_results = tavily_search.invoke(query)
        
        # Process and clean up results
        cleaned_results = []
        for result in search_results:
            cleaned_results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "source": "tavily"
            })
            
        logger.info(f"Found {len(cleaned_results)} search results")
        return cleaned_results
    
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return []

def extract_content(url: str) -> str:
    """
    Extract content from a web page using Beautiful Soup.
    
    Args:
        url: The URL to extract content from
        
    Returns:
        Extracted text content from the page
    """
    logger.info(f"Extracting content from: {url}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.extract()
            
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up text (remove extra spaces, newlines, etc.)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully extracted content: {len(text)} characters")
        
        # If text is too long, truncate it
        if len(text) > 15000:
            text = text[:15000] + "... [Content truncated due to length]"
            
        return text
    
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return f"Failed to extract content: {str(e)}"

def synthesize_information(main_query: str, search_results: List[Dict[str, Any]], sub_questions: List[Dict[str, str]]) -> str:
    """
    Synthesize information from search results into a comprehensive answer.
    
    Args:
        main_query: The original research query
        search_results: List of search results with content
        sub_questions: List of sub-questions that were analyzed
        
    Returns:
        Synthesized answer to the main query
    """
    logger.info(f"Synthesizing information from {len(search_results)} search results")
    
    # Prepare context from search results - limit to avoid context length issues
    context = ""
    results_used = 0
    
    for i, result in enumerate(search_results):
        if 'content' in result and result['content'] and results_used < 6:
            # Add a snippet of the content (first 300 chars)
            content_snippet = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
            context += f"\nSource {i+1}: {result.get('title', 'Untitled')}\n"
            context += f"URL: {result.get('url', 'No URL')}\n"
            context += f"Content snippet: {content_snippet}\n"
            results_used += 1
    
    # Create list of sub-questions for context
    sub_questions_text = "\n".join([f"- {sq['question']}" for sq in sub_questions])
    
    synthesis_prompt = ChatPromptTemplate.from_messages([
        ("system", """
        You are an expert researcher who synthesizes information from multiple sources to answer complex questions.
        Given a main research query, related sub-questions, and information from several web sources, create a comprehensive,
        well-structured answer that addresses the main query.
        
        Your response should:
        1. Begin with a concise summary that directly answers the main query
        2. Organize information logically by sub-topics or aspects of the question
        3. Cite sources when presenting specific information
        4. Be comprehensive but focused on the most relevant information
        5. Identify any gaps in the available information or areas that need further research
        
        Write in clear, professional language.
        """),
        ("human", """
        Main Research Query: {main_query}
        
        Sub-questions explored:
        {sub_questions}
        
        Sources Information:
        {context}
        
        Please synthesize a comprehensive answer to the main research query based on this information.
        """)
    ])
    
    chain = synthesis_prompt | model | StrOutputParser()
    
    try:
        result = chain.invoke({
            "main_query": main_query,
            "sub_questions": sub_questions_text,
            "context": context
        })
        
        logger.info("Successfully synthesized information")
        return result
    
    except Exception as e:
        logger.error(f"Error in synthesis: {e}")
        return f"Failed to synthesize information: {str(e)}"