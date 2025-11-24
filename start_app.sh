#!/bin/bash

echo "🚀 Starting Nail AR Application..."
echo ""

# Activate venv
# Priority: VENV_PATH > ./venv > /workspace/nail-projects/venv
if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo "✅ Venv activated: $VENV_PATH"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Venv activated: ./venv"
elif [ -f "/workspace/nail-projects/venv/bin/activate" ]; then
    source /workspace/nail-projects/venv/bin/activate
    echo "✅ Venv activated: /workspace/nail-projects/venv"
else
    echo "⚠️  No venv found, using system python"
fi

echo ""
echo "🔧 Starting backend on port 8000..."

# Start backend
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
MAX_WAIT=60
COUNTER=0

while [ $COUNTER -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi

    # Check if backend process is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend failed to start! Check logs above."
        exit 1
    fi

    sleep 1
    COUNTER=$((COUNTER + 1))

    if [ $((COUNTER % 5)) -eq 0 ]; then
        echo "   Still waiting... ($COUNTER seconds)"
    fi
done

if [ $COUNTER -eq $MAX_WAIT ]; then
    echo "❌ Backend timeout after $MAX_WAIT seconds"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🌐 Starting frontend on port 3000..."

# Start frontend
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

sleep 2

# Check if frontend started
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "❌ Frontend failed to start!"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=================================="
echo "✅ Application is running!"
echo "=================================="
echo ""
echo "Frontend: http://localhost:3000/app-realtime.html"
echo "Backend:  http://localhost:8000/docs"
echo ""
echo "CORS is enabled for all origins"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

wait
