# Inference Latency Optimization Guide

Current: **180-200ms** → Target: **< 100ms**

---

## Quick Start - Use Optimized Script

```bash
# Fastest settings (should get ~80-120ms)
python live_inference_optimized.py --input-size 320

# Even faster (skip every other frame)
python live_inference_optimized.py --input-size 320 --skip-frames 2

# Maximum speed (may sacrifice some accuracy)
python live_inference_optimized.py --input-size 224 --skip-frames 2
```

---

## Optimization Techniques Applied

### 1. **Reduce Input Resolution** ⚡ (Biggest Impact)
```bash
# 432×432 → 320×320 = ~2x faster
python live_inference_optimized.py --input-size 320

# 432×432 → 224×224 = ~3-4x faster
python live_inference_optimized.py --input-size 224
```

**Impact:** 432² = 186,624 pixels → 320² = 102,400 pixels = **45% fewer pixels**

### 2. **Frame Skipping** ⚡
Process every 2nd or 3rd frame, reuse previous result:
```bash
# Process every 2nd frame (2x effective FPS)
python live_inference_optimized.py --skip-frames 2
```

### 3. **Fast Interpolation**
- Preprocessing: `cv2.INTER_AREA` (fastest for downscaling)
- Mask resizing: `cv2.INTER_NEAREST` (fastest overall)

### 4. **Multi-threading**
```python
torch.set_num_threads(4)  # Use 4 CPU threads
```

### 5. **Model Warmup**
Run 3 dummy inferences before starting to compile model

### 6. **Efficient Memory**
- Use deque for performance tracking (faster than list)
- Direct NumPy operations
- Minimize copies

### 7. **Pre-filtering**
Filter low-confidence detections before mask processing

---

## Performance Comparison

| Input Size | Expected Latency | Quality | Use Case |
|------------|-----------------|---------|----------|
| **432×432** | 180-200ms | ★★★★★ | Production |
| **384×384** | 120-150ms | ★★★★☆ | Balanced |
| **320×320** | 80-120ms | ★★★★☆ | Recommended |
| **224×224** | 50-80ms | ★★★☆☆ | Real-time |

With frame skip (×2):
| Input Size + Skip | Effective FPS | Latency Perceived |
|-------------------|---------------|-------------------|
| 320 + skip 2 | ~12-15 FPS | Smooth |
| 224 + skip 2 | ~18-25 FPS | Very smooth |

---

## Interactive Controls in Optimized Script

While running:
- **'1'** - Input size 224×224 (fastest)
- **'2'** - Input size 320×320 (fast)
- **'3'** - Input size 384×384 (balanced)
- **'4'** - Input size 432×432 (accurate)
- **'f'** - Toggle frame skip on/off

---

## Hardware-Specific Optimizations

### If you have a GPU:

```python
# Add to script (requires CUDA PyTorch)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)
img_tensor = img_tensor.to(device)
```

With GPU: **20-40ms** inference time!

### CPU Optimization:

```bash
# Set environment variables before running
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4

python live_inference_optimized.py --input-size 320
```

---

## Android Deployment Tips

For Android (similar latency targets):

### 1. Use Lower Resolution
```java
// Resize to 320×320 instead of 432×432
Bitmap resized = Bitmap.createScaledBitmap(bitmap, 320, 320, true);
```

### 2. Enable NNAPI
```java
model.setUseNNAPI(true);  // Use Android Neural Networks API
```

### 3. Process Every N Frames
```kotlin
private var frameCount = 0

override fun analyze(image: ImageProxy) {
    frameCount++
    if (frameCount % 2 == 0) {  // Process every 2nd frame
        runInference(image)
    }
    image.close()
}
```

### 4. Use Lower Quality Camera
```kotlin
imageAnalysis.setTargetResolution(Size(640, 480))  // Lower than 1080p
```

---

## Benchmarking Different Sizes

Run this to test all sizes:

```bash
# Test 224
python live_inference_optimized.py --input-size 224
# (Watch FPS for 30 seconds, press 'q')

# Test 320
python live_inference_optimized.py --input-size 320

# Test 384
python live_inference_optimized.py --input-size 384

# Test 432 (original)
python live_inference_optimized.py --input-size 432
```

---

## Expected Results

### On Your System (CPU):
- **432×432**: ~180-200ms ✅ (current)
- **320×320**: ~80-120ms ⚡ (recommended)
- **224×224**: ~50-80ms ⚡⚡ (fastest)

### With Frame Skip (×2):
- **320×320 + skip**: Effective ~12-15 FPS (smooth)
- **224×224 + skip**: Effective ~18-25 FPS (very smooth)

---

## Quality vs Speed Trade-off

### ✅ Recommended: 320×320
- Good balance
- ~2x faster than 432
- Minimal quality loss
- Works well for nail detection

### ⚡ For maximum speed: 224×224 + frame skip
- ~3-4x faster than 432
- Some quality loss (smaller masks)
- Still usable for nail AR

### 🎯 For production: 320×320 with adaptive skip
- Process every frame when hand is still
- Skip frames during movement
- Best user experience

---

## Advanced: Quantization (Future Optimization)

Convert model to INT8 for even faster inference:

```python
# Requires additional conversion (not done yet)
# Could achieve 30-50ms inference time
# Would need to re-export model with quantization
```

---

## Summary

**To reduce from 180-200ms to < 100ms:**

1. **Run optimized script:**
   ```bash
   python live_inference_optimized.py --input-size 320
   ```

2. **Expected result:** ~80-120ms (2x faster)

3. **For even faster:** Add `--skip-frames 2`

4. **For Android:** Use same optimizations (320×320 input, NNAPI, frame skip)

The optimized script has all these built-in and you can adjust them live with keyboard shortcuts!
