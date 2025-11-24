# ✅ RunPod Deployment - Final Configuration

## What Was Fixed

The frontend now **auto-detects** the correct backend URL:

- **localhost**: Uses `http://localhost:8000`
- **RunPod**: Uses `https://xxxxx-8000.proxy.runpod.net` (replaces 3000 with 8000)
- **Other**: Uses `hostname:8000`

## How to Run

```bash
cd /workspace/nail-projects
chmod +x start_app.sh
./start_app.sh
```

## RunPod Port Configuration

**Expose these ports in RunPod:**
- Port **3000** - Frontend
- Port **8000** - Backend API

## Access URLs

On RunPod, you'll get URLs like:

```
Frontend: https://xxxxx-3000.proxy.runpod.net/app-realtime.html
Backend:  https://xxxxx-8000.proxy.runpod.net/docs
```

The frontend **automatically** connects to the backend by changing `3000` to `8000` in the URL.

## Test Connection

Open this page first to verify everything works:

```
https://xxxxx-3000.proxy.runpod.net/test-connection.html
```

This will:
- ✅ Show detected URLs
- ✅ Test backend connectivity
- ✅ Test materials endpoint
- ✅ Verify CORS configuration

## How It Works

In `frontend/app-realtime.js`:

```javascript
function getApiBaseUrl() {
    const hostname = window.location.hostname;

    // Localhost
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }

    // RunPod (proxy.runpod.net)
    if (hostname.includes('proxy.runpod.net')) {
        // Replace -3000 with -8000
        return window.location.origin.replace('-3000.', '-8000.');
    }

    // Default
    return `${window.location.protocol}//${hostname}:8000`;
}
```

## Startup Process

The `start_app.sh` script:

1. ✅ Activates venv at `/workspace/nail-projects/venv/`
2. ✅ Starts backend on `0.0.0.0:8000`
3. ✅ Waits for backend health check (up to 60 seconds)
4. ✅ Starts frontend on `0.0.0.0:3000`
5. ✅ Verifies both are running

## CORS Configuration

Already configured in `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

No additional configuration needed!

## Troubleshooting

### Backend can't be reached

Check browser console:
```
🔧 API Configuration:
   Frontend: https://xxxxx-3000.proxy.runpod.net
   Backend: https://xxxxx-8000.proxy.runpod.net
```

If backend URL is wrong, verify:
- Port 8000 is exposed in RunPod
- Backend is actually running: `curl localhost:8000/docs`

### CORS errors

The backend allows all origins. If you still see CORS:
- Clear browser cache
- Check backend logs for actual errors
- Use test-connection.html to diagnose

### Backend crashes

Run manually to see errors:
```bash
cd /workspace/nail-projects/backend
source /workspace/nail-projects/venv/bin/activate
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Common issues:
- Model not found (check path in model_rf_deter.py)
- Missing dependencies (pip install rfdetr supervision)

## Expected Latency on RTX 4090

- WebGL Mode: ~50ms
- Professional Mode: ~300ms
- Model Inference: ~100ms

## Complete Checklist

- [ ] Project at `/workspace/nail-projects/`
- [ ] Venv at `/workspace/nail-projects/venv/`
- [ ] Model checkpoint exists and path is correct
- [ ] Dependencies installed in venv
- [ ] Ports 3000 and 8000 exposed in RunPod
- [ ] `chmod +x start_app.sh` executed
- [ ] Script runs without errors
- [ ] test-connection.html shows all green
- [ ] Main app works at app-realtime.html

## Ready to Deploy! 🚀

```bash
cd /workspace/nail-projects
./start_app.sh
```

Then open:
```
https://YOUR-POD-ID-3000.proxy.runpod.net/app-realtime.html
```

Done! 💅✨
