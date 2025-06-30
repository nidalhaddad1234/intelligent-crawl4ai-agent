#!/bin/bash
set -e

echo "🚀 Starting Model Manager for Intelligent Crawl4AI Agent"
echo "=================================================="

# Wait for Ollama service to be ready
echo "⏳ Waiting for Ollama service..."
until curl -f "${OLLAMA_URL}/api/tags" >/dev/null 2>&1; do
    echo "   Ollama not ready yet, waiting..."
    sleep 5
done

echo "✅ Ollama is ready!"

# Run the model setup script
echo "📥 Setting up models..."
python3 /app/model_setup.py

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo "✅ Model setup completed successfully!"
    echo "🎯 DeepSeek-Coder-1.3B is ready for web scraping!"
else
    echo "❌ Model setup failed!"
    exit 1
fi

echo "=================================================="
echo "🎉 Model Manager completed successfully!"
