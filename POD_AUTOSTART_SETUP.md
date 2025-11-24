# Pod Autostart Setup Guide

This guide explains how to make your Nail AR application start automatically in your Docker/Kubernetes pod.

## Understanding the Environment

You're running in a **container/pod environment** (not a traditional Linux system), which means:
- ❌ No systemd available
- ❌ Traditional service management won't work
- ✅ Use Docker ENTRYPOINT or Kubernetes lifecycle hooks

## Solution Overview

### For Docker Containers

Your application will start automatically when the container starts using the `ENTRYPOINT` directive in the Dockerfile.

### Files Created

1. **[docker-entrypoint.sh](docker-entrypoint.sh)** - Container startup script
2. **[Dockerfile](Dockerfile)** - Updated with ENTRYPOINT
3. **This guide** - Documentation

## How It Works

### Container Lifecycle

```
Container Starts
    ↓
Docker runs ENTRYPOINT
    ↓
docker-entrypoint.sh executes
    ↓
Activates venv
    ↓
Runs start_app.sh
    ↓
Backend + Frontend start
    ↓
Application ready!
```

## Configuration Files

### 1. docker-entrypoint.sh

```bash
#!/bin/bash
set -e

# Activate virtual environment
source /workspace/nail-projects/venv/bin/activate

# Change to project directory
cd /workspace/nail-projects

# Start the application
exec ./start_app.sh
```

### 2. Dockerfile (Updated)

```dockerfile
# Copy entrypoint
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Set the entrypoint (runs on container start)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
```

## Usage

### Rebuild Docker Image

After making these changes:

```bash
# Build the image
docker build -t nail-ar:latest .

# Or if using docker-compose
docker-compose build
```

### Run Container

```bash
# Run with autostart
docker run -d \
  --name nail-ar \
  --gpus all \
  -p 8000:8000 \
  -p 3000:3000 \
  -v $(pwd):/workspace/nail-projects \
  nail-ar:latest
```

The application will start automatically!

### Check Logs

```bash
# View container logs
docker logs nail-ar

# Follow logs in real-time
docker logs -f nail-ar
```

## For Kubernetes Pods

If you're using Kubernetes, the same approach works:

### kubernetes-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nail-ar-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nail-ar
  template:
    metadata:
      labels:
        app: nail-ar
    spec:
      containers:
      - name: nail-ar
        image: your-registry/nail-ar:latest
        ports:
        - containerPort: 8000
          name: backend
        - containerPort: 3000
          name: frontend
        resources:
          limits:
            nvidia.com/gpu: 1  # Request 1 GPU
        volumeMounts:
        - name: model-storage
          mountPath: /workspace/nail-projects
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: nail-ar-pvc
```

### kubernetes-service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nail-ar-service
spec:
  type: LoadBalancer
  selector:
    app: nail-ar
  ports:
  - name: backend
    port: 8000
    targetPort: 8000
  - name: frontend
    port: 3000
    targetPort: 3000
```

### Deploy to Kubernetes

```bash
# Apply deployment
kubectl apply -f kubernetes-deployment.yaml

# Apply service
kubectl apply -f kubernetes-service.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/nail-ar-deployment
```

## Container Restart Policy

### Docker

```bash
# Run with auto-restart
docker run -d \
  --name nail-ar \
  --restart unless-stopped \  # Restart automatically
  --gpus all \
  -p 8000:8000 \
  -p 3000:3000 \
  nail-ar:latest
```

Restart policies:
- `no` - Don't restart (default)
- `on-failure` - Restart if exit code != 0
- `always` - Always restart
- `unless-stopped` - Restart unless manually stopped

### Kubernetes

In the deployment YAML:

```yaml
spec:
  template:
    spec:
      restartPolicy: Always  # Always restart on failure
      containers:
      - name: nail-ar
        # ... rest of config
```

## Troubleshooting

### Container doesn't start

