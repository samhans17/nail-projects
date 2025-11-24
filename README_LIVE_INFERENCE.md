# Live Inference Scripts

Two scripts for testing your nail segmentation model with a webcam.

---

## Option 1: PyTorch Mobile Model (Tests Android Model)

Tests the exported `.pt` model that you'll use on Android.

### Run:
```bash
python live_inference_pytorch_mobile.py
```

### Features:
- ✅ Tests the **exact same model** that runs on Android
- ✅ See how it performs before deploying
- ✅ Real-time visualization with masks
- ✅ FPS counter and inference time
- ✅ Adjustable confidence threshold

### Controls:
- **q** or **ESC** - Quit
- **SPACE** - Pause/Resume
- **s** - Save screenshot
- **+/-** - Adjust confidence threshold

### Options:
```bash
python live_inference_pytorch_mobile.py --help

# Custom camera
python live_inference_pytorch_mobile.py --camera 1

# Custom threshold
python live_inference_pytorch_mobile.py --threshold 0.3

# Lower resolution (faster)
python live_inference_pytorch_mobile.py --width 320 --height 240
```

---

## Option 2: Original RF-DETR (Faster & More Accurate)

Uses the Python RF-DETR library directly (not the mobile model).

### Run:
```bash
python live_inference_original.py
```

### Features:
- ✅ Faster inference (uses Python API)
- ✅ More accurate (no conversion artifacts)
- ✅ Better for testing on your computer
- ✅ Same visualization and controls

### Use When:
- Testing the model quality
- Developing your application
- Your computer has good GPU

---

## Requirements

Both scripts need:
```bash
pip install opencv-python pillow numpy

# For original RF-DETR:
pip install rfdetr
```

---

## Comparison

| Feature | PyTorch Mobile | Original RF-DETR |
|---------|----------------|------------------|
| **Model** | `rfdetr_nails.pt` | Python checkpoint |
| **Speed** | Slower (mobile optimized) | Faster (native Python) |
| **Accuracy** | Same as Android | Full accuracy |
| **Use Case** | Test Android model | Development/Testing |
| **FPS (typical)** | ~5-10 FPS | ~10-20 FPS |

---

## Example Output

```
============================================================
Live Nail Segmentation with PyTorch Mobile
============================================================

📦 Loading PyTorch Mobile model from: ./pytorch_mobile_models/rfdetr_nails.pt
✅ Model loaded successfully
📷 Opening camera 0...
✅ Camera opened: 640×480

============================================================
CONTROLS:
  'q' or 'ESC' - Quit
  'SPACE'      - Pause/Resume
  's'          - Save screenshot
  '+'/'-'      - Adjust confidence threshold
============================================================

[Real-time video window showing:]
FPS: 8.5
Inference: 118.2ms
Nails: 3
Threshold: 0.50
```

---

## Troubleshooting

### Camera not found:
```bash
# List available cameras
python -c "import cv2; print([cv2.VideoCapture(i).isOpened() for i in range(5)])"

# Try different camera index
python live_inference_pytorch_mobile.py --camera 1
```

### Too slow:
```bash
# Lower resolution
python live_inference_pytorch_mobile.py --width 320 --height 240

# Or use the original model
python live_inference_original.py
```

### Model not found:
```bash
# Check model exists
ls -lh pytorch_mobile_models/rfdetr_nails.pt

# Re-export if needed
python export_pytorch_mobile_simple.py
```

---

## Performance Tips

1. **Close other applications** to free up CPU/GPU
2. **Use lower resolution** for faster processing
3. **Adjust threshold** to filter low-confidence detections
4. **Use original model** for development, mobile model for final testing

---

## Next Steps

After testing:
1. ✅ Verify model works correctly
2. ✅ Check performance (FPS)
3. ✅ Adjust threshold for best results
4. 📱 Deploy to Android (see ANDROID_DEPLOYMENT_GUIDE.md)

---

## Visualization

The scripts show:
- **Colored masks** - Each nail gets a different color
- **Contours** - Outline of detected nails
- **Confidence** - Score for each detection
- **FPS counter** - Real-time performance
- **Inference time** - Per-frame processing time

---

Enjoy testing your nail segmentation model! 🎉
