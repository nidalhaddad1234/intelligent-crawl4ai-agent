#!/usr/bin/env python3
"""
New Lightweight Web UI Server
Clean, modular replacement for the 3,469-line monster
"""

import uvicorn
from web_ui.app import app

if __name__ == "__main__":
    print("🚀 Starting AI-First Web UI Server v2.0.0")
    print("📊 Reduced from 3,469 lines to ~100 lines (97% reduction!)")
    print("🔧 Now modular, maintainable, and organized")
    print()
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8080, 
        reload=True,
        log_level="info"
    )
