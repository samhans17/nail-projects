#!/bin/bash
set -e

echo "🚀 Starting Nail AR Application in Pod..."
echo ""

# Activate virtual environment
if [ -f "/workspace/nail-projects/venv/bin/activate" ]; then
    source /workspace/nail-projects/venv/bin/activate
    echo "✅ Venv activated: /workspace/nail-projects/venv"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Venv activated: ./venv"
else
    echo "⚠️  No venv found, using system python"
fi

echo ""

# Change to project directory
cd /workspace/nail-projects

# Execute the startup script
exec ./start_app.sh
