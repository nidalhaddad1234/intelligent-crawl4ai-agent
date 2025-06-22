# 🌐 Web UI Documentation

## ChatGPT-like Interface for Intelligent Crawl4AI Agent

The Web UI provides a modern, conversational interface for interacting with your intelligent scraping agent. It's designed to feel familiar and intuitive, similar to ChatGPT, while providing powerful web scraping capabilities.

## 🚀 Quick Start

### 1. Start the Web UI
```bash
# Start all services including Web UI
./start_web_ui.sh

# Or manually with docker-compose
docker-compose up -d web-ui
```

### 2. Access the Interface
Open your browser and go to: **http://localhost:8888**

### 3. Start Chatting
Try these example conversations:

**Getting Help:**
```
You: What can you help me with?
Assistant: [Explains all available features and capabilities]
```

**Simple Scraping:**
```
You: Scrape data from https://example.com
Assistant: [Analyzes the site and extracts data]
```

**Website Analysis:**
```
You: Analyze the structure of https://news.ycombinator.com
Assistant: [Provides technical analysis and recommendations]
```

**High-Volume Jobs:**
```
You: Process these 1000 URLs for business contact information
[Paste URLs or upload file]
Assistant: [Submits high-volume job and provides job ID]
```

## 🎯 Key Features

### **Conversational Interface**
- Natural language interaction
- Context-aware responses
- Session-based chat history
- Real-time communication via WebSocket

### **Smart Intent Detection**
The assistant automatically detects what you want to do:
- **Scraping requests**: "scrape", "extract", "get data"
- **Analysis requests**: "analyze", "examine", "check"
- **Job status**: "status", "progress", "job"
- **Search**: "find", "search", "look for"
- **Export**: "export", "download", "save"

### **Quick Actions**
Click the quick action buttons for common tasks:
- 💡 **Help**: Get information about capabilities
- 🔍 **Analyze URL**: Analyze website structure
- 🎯 **Scrape Data**: Extract data from URLs
- 📊 **System Status**: Check system health
- 💾 **Export Data**: Download your results

### **URL Input**
- Automatically shows URL input field when needed
- Supports multiple URLs (comma-separated)
- Validates URL formats

## 💬 Conversation Examples

### Example 1: Contact Information Extraction
```
You: I need to extract contact information from these business websites:
https://company1.com, https://company2.com, https://company3.com