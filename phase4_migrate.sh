#!/bin/bash
# Phase 4: Migration Script - Remove Hardcoded Logic

echo "🚀 Phase 4: Migrating to AI-First Architecture"
echo "============================================="

# Step 1: Backup original files
echo "📦 Step 1: Creating backups..."
if [ -f "web_ui_server.py" ]; then
    cp web_ui_server.py web_ui_server_v1_rule_based.py
    echo "✅ Backed up web_ui_server.py"
fi

# Step 2: Create migration branch
echo -e "\n🌿 Step 2: Git operations..."
git add -A
git commit -m "Phase 4: Backup before AI-first migration"
git tag v1-rule-based-backup

# Step 3: Test AI planning
echo -e "\n🧪 Step 3: Testing AI planning system..."
cd ai_core
python test_ai_planning.py

echo -e "\n📋 Migration Checklist:"
echo "----------------------"
echo "[ ] 1. Ollama is running and deepseek-coder:1.3b is available"
echo "[ ] 2. AI planning tests show correct plans"
echo "[ ] 3. Backup files created successfully"
echo "[ ] 4. Ready to replace web_ui_server.py with AI-first version"
echo "[ ] 5. All tools are registered and working"

echo -e "\n🎯 Next Steps:"
echo "1. Review the AI planning test results above"
echo "2. If plans look good, run: python migrate_web_ui.py"
echo "3. Test the new AI-first server"
echo "4. Delete old hardcoded methods"

echo -e "\n⚠️  Rollback Command:"
echo "git checkout v1-rule-based-backup -- web_ui_server.py"
