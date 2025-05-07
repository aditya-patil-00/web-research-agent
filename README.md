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

- Python 3.8+ (for local development)
- Docker (for containerized deployment)
- DEEPINFRA API key
- Tavily API key

### Installation

#### Option 1: Local Development

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/web-research-agent.git
   cd web-research-agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   DEEPINFRA_API_TOKEN=your_openai_key_here
   TAVILY_API_KEY=your_tavily_key_here
   ```

#### Option 2: Docker Deployment

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/web-research-agent.git
   cd web-research-agent
   ```

2. Build the Docker image:
   ```
   docker build -t web-research-agent .
   ```

3. Run the container:
   ```
   docker run -p 8501:8501 \
     -e DEEPINFRA_API_TOKEN=your_openai_key_here \
     -e TAVILY_API_KEY=your_tavily_key_here \
     web-research-agent
   ```

   The application will be available at `http://localhost:8501`

## Usage

### Local Development

Run the agent from the command line:
   ```
   streamlit run app.py
   ```

### Docker Deployment

After starting the container, access the web interface at `http://localhost:8501`

## How It Works

1. **Query Analysis**: The agent breaks down your complex query into more manageable sub-questions.
2. **Web Search**: For each sub-question, the agent searches the web using the Tavily API.
3. **Content Extraction**: The agent extracts and processes content from the search results.
4. **Information Synthesis**: All gathered information is synthesized into a comprehensive answer.

## Workflow

![workflow](https://i.imgur.com/1btUWJe.png)

## Project Structure

- `app.py` - Main application file
- `tools.py` - Core research tools (query analysis, web search, content extraction, synthesis)
- `utils.py` - Helper functions (caching, parallelization, text processing)
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies
- `.dockerignore` - Docker build exclusions

## Requirements

### Python Dependencies
```
langchain
langchain-openai
langchain-community
bs4
requests
python-dotenv
```

### Docker Dependencies
- Docker Engine 20.10.0 or later
- Docker Compose (optional, for multi-container setups)

## Troubleshooting

### Common Issues

1. **No Search Results**
   - Clear the cache using the "Clear Cache" button
   - Verify your API keys are correct
   - Try a simpler or more general query

2. **Docker Issues**
   - Ensure Docker is running
   - Check if port 8501 is available
   - Verify environment variables are set correctly

3. **API Key Issues**
   - Make sure both DEEPINFRA_API_TOKEN and TAVILY_API_KEY are set
   - Verify the keys are valid and have sufficient permissions
   - Check for any rate limiting or quota issues
