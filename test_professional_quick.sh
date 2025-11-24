#!/bin/bash
echo "🧪 Testing Professional Rendering Endpoint..."
echo ""

# Test with result.jpg
if [ -f "result.jpg" ]; then
    echo "📸 Testing with result.jpg..."
    RESPONSE=$(curl -X POST http://localhost:8000/api/nails/render-professional \
        -F "file=@result.jpg" \
        -F "material=metallic_gold" \
        --silent --output /dev/null \
        --write-out "HTTP_CODE:%{http_code}|TIME:%{time_total}s")
    
    HTTP_CODE=$(echo $RESPONSE | cut -d'|' -f1 | cut -d':' -f2)
    TIME=$(echo $RESPONSE | cut -d'|' -f2 | cut -d':' -f2)
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Professional endpoint working! (${TIME})"
        echo ""
        echo "🌐 Frontend should now work at:"
        echo "   http://localhost:8080/frontend/app-realtime.html"
        echo ""
        echo "📝 To test:"
        echo "   1. Open the URL above"
        echo "   2. Click 'Start Camera'"
        echo "   3. Select 'Professional' mode"
        echo "   4. Choose 'Metallic Gold' preset"
        echo "   5. Click 'Segment Nails'"
        echo "   6. See beautiful photo-realistic nails! ✨"
    else
        echo "❌ Endpoint returned HTTP $HTTP_CODE"
        echo "   Check if backend is running: uvicorn main:app --reload"
    fi
else
    echo "⚠️  No test image found. Try with a nail photo."
fi
