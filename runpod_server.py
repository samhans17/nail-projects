#!/usr/bin/env python3
"""
RunPod Unified Server
Serves both FastAPI backend and static frontend on port 8000
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.main import app as backend_app

# Create main app
app = FastAPI(title="Nail AR - RunPod Deployment")

# Mount the backend API under /api prefix
app.mount("/api", backend_app)

# Mount frontend static files
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

    @app.get("/")
    async def serve_frontend():
        """Serve the main frontend HTML"""
        index_file = frontend_path / "app-realtime.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Nail AR API is running! Visit /docs for API documentation."}
else:
    @app.get("/")
    async def root():
        return {"message": "Nail AR API is running on RunPod! Visit /docs for API documentation."}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nail-ar-runpod",
        "backend": "running",
        "frontend": "available" if frontend_path.exists() else "not_found"
    }

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    print("=" * 60)
    print("🚀 Nail AR Application - RunPod Deployment")
    print("=" * 60)
    print(f"📡 Backend API:  http://{host}:{port}/api")
    print(f"🌐 Frontend:     http://{host}:{port}/")
    print(f"📚 API Docs:     http://{host}:{port}/docs")
    print(f"❤️  Health:      http://{host}:{port}/health")
    print("=" * 60)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
