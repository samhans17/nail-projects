# RunPod Deployment Guide - Nail AR Application

Complete guide for deploying the Nail AR application on RunPod.io with RTX 4090 24GB GPU.

---

## 🚀 Quick Start (Local Testing)

### Option 1: Single Command Startup
```bash
cd /home/usama-naveed/nail-project
./start_app.sh
```

This will start:
- **Backend (FastAPI):** http://localhost:8000
- **Frontend:** http://localhost:3000/app-realtime.html

Press `Ctrl+C` to stop both servers.

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
cd /home/usama-naveed/nail-project/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/usama-naveed/nail-project/frontend
python3 -m http.server 3000
```

Then open: http://localhost:3000/app-realtime.html

---

## 📦 RunPod Deployment

### Prerequisites

1. **RunPod Account**: Sign up at https://runpod.io
2. **Model Checkpoint**: `checkpoint_best_total.pth` (~390MB)
3. **GPU**: RTX 4090 24GB (recommended for best latency)

### Step 1: Prepare Your Code

```bash
cd /home/usama-naveed/nail-project

# Create deployment package
tar -czf nail-ar-app.tar.gz \
    backend/ \
    frontend/ \
    professional_nail_renderer/ \
    requirements.txt \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude=".git"

# You'll also need to upload checkpoint_best_total.pth separately
```

### Step 2: Create RunPod Dockerfile

Create this file in your project root:

```dockerfile
# Dockerfile for RunPod
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install additional packages
RUN pip install --no-cache-dir \
    rfdetr==1.3.0 \
    supervision==0.27.0 \
    opencv-python-headless==4.10.0.84

# Copy application code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY professional_nail_renderer/ /app/professional_nail_renderer/

# Environment variables
ENV MODEL_PATH=/app/models/checkpoint_best_total.pth
ENV PYTHONPATH=/app
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start script
CMD ["bash", "-c", "cd /app/backend && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000"]
```

### Step 3: Build Docker Image

```bash
# Build the image
docker build -t nail-ar-runpod:latest .

# Test locally (optional)
docker run -it --rm \
    --gpus all \
    -p 8000:8000 \
    -v /home/usama-naveed/nail_AR-rfdeter/output:/app/models \
    nail-ar-runpod:latest
```

### Step 4: Push to Docker Hub

```bash
# Tag for Docker Hub
docker tag nail-ar-runpod:latest YOUR_DOCKERHUB_USERNAME/nail-ar-runpod:latest

# Login to Docker Hub
docker login

# Push
docker push YOUR_DOCKERHUB_USERNAME/nail-ar-runpod:latest
```

### Step 5: Deploy on RunPod

1. **Go to RunPod.io** → Pods → Deploy
2. **Select GPU**: RTX 4090 (24GB VRAM)
3. **Container Image**: `YOUR_DOCKERHUB_USERNAME/nail-ar-runpod:latest`
4. **Container Disk**: 20GB minimum
5. **Expose HTTP Ports**: `8000`
6. **Volume Mounts**:
   - Upload `checkpoint_best_total.pth` to network storage
   - Mount as: `/app/models`

7. **Environment Variables**:
   ```
   MODEL_PATH=/app/models/checkpoint_best_total.pth
   PORT=8000
   ```

8. **Click Deploy**

### Step 6: Access Your Application

Once deployed, RunPod will give you a URL like:
```
https://xxxxx-8000.proxy.runpod.net
```

Access your app at:
- **Frontend**: `https://xxxxx-8000.proxy.runpod.net/` (needs modification)
- **API**: `https://xxxxx-8000.proxy.runpod.net/api/nails/segment`
- **Docs**: `https://xxxxx-8000.proxy.runpod.net/docs`

---

## 🎯 Latency Optimizations for RTX 4090

### Backend Optimizations

**1. Update `backend/main.py`:**
```python
# Add at top of file
import torch
torch.backends.cudnn.benchmark = True  # Auto-tune for best performance
torch.set_float32_matmul_precision('high')  # Use TF32 on 4090
```

**2. Model Optimization:**
```python
# In model_rf_deter.py
model = RFDETRSegPreview(pretrain_weights=MODEL_PATH)
model.optimize_for_inference()

# Add these for 4090
model.eval()
torch.set_grad_enabled(False)

# Compile model (PyTorch 2.0+)
if hasattr(torch, 'compile'):
    model = torch.compile(model, mode='max-autotune')
```

**3. Batch Processing:**
For multiple nails, process in batch:
```python
# Instead of one-by-one processing
detections = model.predict_batch(images, threshold=0.2)
```

### Expected Latencies on RTX 4090

| Operation | Latency | Notes |
|-----------|---------|-------|
| Model Inference | 80-120ms | RF-DETR on 432×432 input |
| Professional Render (5 nails) | 150-200ms | CPU rendering |
| WebGL Mode | 30-50ms | GPU-accelerated |
| Total API Call | 250-350ms | End-to-end |

