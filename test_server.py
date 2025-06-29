#!/usr/bin/env python3
"""Simple test server to verify setup"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
import os

app = FastAPI()

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head><title>Intelligent Crawl4AI</title></head>
        <body>
            <h1>🚀 Intelligent Crawl4AI Agent</h1>
            <p>Web UI is starting up...</p>
            <p>Services:</p>
            <ul>
                <li>Ollama URL: {}</li>
                <li>ChromaDB URL: {}</li>
                <li>Redis URL: {}</li>
                <li>PostgreSQL URL: {}</li>
            </ul>
            <p>If you see this page, the basic server is working!</p>
        </body>
    </html>
    """.format(
        os.getenv('OLLAMA_URL', 'Not set'),
        os.getenv('CHROMADB_URL', 'Not set'),
        os.getenv('REDIS_URL', 'Not set'),
        os.getenv('POSTGRES_URL', 'Not set')
    ))

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🌐 Starting simple test server on port 8888...")
    uvicorn.run(app, host="0.0.0.0", port=8888)
