# web-research-agent

A simple yet powerful web research agent that can analyze complex queries, search the web, extract content, and synthesize comprehensive answers.

## Features

-  **Query Analysis**: Breaks down complex research questions into sub-questions
- **Web Search**: Uses Tavily API to search the web efficiently
- **Content Extraction**: Retrieves and processes relevant content from web pages
- **Information Synthesis**: Combines information from multiple sources into a coherent answer
- **Performance Optimization**: Includes caching to avoid repeated search

## Setup

### Prerequisites

- Python 3.8+
- OpenAI API key
- Tavily API key

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-research-agent.git
   cd ai-research-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

## Usage

### Command Line Interface

Run the agent from the command line:

```bash
python app.py --query "Your complex research question here"
```

#### Options:

- `--query` or `-q`: The research query to process
- `--output` or `-o`: Save results to a specified file
- `--skip-cache`: Skip using cached results
- `--max-sources`: Maximum number of sources to analyze (default: 10)

Example:
```bash
python app.py --query "What are the environmental impacts of electric vehicles compared to gas vehicles?" --output results.json
```

### As a Library

You can also use the agent programmatically:

```python
from app import research_workflow

results = research_workflow("Your research query here")
print(results["answer"])
```

## How It Works

1. **Query Analysis**: The agent breaks down your complex query into more manageable sub-questions.
2. **Web Search**: For each sub-question, the agent searches the web using the Tavily API.
3. **Content Extraction**: The agent extracts and processes content from the search results.
4. **Information Synthesis**: All gathered information is synthesized into a comprehensive answer.

## Project Structure

- `app.py` - Main application file
- `tools.py` - Core research tools (query analysis, web search, content extraction, synthesis)
- `utils.py` - Helper functions (caching, parallelization, text processing)

## Requirements

```
langchain
langchain-openai
langchain-community
bs4
requests
python-dotenv
```
