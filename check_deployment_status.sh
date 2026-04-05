#!/bin/bash
# Monitor HF Spaces deployment status

SPACE_URL="https://huggingface.co/spaces/Lucifer4142T/sst"
API_URL="https://Lucifer4142T-sst.hf.space"

echo "🔍 Checking HF Spaces Deployment Status"
echo "========================================"
echo ""
echo "Space URL: $SPACE_URL"
echo "API URL: $API_URL"
echo ""

# Check Space status via huggingface-hub
echo "Checking Space status..."
hf spaces info Lucifer4142T/sst 2>&1 | head -20

echo ""
echo "Checking API health..."
for i in {1..30}; do
    echo -n "Attempt $i... "
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
    if [ "$response" = "200" ]; then
        echo "✅ UP (HTTP $response)"
        echo ""
        echo "Testing endpoints:"
        curl -s "$API_URL/health" | jq . 2>/dev/null || curl -s "$API_URL/health"
        echo ""
        curl -s "$API_URL/tasks" | jq . 2>/dev/null || curl -s "$API_URL/tasks"
        exit 0
    else
        echo "Building... (HTTP $response)"
    fi
    sleep 5
done

echo ""
echo "⏱️  Space is still building. Check status at:"
echo "$SPACE_URL/settings"
