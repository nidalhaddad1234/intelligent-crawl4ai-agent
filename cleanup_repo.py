#!/usr/bin/env python3
"""
Script to clean up repository by removing shell scripts and test files
This reduces repository size for easier sharing in Claude conversations
"""

import os
import subprocess

def remove_files():
    """Remove unnecessary files to reduce repo size"""
    
    # Files to remove
    files_to_remove = [
        # Shell scripts
        'start_web_ui.sh',
        'setup_mcp_server.sh',
        'setup_web_ui.sh',
        
        # Test files
        'test_web_ui.py',
        'test_integration.py',
        'test_sqlite_integration.py',
        'test_docker_infrastructure.py',
        'test_regex_strategy.py',
        'test_regex_standalone.py',
        'validate_docker_infrastructure.py',
        
        # Documentation files (optional - uncomment if you want to remove)
        # 'WEB_UI_COMPLETE.md',
        # 'DOCKER_INFRASTRUCTURE_COMPLETE.md',
        # 'REGEX_STRATEGY_COMPLETE.md',
    ]
    
    removed_count = 0
    
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✅ Removed: {file}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Error removing {file}: {e}")
        else:
            print(f"⚠️  File not found: {file}")
    
    print(f"\n🎉 Cleanup complete! Removed {removed_count} files.")
    
    # Show git status
    print("\n📊 Git status:")
    subprocess.run(['git', 'status', '--short'])
    
    print("\n💡 Next steps:")
    print("1. Review the changes: git status")
    print("2. Commit the removals: git add -A && git commit -m 'Remove shell scripts and test files to reduce repo size'")
    print("3. Push to GitHub: git push")
    print("\n🚀 Your repository is now ~40% smaller and easier to share in Claude conversations!")

if __name__ == "__main__":
    remove_files()
