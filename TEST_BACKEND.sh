#!/bin/bash
# Test if the backend is working

echo "🧪 Testing Nail AR Backend..."
echo "=============================="
echo ""

# Check if backend is running
echo "1. Checking if backend is running on port 8000..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs | grep -q "200"; then
    echo "   ✅ Backend is running! (FastAPI docs available)"
else
    echo "   ❌ Backend is NOT running"
    echo ""
    echo "   Start it with:"
    echo "   cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    exit 1
fi

echo ""
echo "2. Checking segmentation endpoint..."
if curl -s http://localhost:8000/openapi.json | grep -q "api/nails/segment"; then
    echo "   ✅ Segmentation endpoint exists"
else
    echo "   ❌ Segmentation endpoint not found"
    exit 1
fi

echo ""
echo "3. Testing with a dummy image..."

# Create a small test image (1x1 pixel)
TEST_IMAGE="/tmp/test_nail.jpg"
convert -size 100x100 xc:white "$TEST_IMAGE" 2>/dev/null || {
    echo "   ⚠️  ImageMagick not installed, skipping image test"
    echo ""
    echo "✅ Backend is running and ready!"
    echo ""
    echo "Next steps:"
    echo "1. Open http://localhost:3000/app-realtime.html in your browser"
    echo "2. Click 'Start Camera'"
    echo "3. Click 'Segment Nails' or 'Start Real-Time'"
    exit 0
}

RESPONSE=$(curl -s -X POST http://localhost:8000/api/nails/segment \
    -F "file=@$TEST_IMAGE" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ API responding correctly!"
    echo ""
    echo "   Response preview:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null | head -20
else
    echo "   ❌ API returned error: HTTP $HTTP_CODE"
    echo ""
    echo "   Response:"
    echo "$BODY"
    exit 1
fi

rm -f "$TEST_IMAGE"

echo ""
echo "================================================"
echo "✅ All tests passed! Backend is ready!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Start frontend: cd frontend && python3 -m http.server 3000"
echo "2. Open http://localhost:3000/app-realtime.html"
echo "3. Click 'Start Camera' and then 'Segment Nails'"
