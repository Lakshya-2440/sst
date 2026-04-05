#!/bin/bash
# Complete HF Spaces deployment in one command

set -e

echo "🚀 HF Spaces Deployment Script"
echo "=============================="
echo ""

# Check if hf CLI is available
if ! command -v hf &> /dev/null; then
    echo "❌ hf CLI not found. Install with: pip install huggingface-hub"
    exit 1
fi

# Step 1: Authenticate
echo "Step 1: Authenticating with Hugging Face..."
echo "Get your token from: https://huggingface.co/settings/tokens"
echo ""
hf auth login

# Verify authentication
echo ""
echo "Verifying authentication..."
hf auth whoami
echo ""

# Step 2: Push to HF Spaces
echo "Step 2: Pushing to HF Spaces..."
cd /Users/lakshyagupta/Desktop/sst
git push origin main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Space URL: https://huggingface.co/spaces/Lucifer4142T/sst"
echo "⏱️  Wait 5-10 minutes for Docker build to complete"
echo ""
echo "After deployment, test with:"
echo "  • curl https://huggingface.co/spaces/Lucifer4142T/sst/health"
echo "  • python validate.py"
echo "  • python inference.py (if API credentials configured)"
