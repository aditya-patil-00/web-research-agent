"""
tools.py - Core tools for the research agent
Contains functions for query analysis, web search, content extraction, and synthesis
"""

import os
import json
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_community.tools.tavily_search import TavilySearchResults

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the model
model = ChatOpenAI(model="gpt-4o")

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
        
        Format your response as a JSON object with lists of sub-questions and search queries.
        """),
        ("human", "{query}")
    ])
    
    class QueryAnalysisResponse(BaseModel):
        sub_questions: List[Dict[str, str]] = Field(description="List of sub-questions with reasoning")
        search_queries: List[str] = Field(description="List of optimized search queries")
    
    output_parser = PydanticOutputParser(pydantic_object=QueryAnalysisResponse)
    
    chain = analysis_prompt | model | output_parser
    
    try:
        result = chain.invoke({"query": query})
        logger.info(f"Query analyzed successfully. Identified {len(result.sub_questions)} sub-questions")
        return {
            "sub_questions": result.sub_questions,
            "search_queries": result.search_queries
        }
    except Exception as e:
        logger.error(f"Error in query analysis: {e}")
        # Fallback to simpler analysis if parsing fails
        simple_prompt = ChatPromptTemplate.from_messages([
            ("system", "Break down this research query into 3-5 key search queries."),
            ("human", "{query}")
        ])
        simple_chain = simple_prompt | model | StrOutputParser()
        result = simple_chain.invoke({"query": query})
        search_queries = [line.strip().replace("- ", "") for line in result.split('\n') if line.strip()]
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
        if len(text) > 20000:
            text = text[:20000] + "... [Content truncated due to length]"
            
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
    
    # Prepare context from search results
    context = ""
    for i, result in enumerate(search_results):
        if 'content' in result and result['content']:
            # Add a snippet of the content (first 500 chars)
            content_snippet = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
            context += f"\nSource {i+1}: {result.get('title', 'Untitled')}\n"
            context += f"URL: {result.get('url', 'No URL')}\n"
            context += f"Content snippet: {content_snippet}\n"
    
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
        
        Write in clear, professional language. Use proper formatting for readability including paragraphs, bullets, 
        and sections as appropriate.
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