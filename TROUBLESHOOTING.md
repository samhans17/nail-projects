# Troubleshooting Guide

## Backend Won't Start

### Check Backend Logs Manually
```bash
cd /workspace/nail-projects/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Common Issues:

**1. Model checkpoint not found**
```bash
# Check if model exists
ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth

# If missing, update path in backend/model_rf_deter.py line 9
```

**2. Missing dependencies**
```bash
source /workspace/nail-projects/venv/bin/activate
pip install rfdetr supervision opencv-python-headless
```

**3. Professional renderer import error**
```bash
# Test imports
cd /workspace/nail-projects/backend
python3 -c "from professional_nail_renderer import NailGeometryAnalyzer"
```

**4. Port already in use**
```bash
# Kill existing process
pkill -f "uvicorn main:app"
lsof -ti:8000 | xargs kill -9
```

## Frontend Won't Start

**Port 3000 already in use**
```bash
pkill -f "http.server 3000"
lsof -ti:3000 | xargs kill -9
```

## CORS Errors in Browser

CORS is already configured in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If still seeing CORS errors:
1. Clear browser cache
2. Check browser console for actual error
3. Verify backend is running: `curl http://localhost:8000/docs`

## GPU Not Being Used

**Check GPU availability**
```bash
nvidia-smi
```

**Test PyTorch CUDA**
```bash
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Force model to GPU** (in `backend/model_rf_deter.py`):
```python
model = model.cuda()
```

## Slow Performance

**Check GPU usage**
```bash
watch -n 0.5 nvidia-smi
```

**Reduce image quality** (in `frontend/app-realtime.js` line 315):
```javascript
const blob = await canvasToBlob(tempCanvas, "image/jpeg", 0.4);  // Lower quality
```

## Test Individual Components

**Test backend health**
```bash
curl http://localhost:8000/health
```

**Test segmentation**
```bash
curl -X POST http://localhost:8000/api/nails/segment \
  -F "file=@test.jpg"
```

**Test materials endpoint**
```bash
curl http://localhost:8000/api/materials
```

## View Backend Logs

**If using the script**
The logs will show in the terminal where you ran `./start_app.sh`

**Find backend process**
```bash
ps aux | grep uvicorn
```

**View specific logs**
```bash
tail -f /tmp/backend.log  # If you redirect logs
```

## Still Not Working?

Run each component manually to see errors:

**Terminal 1 - Backend:**
```bash
cd /workspace/nail-projects/backend
source /workspace/nail-projects/venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /workspace/nail-projects/frontend
python3 -m http.server 3000
```

This will show you the exact error messages!
