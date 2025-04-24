"""
app.py - Streamlit UI for the research agent using open source model
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv
import logging

# Import our modules
from tools import analyze_query, web_search, extract_content, synthesize_information
from utils import setup_environment, SimpleCache, generate_cache_key, clean_text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize cache
cache = SimpleCache()

def research_workflow(query, progress_bar=None, status_text=None):
    """
    Execute the research workflow with Streamlit progress updates.
    
    Args:
        query: The main research query
        progress_bar: Streamlit progress bar
        status_text: Streamlit status text element
        
    Returns:
        Dictionary containing research results
    """
    if progress_bar:
        progress_bar.progress(0.05)
    if status_text:
        status_text.text("Analyzing query...")
    
    # Step 1: Query Analysis
    cache_key = f"analysis_{generate_cache_key(query)}"
    analysis = cache.get(cache_key)
    
    if analysis is None:
        analysis = analyze_query(query)
        cache.set(cache_key, analysis)
    
    sub_questions = analysis["sub_questions"]
    search_queries = analysis["search_queries"]
    
    if progress_bar:
        progress_bar.progress(0.2)
    if status_text:
        status_text.text(f"Query broken down into {len(sub_questions)} sub-questions")
    
    # Results structure
    results = {
        "main_query": query,
        "sub_questions": [],
        "answer": None
    }
    
    # Step 2 & 3: Web Search and Content Extraction for each sub-question
    total_steps = len(sub_questions)
    for i, (sub_q, search_q) in enumerate(zip(sub_questions, search_queries)):
        if status_text:
            status_text.text(f"Researching sub-question {i+1}/{total_steps}: {sub_q['question']}")
        
        sub_q_results = {
            "question": sub_q["question"],
            "reasoning": sub_q.get("reasoning", ""),
            "sources": []
        }
        
        # Search for this sub-question
        search_cache_key = f"search_{generate_cache_key(search_q)}"
        search_results = cache.get(search_cache_key)
        
        if search_results is None:
            search_results = web_search(search_q, num_results=3)
            cache.set(search_cache_key, search_results)
        
        # Process each search result
        for result in search_results:
            if 'url' in result and result['url']:
                content_cache_key = f"content_{generate_cache_key(result['url'])}"
                content = cache.get(content_cache_key)
                
                if content is None and 'content' not in result:
                    content = extract_content(result['url'])
                    cache.set(content_cache_key, content)
                    result['content'] = content
                elif content is not None:
                    result['content'] = content
                
            sub_q_results["sources"].append(result)
        
        results["sub_questions"].append(sub_q_results)
        
        if progress_bar:
            progress = 0.2 + ((i + 1) / total_steps) * 0.5
            progress_bar.progress(progress)
    
    # Step 4: Synthesize Information
    if status_text:
        status_text.text("Synthesizing information...")
    
    all_sources = []
    for sq in results["sub_questions"]:
        all_sources.extend(sq["sources"])
    
    answer = synthesize_information(query, all_sources, sub_questions)
    results["answer"] = answer
    
    if progress_bar:
        progress_bar.progress(1.0)
    if status_text:
        status_text.text("Research completed!")
    
    return results

def main():
    """Main Streamlit app function"""
    st.set_page_config(
        page_title="AI Research Agent",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 AI Research Agent")
    st.write("Research complex topics with an AI assistant that searches the web for you.")
    
    # Display model info
    st.info("This app uses Llama 3 70B Instruct, Meta's latest large language model, for analysis and synthesis.")
    
    # Check for required API keys
    if not os.getenv("TAVILY_API_KEY") or not os.getenv("DEEPINFRA_API_TOKEN"):
        st.error("Missing required API keys. Please set the TAVILY_API_KEY and DEEPINFRA_API_TOKEN environment variables.")
        st.info("You can get a free Tavily API key at https://tavily.com")
        st.info("You can get a DeepInfra API token at https://deepinfra.com")
        return
    
    # Query input
    query = st.text_area("Enter your research question:", height=100)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        search_button = st.button("Research", type="primary", use_container_width=True)
    with col2:
        clear_cache = st.button("Clear Cache", use_container_width=False)
    
    if clear_cache:
        global cache
        cache = SimpleCache()
        st.success("Cache cleared!")
    
    if search_button and query:
        start_time = time.time()
        
        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Run research workflow
            with st.spinner("Researching... This may take a minute with the open source model."):
                results = research_workflow(query, progress_bar, status_text)
            
            # Display results
            elapsed_time = time.time() - start_time
            st.success(f"Research completed in {elapsed_time:.2f} seconds")
            
            # Show the main answer
            st.header("Research Results")
            st.markdown(results["answer"])
            
            # Show sources in an expander
            with st.expander("Show Research Process"):
                for i, sub_q in enumerate(results["sub_questions"]):
                    st.subheader(f"Sub-question {i+1}: {sub_q['question']}")
                    if sub_q.get("reasoning"):
                        st.write(f"*Reasoning: {sub_q['reasoning']}*")
                    
                    # Display sources in a table
                    sources_data = []
                    for src in sub_q["sources"]:
                        if src.get("title") and src.get("url"):
                            sources_data.append({
                                "Title": src.get("title"),
                                "URL": src.get("url"),
                                "Snippet": clean_text(src.get("content", ""), 200)
                            })
                    
                    if sources_data:
                        st.write("Sources:")
                        for src in sources_data:
                            with st.container():
                                st.write(f"**{src['Title']}**")
                                st.write(f"[{src['URL']}]({src['URL']})")
                                st.write(src['Snippet'])
                                st.divider()
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.error(f"Error in research workflow: {e}")
        
        finally:
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
    
    # Add some spacing
    st.write("")
    
    # Add footer with information
    st.markdown("---")
    st.write("This AI Research Agent can help you research complex topics by breaking them down, searching the web, and synthesizing information.")
    
    # Add tips for better results
    with st.expander("Tips for better results"):
        st.markdown("""
        - Be specific in your questions
        - Include key terms and concepts
        - For complex topics, try to limit scope (e.g., "environmental impact of EVs in urban areas" instead of just "electric vehicles")
        - If you're not getting good results, try rephrasing your question
        - The open-source model may be slower and less capable than commercial models, so be patient and keep queries focused
        """)

if __name__ == "__main__":
    main()