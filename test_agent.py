import pytest
from unittest.mock import Mock, patch
from tools import analyze_query, web_search, extract_content, synthesize_information

# Test data
SAMPLE_QUERY = "What are the effects of climate change?"
MOCK_SEARCH_RESULT = [{
    "title": "Climate Change Effects",
    "url": "https://example.com/climate",
    "content": "Rising temperatures and sea levels are major effects of climate change.",
    "source": "tavily"
}]

# Test query analysis
def test_analyze_query_basic():
    """Test basic query analysis functionality"""
    result = analyze_query(SAMPLE_QUERY)
    
    # Check structure
    assert isinstance(result, dict)
    assert "sub_questions" in result
    assert "search_queries" in result
    
    # Check content
    assert len(result["sub_questions"]) > 0
    assert len(result["search_queries"]) > 0
    assert all(isinstance(q, dict) for q in result["sub_questions"])
    assert all(isinstance(q, str) for q in result["search_queries"])

def test_analyze_query_invalid():
    """Test query analysis with invalid inputs"""
    # Test None input
    with pytest.raises(TypeError):
        analyze_query(None)
    
    # Test empty string
    with pytest.raises(ValueError):
        analyze_query("")
    
    # Test whitespace only
    with pytest.raises(ValueError):
        analyze_query("   ")

# Test web search
@patch('tools.tavily_search')
def test_web_search_basic(mock_tavily):
    """Test basic web search functionality"""
    # Setup mock
    mock_tavily.invoke.return_value = MOCK_SEARCH_RESULT
    
    # Test search
    results = web_search(SAMPLE_QUERY)
    
    # Verify structure
    assert isinstance(results, list)
    assert len(results) > 0
    
    # Verify content
    result = results[0]
    assert "title" in result
    assert "url" in result
    assert "content" in result
    assert "source" in result

@patch('tools.tavily_search')
def test_web_search_error(mock_tavily):
    """Test web search error handling"""
    # Simulate API error
    mock_tavily.invoke.side_effect = Exception("API Error")
    
    # Should return empty list on error
    results = web_search(SAMPLE_QUERY)
    assert results == []

# Test content extraction
def test_extract_content_invalid():
    """Test content extraction with invalid URL"""
    result = extract_content("not_a_valid_url")
    assert "Failed to extract content" in result

# Test information synthesis
def test_synthesize_information_basic():
    """Test basic information synthesis"""
    # Test data
    sub_questions = [{"question": "What causes climate change?", "reasoning": "Understanding causes"}]
    
    # Test synthesis
    result = synthesize_information(
        main_query=SAMPLE_QUERY,
        search_results=MOCK_SEARCH_RESULT,
        sub_questions=sub_questions
    )
    
    # Verify output
    assert isinstance(result, str)
    assert len(result) > 0

# Test full workflow
@patch('tools.web_search')
def test_basic_workflow(mock_search):
    """Test the basic research workflow"""
    # Setup mock
    mock_search.return_value = MOCK_SEARCH_RESULT
    
    # Step 1: Query Analysis
    analysis = analyze_query(SAMPLE_QUERY)
    assert analysis is not None
    assert len(analysis["sub_questions"]) > 0
    
    # Step 2: Web Search
    search_results = web_search(analysis["search_queries"][0])
    assert len(search_results) > 0
    
    # Step 3: Synthesis
    result = synthesize_information(
        SAMPLE_QUERY,
        search_results,
        analysis["sub_questions"]
    )
    assert isinstance(result, str)
    assert len(result) > 0

if __name__ == "__main__":
    pytest.main([__file__])