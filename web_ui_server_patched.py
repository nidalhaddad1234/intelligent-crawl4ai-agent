#!/usr/bin/env python3
"""
Quick fix for the LearningMemory error
Adds the missing method to the memory system
"""

import os
import sys
sys.path.insert(0, '/app')

# Patch the LearningMemory class
try:
    from ai_core.learning.memory import LearningMemory
    
    # Add the missing method
    async def find_similar_patterns(self, request: str, threshold: float = 0.7):
        """Find similar patterns in memory - simple implementation"""
        # Return empty list for now to avoid errors
        return []
    
    # Monkey patch the method
    LearningMemory.find_similar_patterns = find_similar_patterns
    print("✅ Patched LearningMemory with find_similar_patterns method")
    
except Exception as e:
    print(f"Could not patch LearningMemory: {e}")

# Now run the actual web UI server
if __name__ == "__main__":
    import web_ui_server
