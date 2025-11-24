# Quick Command Reference

## 🚀 Start Application Locally

### Single Command (Recommended)
```bash
cd /home/usama-naveed/nail-project
./start_app.sh
```

### Manual Start
```bash
# Terminal 1 - Backend
cd /home/usama-naveed/nail-project/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd /home/usama-naveed/nail-project/frontend
python3 -m http.server 3000
```

**Access:**
- Frontend: http://localhost:3000/app-realtime.html
- API Docs: http://localhost:8000/docs
- Backend: http://localhost:8000

---

## 🐳 Docker Commands

### Build Image
```bash
cd /home/usama-naveed/nail-project
docker build -t nail-ar:latest .
```

### Run Locally with Docker
```bash
docker run -it --rm \
  --gpus all \
  -p 8000:8000 \
  -v /home/usama-naveed/nail_AR-rfdeter/output:/app/models \
  nail-ar:latest
```

### Push to Docker Hub
```bash
docker tag nail-ar:latest YOUR_USERNAME/nail-ar:latest
docker login
docker push YOUR_USERNAME/nail-ar:latest
```

---

## 🧪 Testing Commands

### Test Backend API
```bash
# Health check
curl http://localhost:8000/health

# Segmentation
curl -X POST http://localhost:8000/api/nails/segment \
  -F "file=@result.jpg" \
  | jq .

# Professional rendering
curl -X POST http://localhost:8000/api/nails/render-professional \
  -F "file=@result.jpg" \
  -F "material=metallic_gold" \
  --output rendered.jpg

# Materials list
curl http://localhost:8000/api/materials | jq .
```

### Monitor GPU
```bash
# Real-time monitoring
watch -n 0.5 nvidia-smi

# Detailed view
nvtop

# Check if process is using GPU
nvidia-smi | grep python
```

---

## 📦 Deployment

### Create Deployment Package
```bash
cd /home/usama-naveed/nail-project
tar -czf nail-ar-app.tar.gz \
  backend/ \
  frontend/ \
  professional_nail_renderer/ \
  requirements.txt \
  start_app.sh \
  --exclude="*.pyc" \
  --exclude="__pycache__"
```

### Upload to RunPod
1. Build Docker image
2. Push to Docker Hub
3. Deploy on RunPod with GPU
4. Mount model checkpoint
5. Expose port 8000

---

## 🛑 Stop Application

### If using start_app.sh
```bash
# Press Ctrl+C in the terminal
```

### Manual Stop
```bash
# Find processes
ps aux | grep uvicorn
ps aux | grep http.server

# Kill by PID
kill <PID>

# Or kill all
pkill -f uvicorn
pkill -f http.server
```

---

## 🔍 Debugging

### Check Backend Logs
```bash
# If running manually
# Check terminal output

# If using systemd
journalctl -u nail-ar-backend -f
```

### Check if Ports are in Use
```bash
# Check port 8000
lsof -i :8000

# Check port 3000
lsof -i :3000

# Kill process on port
kill -9 $(lsof -t -i:8000)
```

### Test Model Loading
```bash
cd /home/usama-naveed/nail-project/backend
python3 -c "from model_rf_deter import model; print('Model loaded:', model)"
```

---

## 🎯 Performance Tuning

### Adjust Backend Workers
```bash
# Single worker (development)
uvicorn main:app --host 0.0.0.0 --port 8000

# Multiple workers (production)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Monitor Memory Usage
```bash
# Overall system
htop

# Specific process
ps aux | grep python | awk '{print $2, $4, $11}'
```

### Clear Cache
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clear pip cache
pip cache purge
```

---

## 📊 Benchmarking

### API Latency Test
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 http://localhost:8000/health
```

### Measure Inference Time
```python
import time
from PIL import Image

img = Image.open("test.jpg")
start = time.time()
result = model.predict(img)
print(f"Inference time: {(time.time() - start)*1000:.1f}ms")
```

---

## 🔄 Update Application

### Pull Latest Changes
```bash
cd /home/usama-naveed/nail-project
git pull  # If using git

# Restart application
./start_app.sh
```

### Update Dependencies
```bash
pip install -r requirements.txt --upgrade
pip install -r backend/requirements.txt --upgrade
```

---

## ✅ Health Checks

### Quick System Check
```bash
# Check GPU
nvidia-smi

# Check Python
python3 --version

# Check dependencies
pip list | grep -E "torch|fastapi|uvicorn|opencv"

# Check disk space
df -h

# Check model file
ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth
```

### Automated Health Check
```bash
#!/bin/bash
echo "🔍 System Health Check"
echo "====================="
echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv
echo ""
echo "Backend Status:"
curl -s http://localhost:8000/health | jq .
echo ""
echo "Model File:"
ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth
```

---

**Pro Tip:** Bookmark this file for quick command reference! 📌
