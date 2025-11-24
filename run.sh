#!/bin/bash
# Quick launcher for Nail AR system

echo "🚀 Starting Nail AR System"
echo "=========================="
echo ""

# Check if in correct directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Must run from nail-project directory"
    echo "   cd /home/usama-naveed/nail-project"
    exit 1
fi

echo "📋 What would you like to do?"
echo ""
echo "1) Start BOTH backend and frontend (recommended)"
echo "2) Start backend only"
echo "3) Start frontend only"
echo "4) Test backend"
echo "5) Exit"
echo ""
read -p "Choose (1-5): " choice

case $choice in
    1)
        echo ""
        echo "🟢 Starting backend in background..."
        cd backend
        uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
        BACKEND_PID=$!
        cd ..
        echo "   Backend PID: $BACKEND_PID"
        echo "   Logs: backend.log"
        sleep 3

        echo ""
        echo "🟢 Starting frontend in background..."
        cd frontend
        python3 -m http.server 3000 > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
        cd ..
        echo "   Frontend PID: $FRONTEND_PID"
        echo "   Logs: frontend.log"
        sleep 2

        echo ""
        echo "✅ Both services started!"
        echo ""
        echo "📝 Save these PIDs to stop later:"
        echo "   Backend:  $BACKEND_PID"
        echo "   Frontend: $FRONTEND_PID"
        echo ""
        echo "🌐 Open in browser:"
        echo ""
        echo "   Main Page (Choose version):"
        echo "   → http://localhost:3000/"
        echo ""
        echo "   Or go directly to optimized version:"
        echo "   → http://localhost:3000/app-realtime-optimized.html"
        echo ""
        echo "🛑 To stop:"
        echo "   kill $BACKEND_PID $FRONTEND_PID"
        echo ""
        ;;

    2)
        echo ""
        echo "🟢 Starting backend..."
        cd backend
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ;;

    3)
        echo ""
        echo "🟢 Starting frontend..."
        cd frontend
        python3 -m http.server 3000
        ;;

    4)
        echo ""
        if [ -f "TEST_BACKEND.sh" ]; then
            ./TEST_BACKEND.sh
        else
            echo "❌ TEST_BACKEND.sh not found"
        fi
        ;;

    5)
        echo "👋 Goodbye!"
        exit 0
        ;;

    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