### Frontend Optimizations

**1. Reduce Image Upload Size:**
```javascript
// In app-realtime.js
const blob = await canvasToBlob(tempCanvas, "image/jpeg", 0.5);  // Lower quality
```

**2. Adjust Processing Interval:**
```javascript
// Set to 500ms for real-time on 4090
processingIntervalEl.value = 500;
```

**3. Use WebGL Mode for Real-Time:**
- Professional mode: Best quality, ~300ms latency
- WebGL mode: Real-time rendering, ~50ms latency

---

## 🧪 Testing Commands

### Test Backend API
```bash
# Health check
curl http://localhost:8000/health

# Test segmentation
curl -X POST http://localhost:8000/api/nails/segment \
  -F "file=@test_image.jpg"

# Test professional rendering
curl -X POST http://localhost:8000/api/nails/render-professional \
  -F "file=@test_image.jpg" \
  -F "material=metallic_gold" \
  --output result.jpg

# Get materials list
curl http://localhost:8000/api/materials
```

### Monitor GPU Usage
```bash
# Watch GPU usage in real-time
watch -n 0.5 nvidia-smi

# More detailed monitoring
nvtop
```

### Benchmark Latency
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Benchmark API
ab -n 100 -c 10 -p test_image.jpg -T "multipart/form-data" \
  http://localhost:8000/api/nails/segment
```

---

## 📊 RunPod Configuration Recommendations

### For Best Latency (RTX 4090)

| Setting | Value | Reason |
|---------|-------|--------|
| GPU | RTX 4090 24GB | Best price/performance |
| vCPU | 8-16 cores | Professional rendering uses CPU |
| RAM | 32GB | Model + rendering buffers |
| Container Disk | 20GB | Code + dependencies |
| Volume Storage | 2GB | Model checkpoint only |
| Region | Closest to users | Minimize network latency |

### Cost Optimization

- **On-Demand**: $0.69/hour (RTX 4090)
- **Spot Instance**: ~$0.35/hour (50% savings, may be interrupted)

For production: Use On-Demand
For development: Use Spot to save costs

---

## 🔧 Troubleshooting

### Backend Won't Start

**Problem**: Model checkpoint not found
```bash
# Check if checkpoint exists
ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth

# Update path in backend/model_rf_deter.py if needed
```

**Problem**: CUDA out of memory
```python
# Reduce batch size or image resolution
# In model_rf_deter.py, resize input:
image = image.resize((432, 432))
```

### Frontend Can't Connect

**Problem**: CORS errors
```python
# In backend/main.py, make sure CORS allows your frontend:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify RunPod domain
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Problem**: Wrong API URL
```javascript
// Check frontend/app-realtime.js
// Update API_URL to your RunPod URL:
const API_URL = "https://xxxxx-8000.proxy.runpod.net/api/nails/segment";
```

### Slow Performance

**Check GPU Usage:**
```bash
nvidia-smi
# Should show Python process using 4090
```

**Check if model is on GPU:**
```python
# Add to model_rf_deter.py
print(f"Model device: {next(model.parameters()).device}")
# Should print: cuda:0
```

---

## 📝 File Structure

```
nail-project/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── model_rf_deter.py    # RF-DETR model loader
│   ├── schemas.py           # Pydantic schemas
│   ├── utils.py             # Helper functions
│   └── requirements.txt     # Backend dependencies
├── frontend/
│   ├── app-realtime.html    # Main UI
│   ├── app-realtime.js      # Application logic
│   ├── webgl-nails.js       # WebGL renderer
│   └── config.js            # API configuration
├── professional_nail_renderer/
│   ├── nail_geometry.py     # Geometry extraction
│   ├── nail_material.py     # Material presets
│   └── photo_realistic_renderer.py  # Rendering engine
├── start_app.sh             # Startup script
├── requirements.txt         # Project dependencies
└── Dockerfile              # RunPod container image
```

---

## ✅ Success Checklist

- [ ] Backend starts without errors on port 8000
- [ ] Frontend accessible on port 3000
- [ ] Model checkpoint loads successfully
- [ ] GPU shows CUDA device in nvidia-smi
- [ ] API responds to /health endpoint
- [ ] Segmentation returns nail polygons
- [ ] Professional rendering produces images
- [ ] WebGL mode works in browser
- [ ] Latency under 350ms for professional mode
- [ ] Latency under 50ms for WebGL mode

---

## 🆘 Support

If you encounter issues:

1. Check logs: `journalctl -u your-service -f`
2. Test API directly: `curl http://localhost:8000/docs`
3. Monitor GPU: `nvidia-smi -l 1`
4. Check VRAM usage: Should be ~4-6GB for RF-DETR

---

**Ready to deploy!** 🚀

For local testing: `./start_app.sh`
For RunPod: Follow deployment steps above