1. Check logs:
   ```bash
   docker logs nail-ar
   ```

2. Verify entrypoint is executable:
   ```bash
   docker exec nail-ar ls -la /app/docker-entrypoint.sh
   # Should show: -rwxr-xr-x
   ```

3. Test entrypoint manually:
   ```bash
   docker exec -it nail-ar /bin/bash
   /app/docker-entrypoint.sh
   ```

### Application crashes

1. Check exit code:
   ```bash
   docker inspect nail-ar --format='{{.State.ExitCode}}'
   ```

2. View full logs:
   ```bash
   docker logs --tail 100 nail-ar
   ```

3. Check if model exists:
   ```bash
   docker exec nail-ar ls -la /workspace/nail-projects/checkpoint_best_total.pth
   ```

### Port already in use

```bash
# Find what's using the port
lsof -i :8000
netstat -tlnp | grep 8000

# Stop conflicting service
docker stop $(docker ps -q --filter "publish=8000")
```

## Health Checks

### Add Health Check to Dockerfile

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/docs || exit 1
```

### Kubernetes Liveness/Readiness Probes

```yaml
livenessProbe:
  httpGet:
    path: /docs
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /docs
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## Environment Variables

### Pass Environment Variables

```bash
# Docker
docker run -d \
  --name nail-ar \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e TF_ENABLE_ONEDNN_OPTS=0 \
  nail-ar:latest

# Kubernetes
env:
- name: CUDA_VISIBLE_DEVICES
  value: "0"
- name: TF_ENABLE_ONEDNN_OPTS
  value: "0"
```

## Monitoring

### Docker Stats

```bash
# Real-time stats
docker stats nail-ar

# One-time stats
docker stats --no-stream nail-ar
```

### Kubernetes Monitoring

```bash
# Pod resource usage
kubectl top pod -l app=nail-ar

# Detailed pod info
kubectl describe pod nail-ar-deployment-xxx

# Events
kubectl get events --sort-by='.lastTimestamp'
```

## Accessing the Application

### From Host Machine

```bash
# Backend API
curl http://localhost:8000/docs

# Frontend
curl http://localhost:3000/app-realtime.html
```

### From Inside Container

```bash
# Enter container
docker exec -it nail-ar /bin/bash

# Test locally
curl http://localhost:8000/docs
```

### From External Network

If using Kubernetes LoadBalancer:

```bash
# Get external IP
kubectl get service nail-ar-service

# Access
curl http://<EXTERNAL-IP>:8000/docs
```

## Complete Example

### 1. Build Image

```bash
docker build -t nail-ar:latest .
```

### 2. Run Container

```bash
docker run -d \
  --name nail-ar \
  --restart unless-stopped \
  --gpus all \
  -p 8000:8000 \
  -p 3000:3000 \
  -v $(pwd):/workspace/nail-projects \
  nail-ar:latest
```

### 3. Verify Running

```bash
# Check container status
docker ps | grep nail-ar

# View logs
docker logs -f nail-ar

# Test endpoints
curl http://localhost:8000/docs
curl http://localhost:8000/api/cache/stats
```

### 4. Access Application

- Frontend: http://localhost:3000/app-realtime.html
- Backend: http://localhost:8000/docs

## Summary

✅ **Docker ENTRYPOINT** - Application starts automatically with container
✅ **Restart Policy** - Auto-restart on failure
✅ **Health Checks** - Monitor application health
✅ **Logging** - All logs available via docker logs
✅ **Kubernetes Ready** - Works in pod environments

Your Nail AR application will now start automatically whenever the container/pod starts! 🚀

## Quick Reference

```bash
# Start container
docker run -d --name nail-ar --restart unless-stopped nail-ar:latest

# View logs
docker logs -f nail-ar

# Stop container
docker stop nail-ar

# Start existing container
docker start nail-ar

# Restart container
docker restart nail-ar

# Remove container
docker rm -f nail-ar
```
