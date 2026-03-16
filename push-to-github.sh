#!/bin/bash
# Auto-push Task Safety Framework to GitHub
# Run this AFTER creating the repo at https://github.com/new

echo "🐶 Pushing Task Safety Framework to GitHub..."
echo ""

cd /home/chen/.openclaw/workspace/task-safety-framework

# Set remote to SSH (uses existing SSH key)
git remote set-url origin git@github.com:chenqin2026/task-safety-framework.git

# Push to main branch
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Repository pushed to:"
    echo "   https://github.com/chenqin2026/task-safety-framework"
    echo ""
    echo "📦 Next steps:"
    echo "   1. Add description: 'Checkpointing and recovery framework for long-running Python tasks'"
    echo "   2. Add topics: python, checkpointing, recovery, ml-training, automation"
    echo "   3. Enable Issues and Discussions"
else
    echo ""
    echo "❌ Push failed. Make sure:"
    echo "   1. You created the repo at: https://github.com/new"
    echo "   2. Repo name is exactly: task-safety-framework"
    echo "   3. Your SSH key is added to GitHub: https://github.com/settings/keys"
    echo ""
    echo "   Your public key:"
    cat ~/.ssh/id_rsa.pub
fi
