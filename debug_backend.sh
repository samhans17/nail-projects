#!/bin/bash

echo "🔍 Backend Diagnostic Script"
echo "=============================="
echo ""

# Activate venv
if [ -f "/workspace/nail-projects/venv/bin/activate" ]; then
    source /workspace/nail-projects/venv/bin/activate
    echo "✅ Venv activated"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Venv activated"
else
    echo "⚠️  No venv found"
fi

echo ""
echo "1️⃣ Checking Python and packages..."
echo "Python: $(which python3)"
python3 --version

echo ""
echo "2️⃣ Checking required packages..."
python3 -c "import fastapi; print('✅ fastapi:', fastapi.__version__)" 2>&1
python3 -c "import uvicorn; print('✅ uvicorn:', uvicorn.__version__)" 2>&1
python3 -c "import torch; print('✅ torch:', torch.__version__)" 2>&1
python3 -c "import cv2; print('✅ opencv:', cv2.__version__)" 2>&1

echo ""
echo "3️⃣ Checking rfdetr..."
python3 -c "from rfdetr import RFDETRSegPreview; print('✅ rfdetr installed')" 2>&1

echo ""
echo "4️⃣ Checking supervision..."
python3 -c "import supervision; print('✅ supervision:', supervision.__version__)" 2>&1

echo ""
echo "5️⃣ Checking model file..."
if [ -f "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth" ]; then
    ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth
    echo "✅ Model file exists"
else
    echo "❌ Model file NOT FOUND at /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
fi

echo ""
echo "6️⃣ Checking professional renderer..."
cd backend 2>/dev/null || cd /workspace/nail-projects/backend
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('..').resolve() / 'professional_nail_renderer'))
try:
    from professional_nail_renderer import NailGeometryAnalyzer, PhotoRealisticNailRenderer
    print('✅ Professional renderer imports OK')
except Exception as e:
    print(f'❌ Professional renderer error: {e}')
" 2>&1

echo ""
echo "7️⃣ Testing model load..."
python3 -c "
try:
    from model_rf_deter import model
    print('✅ Model loaded successfully')
except Exception as e:
    print(f'❌ Model load failed: {e}')
    import traceback
    traceback.print_exc()
" 2>&1

echo ""
echo "8️⃣ Checking ports..."
if command -v lsof &> /dev/null; then
    echo "Port 8000:"
    lsof -i :8000 2>&1 || echo "   Not in use"
    echo "Port 3000:"
    lsof -i :3000 2>&1 || echo "   Not in use"
else
    echo "lsof not available"
fi

echo ""
echo "=============================="
echo "Diagnostic complete!"
echo ""
echo "To start backend manually with full logs:"
echo "  cd /workspace/nail-projects/backend"
echo "  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug"
