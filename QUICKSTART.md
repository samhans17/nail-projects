# Quick Start Guide

## 🚀 Run the Application

### Method 1: Using Startup Script (Recommended)

```bash
cd /home/usama-naveed/nail-project

# Option A: Activate venv and run
source /path/to/your/venv/bin/activate
./start_app.sh

# Option B: Set VENV_PATH environment variable
export VENV_PATH=/path/to/your/venv
./start_app.sh

# Option C: Auto-detect (if venv is in project directory)
./start_app.sh
```

### Method 2: Manual Start with Virtual Environment

```bash
cd /home/usama-naveed/nail-project

# Activate your virtual environment
source /path/to/your/venv/bin/activate

# Terminal 1 - Backend
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend (new terminal)
cd frontend
python3 -m http.server 3000
```

## 🌐 Access the Application

Once running:
- **Frontend**: http://localhost:3000/app-realtime.html
- **API Docs**: http://localhost:8000/docs
- **Backend API**: http://localhost:8000

## 🐳 For RunPod Deployment

If deploying to RunPod with virtual environment:

```bash
# In your RunPod container, activate venv first
source /workspace/venv/bin/activate

# Then start the application
cd /workspace/nail-project
./start_app.sh
```

Or set it in your Dockerfile:
```dockerfile
ENV VENV_PATH=/workspace/venv
CMD ["/bin/bash", "-c", "source $VENV_PATH/bin/activate && cd /workspace/nail-project && ./start_app.sh"]
```

## 🛑 Stop the Application

Press `Ctrl+C` in the terminal where you ran `./start_app.sh`

## ✅ Verify Everything Works

1. Open http://localhost:3000/app-realtime.html
2. Click "Start Camera"
3. Select rendering mode (WebGL or Professional)
4. Click "Segment Nails"
5. See the magic! ✨

## 🔧 Troubleshooting

**Virtual environment not found?**
```bash
# Create one
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

**Port already in use?**
```bash
# Kill existing processes
pkill -f uvicorn
pkill -f "http.server"

# Or use different ports
# Edit start_app.sh and change port numbers
```

**Model not found?**
```bash
# Check if checkpoint exists
ls -lh /home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth

# If not, update MODEL_PATH in backend/model_rf_deter.py
```

---

For more details, see:
- **[COMMANDS.md](COMMANDS.md)** - All available commands
- **[RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md)** - Full deployment guide
