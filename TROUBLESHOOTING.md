# 🔧 Troubleshooting Guide

## Quick Diagnostics

Run this to test if backend is working:
```bash
cd /home/usama-naveed/nail-project
./TEST_BACKEND.sh
```

---

## Problem: "Segment Nails" Button Does Nothing

### Step 1: Check Browser Console

1. Open the app: `http://localhost:3000/app-realtime.html`
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Click "Segment Nails"
5. Look for error messages

### What to Look For:

**If you see:** `❌ Segmentation error: Failed to fetch`
→ **Backend is not running**

**Solution:**
```bash
cd /home/usama-naveed/nail-project/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

**If you see:** `❌ API error 500: ...`
→ **Backend crashed or model error**

**Solution:**
1. Check the backend terminal for Python errors
2. Make sure RF-DETR model exists at:
   `/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth`
3. Check if required packages are installed:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

---

**If you see:** `❌ API error 422: ...`
→ **Invalid request format**

**Solution:**
- This is a bug in the frontend
- Check that `blob` is being created correctly
- Look for console log: `Blob size: XXX KB`

---

**If you see:** Network error or CORS error
→ **CORS or connectivity issue**

**Solution:**
1. Make sure backend is running on port 8000
2. Check CORS is enabled in `backend/main.py`
3. Try accessing API directly:
   ```bash
   curl http://localhost:8000/docs
   ```

---

## Problem: "Start Real-Time Processing" Does Nothing

### Checklist:

1. **Is camera started?**
   - You must click "Start Camera" first
   - Video should be visible

2. **Did segmentation work once?**
   - Try "Segment Nails" button first
   - Make sure it detects nails

3. **Check console for errors:**
   - Press F12 → Console
   - Look for repeating errors

### Common Issues:

**Rapid API errors**
→ Backend can't keep up

**Solution:**
- Increase "Processing Interval" to 1000ms or higher
- Check backend is using GPU (not CPU)

---

## Problem: Camera Won't Start

### Issue: Button click does nothing

**Cause:** You're not using `localhost`

**Solution:**
Must use: `http://localhost:3000/app-realtime.html`
NOT: `http://0.0.0.0:3000/` or `http://192.168.x.x:3000/`

### Issue: "getUserMedia not available"

**Cause:** Browser security

**Solution:**
1. Use HTTPS or localhost
2. Update browser to latest version
3. Enable camera permissions in browser settings

### Issue: Permission denied

**Cause:** Camera blocked

**Solution:**
1. Click the camera icon in address bar
2. Allow camera access
3. Reload page

---

## Problem: Low FPS (< 30)

### Check Stats Panel:

**If "Render Time" > 30ms:**
→ GPU is slow

**Solution:**
1. Reduce metallic to 0%
2. Lower camera resolution
3. Close other GPU-heavy apps
4. Enable hardware acceleration in browser

**If "API Latency" > 1000ms:**
→ Backend is slow

**Solution:**
1. Check if backend is using GPU:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   ```
2. Increase processing interval to 1000ms+
3. Use smaller images (lower camera resolution)

---

## Problem: No Nails Detected

### Checklist:

1. **Good lighting?**
   - Needs bright, even lighting
   - Avoid shadows

2. **Hand position?**
   - Show palm to camera
   - Nails should be visible
   - Not too far away

3. **Model loaded?**
   - Check backend terminal for:
     `RF-DETR model loaded and optimized for inference.`

4. **Check API response:**
   - Look in console for:
     `✅ Segmentation result: {nails: []}`
   - If `nails` array is empty, model didn't detect anything

### Solutions:

1. **Improve lighting:**
   - Use natural light or bright room
   - Avoid direct shadows on hand

2. **Better hand position:**
   - Closer to camera
   - Show palm clearly
   - Keep hand steady

3. **Check model:**
   - Verify checkpoint file exists
   - Check backend logs for errors

---

## Problem: Backend Won't Start

### Error: `ModuleNotFoundError: No module named 'rfdetr'`

**Solution:**
```bash
pip install rfdetr supervision torch torchvision opencv-python
```

### Error: `FileNotFoundError: checkpoint_best_total.pth`

**Solution:**
Update the path in `backend/model_rf_deter.py`:
```python
model = RFDETRSegPreview(pretrain_weights="YOUR_ACTUAL_PATH_HERE")
```

### Error: `CUDA out of memory`

**Solution:**
1. Use CPU instead (edit model_rf_deter.py)
2. Reduce image size
3. Close other GPU applications

---

## Problem: WebGL Not Working

### Error: "WebGL 2 not supported"

**Solution:**
1. Update browser to latest version
2. Try Chrome/Firefox (best WebGL support)
3. Enable hardware acceleration:
   - Chrome: `chrome://settings/` → Advanced → System
   - Firefox: `about:preferences` → Performance

### Error: Blank canvas

**Solution:**
1. Check browser console for WebGL errors
2. Try the non-WebGL version: `http://localhost:3000/`
3. Check GPU drivers are up to date

---

## Debugging Commands

### Check if backend is running:
```bash
curl http://localhost:8000/docs
```

### Check if frontend is serving:
```bash
curl http://localhost:3000/app-realtime.html
```

### Test segmentation API:
```bash
# Create test image
convert -size 640x480 xc:white test.jpg

# Test endpoint
curl -X POST http://localhost:8000/api/nails/segment \
  -F "file=@test.jpg"
```

### Check Python packages:
```bash
cd backend
pip list | grep -E "(fastapi|uvicorn|torch|rfdetr)"
```

### Check GPU availability:
```bash
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

---

## Browser Console Checklist

When debugging, look for these console messages:

### ✅ Good Messages:
```
app-realtime.js loaded successfully
✓ Camera started
📸 Capturing frame for segmentation...
Frame size: 1280×720
Blob size: 45.3KB
🌐 Sending to API: http://localhost:8000/api/nails/segment
📡 Response status: 200 (456ms)
✅ Segmentation result: {width: 1280, height: 720, nails: Array(10)}
```

### ❌ Bad Messages (and solutions):
```
❌ Segmentation error: Failed to fetch
→ Backend not running

❌ API error 500: Internal Server Error
→ Check backend terminal for Python errors

❌ getUserMedia not available
→ Use http://localhost:3000 (not IP address)

❌ WebGL 2 not supported
→ Update browser or enable hardware acceleration
```

---

## Still Not Working?

### Collect Debug Info:

1. **Browser console output** (F12 → Console → copy all)
2. **Backend terminal output** (copy last 50 lines)
3. **Browser version** (`chrome://version` or `about:support`)
4. **Python version** (`python3 --version`)
5. **CUDA available?** (`python3 -c "import torch; print(torch.cuda.is_available())"`)

### Try Basic Version:

If real-time version doesn't work, try the simpler version:
```
http://localhost:3000/
```

This uses 2D Canvas (no WebGL) and might work better for debugging.

---

## Common Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Camera won't start | Use `localhost:3000` not IP address |
| Segment does nothing | Start backend with `uvicorn main:app` |
| No nails detected | Better lighting, show palm |
| Low FPS | Increase processing interval, disable metallic |
| Backend error | Check model path, install packages |
| WebGL error | Update browser, enable acceleration |

---

## Need Help?

1. Run `./TEST_BACKEND.sh` to verify backend
2. Check browser console (F12)
3. Check backend terminal for errors
4. Review this troubleshooting guide
5. Try the basic version first
