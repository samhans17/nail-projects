# RunPod Deployment - Nail AR Application with RF-DETR
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt /app/backend/requirements.txt
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Install additional dependencies for RF-DETR and professional rendering
RUN pip install --no-cache-dir \
    torch torchvision \
    supervision \
    scipy \
    scikit-image

# Copy the entire project
COPY . /app/

# Create directory for model checkpoint
RUN mkdir -p /app/models

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/models/checkpoint_best_total.pth
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port 8000 (RunPod will map this)
EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Nail AR Application on RunPod..."\n\
echo ""\n\
echo "📦 Checking model checkpoint..."\n\
if [ ! -f "$MODEL_PATH" ]; then\n\
    echo "⚠️  Model checkpoint not found at $MODEL_PATH"\n\
    echo "Please upload checkpoint_best_total.pth to /app/models/"\n\
    exit 1\n\
fi\n\
echo "✅ Model checkpoint found!"\n\
echo ""\n\
echo "🌐 Starting FastAPI backend + Frontend on port 8000..."\n\
cd /app\n\
exec python3 runpod_server.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Copy docker entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]
