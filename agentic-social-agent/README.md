# Agentic Social Agent

A comprehensive news processing workflow built with LangGraph that searches, processes, and generates social media content from local news sources.

## Features

- 🔍 **News Search**: Search for latest news using Tavily API
- 📄 **Content Extraction**: Extract and process article content
- 💾 **Data Storage**: Store articles and metadata in MongoDB
- 🔤 **Text Embedding**: Create embeddings for semantic search
- 📝 **Content Summarization**: Generate AI-powered summaries
- 📱 **Social Media Posts**: Create posts for different platforms
- 📊 **Poll Creation**: Generate engagement polls from news topics
- 📋 **Comprehensive Logging**: Detailed logging and error tracking
- 🛡️ **Error Handling**: Graceful fallbacks and error recovery

## Architecture

The system is built as a LangGraph workflow with the following agents:

1. **News Search** (`news_search.py`) - Searches for articles using Tavily
2. **Info Extraction** (`info_extraction.py`) - Extracts content and 5W1H information
3. **Article Storage** (`article_storage.py`) - Stores articles in MongoDB
4. **Embedding** (`embed.py`) - Creates text embeddings for semantic search
5. **Summarization** (`summarize.py`) - Generates article summaries
6. **Post Generation** (`post_generation.py`) - Creates social media posts
7. **Poll Creation** (`poll_creation.py`) - Generates engagement polls

## Logging and Error Handling

### Structured Logging

The system includes comprehensive logging with:

- **File Logging**: Detailed logs saved to `logs/` directory
- **Console Logging**: Real-time progress updates
- **Structured Data**: JSON-formatted log entries with metadata
- **Performance Tracking**: Timing and metrics for each step
- **Error Tracking**: Full error context and tracebacks

### Error Handling Features

- **Graceful Degradation**: System continues running even if individual steps fail
- **Fallback Mechanisms**: Default responses when services are unavailable
- **Input Validation**: Comprehensive validation of environment variables and input data
- **API Error Handling**: Specific handling for OpenAI, Tavily, and MongoDB errors
- **Connection Management**: Proper cleanup of database connections

## Setup

### Prerequisites

- Python 3.8+
- MongoDB (optional, for data persistence)
- OpenAI API key
- Tavily API key

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   MONGODB_URI=your_mongodb_connection_string
   ```

### Running the Application

```bash
python main.py
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for AI processing |
| `TAVILY_API_KEY` | Yes | Tavily API key for news search |
| `MONGODB_URI` | No | MongoDB connection string (optional) |

## Output

The workflow produces:

- **Articles**: Raw news articles with metadata
- **Summaries**: AI-generated article summaries
- **Embeddings**: Vector embeddings for semantic search
- **Social Media Posts**: Posts for different character limits (50, 100, 500)
- **Polls**: Engagement polls based on news topics
- **Metrics**: Performance and processing metrics

## Log Files

Logs are stored in the `logs/` directory with the following structure:

```
logs/
├── workflow_<id>_<timestamp>.log    # Detailed workflow logs
└── ...
```

Each log file contains:
- Step-by-step execution details
- API call metrics and timing
- Error information with full context
- Performance metrics
- Data processing statistics

## Error Recovery

The system includes several error recovery mechanisms:

### MongoDB Connection Issues
- Graceful fallback when MongoDB is unavailable
- Continues processing without data persistence
- Logs connection attempts and failures

### API Rate Limits
- Automatic retry logic for transient failures
- Graceful degradation when APIs are unavailable
- Detailed logging of API call failures

### Data Validation
- Input validation at each step
- Fallback values for missing data
- Comprehensive error reporting

## Monitoring and Debugging

### Real-time Monitoring
- Console output shows progress in real-time
- Step-by-step execution tracking
- Performance metrics for each operation

### Debugging Features
- Detailed error messages with context
- Full stack traces for debugging
- Input/output validation logging
- API call timing and success rates

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   - Ensure all required environment variables are set
   - Check `.env` file format and permissions

2. **MongoDB Connection Issues**
   - Verify MongoDB URI format
   - Check network connectivity
   - System will continue without MongoDB

3. **API Rate Limits**
   - Monitor API usage in logs
   - Consider implementing rate limiting
   - System includes retry logic

## Contributing

When contributing to this project:

1. Follow the existing error handling patterns
2. Add comprehensive logging to new features
3. Include fallback mechanisms for critical operations
4. Update documentation for new features
5. Add tests for error scenarios 