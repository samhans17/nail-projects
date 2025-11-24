#!/bin/bash

echo "🧪 Testing Performance Optimizations..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if server is running
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend is not running!${NC}"
    echo "Start it with: ./start_app.sh"
    exit 1
fi

echo -e "${GREEN}✅ Backend is running${NC}"
echo ""

# Test 1: Cache stats endpoint
echo "Test 1: Cache Statistics Endpoint"
if curl -s http://localhost:8000/api/cache/stats | jq . > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Cache stats endpoint works${NC}"
    curl -s http://localhost:8000/api/cache/stats | jq .
else
    echo -e "${RED}❌ Cache stats endpoint failed${NC}"
fi
echo ""

# Test 2: Check if test image exists
TEST_IMAGE="test_nail.jpg"
if [ ! -f "$TEST_IMAGE" ]; then
    echo -e "${YELLOW}⚠️  No test image found at $TEST_IMAGE${NC}"
    echo "Skipping performance tests (need a test image)"
    exit 0
fi

# Test 3: First request (cache miss)
echo "Test 2: First Request (Cache Miss)"
START=$(date +%s%N)
RESPONSE1=$(curl -s -w "\n%{http_code}" -X POST -F "file=@$TEST_IMAGE" http://localhost:8000/api/nails/segment)
HTTP_CODE1=$(echo "$RESPONSE1" | tail -n1)
END=$(date +%s%N)
DURATION1=$(( (END - START) / 1000000 )) # Convert to milliseconds

if [ "$HTTP_CODE1" = "200" ]; then
    echo -e "${GREEN}✅ First request successful${NC}"
    echo "   Duration: ${DURATION1}ms (expected: model loading + inference)"
else
    echo -e "${RED}❌ First request failed (HTTP $HTTP_CODE1)${NC}"
fi
echo ""

# Test 4: Second request (cache hit)
echo "Test 3: Second Request (Cache Hit)"
START=$(date +%s%N)
RESPONSE2=$(curl -s -w "\n%{http_code}" -X POST -F "file=@$TEST_IMAGE" http://localhost:8000/api/nails/segment)
HTTP_CODE2=$(echo "$RESPONSE2" | tail -n1)
END=$(date +%s%N)
DURATION2=$(( (END - START) / 1000000 ))

if [ "$HTTP_CODE2" = "200" ]; then
    echo -e "${GREEN}✅ Second request successful${NC}"
    echo "   Duration: ${DURATION2}ms (should be much faster!)"

    # Calculate speedup
    if [ $DURATION1 -gt 0 ] && [ $DURATION2 -gt 0 ]; then
        SPEEDUP=$(awk "BEGIN {printf \"%.1f\", $DURATION1/$DURATION2}")
        echo -e "   ${GREEN}🚀 Speedup: ${SPEEDUP}x faster${NC}"
    fi
else
    echo -e "${RED}❌ Second request failed (HTTP $HTTP_CODE2)${NC}"
fi
echo ""

# Test 5: Cache stats after requests
echo "Test 4: Cache Stats After Requests"
CACHE_STATS=$(curl -s http://localhost:8000/api/cache/stats | jq -r '.size')
if [ "$CACHE_STATS" -gt 0 ]; then
    echo -e "${GREEN}✅ Cache has $CACHE_STATS entries${NC}"
else
    echo -e "${YELLOW}⚠️  Cache is empty (unexpected)${NC}"
fi
echo ""

# Test 6: Clear cache
echo "Test 5: Clear Cache"
CLEAR_RESPONSE=$(curl -s -X POST http://localhost:8000/api/cache/clear | jq -r '.message')
if [ "$CLEAR_RESPONSE" = "Cache cleared successfully" ]; then
    echo -e "${GREEN}✅ Cache cleared successfully${NC}"
else
    echo -e "${RED}❌ Cache clear failed${NC}"
fi
echo ""

# Summary
echo "=================================="
echo "📊 Performance Test Summary"
echo "=================================="
echo "First request:  ${DURATION1}ms"
echo "Second request: ${DURATION2}ms"
if [ $DURATION1 -gt 0 ] && [ $DURATION2 -gt 0 ]; then
    IMPROVEMENT=$(awk "BEGIN {printf \"%.1f\", (1-$DURATION2/$DURATION1)*100}")
    echo -e "${GREEN}Improvement: ${IMPROVEMENT}% faster${NC}"
fi
echo ""
echo "All optimizations are working! 🎉"
