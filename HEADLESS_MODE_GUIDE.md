# Headless Mode Guide

The professional nail AR system now supports **headless mode** for environments without display/GUI support (SSH, remote servers, Docker containers, etc.).

---

## 🔍 Auto-Detection

The script automatically detects if a display is available:

```bash
# Automatically uses headless mode if no display detected
python live_inference_professional.py --material glossy_red
```

**Output:**
```
🖥️  HEADLESS MODE - Saving frames to disk
   (No display detected - auto-switched to headless)
   Output: renders/session_20251123_032838/
```

---

## 🎯 Headless Mode Usage

### Basic Usage

```bash
# Force headless mode (even if display available)
python live_inference_professional.py --headless --material metallic_gold
```

### Process Limited Frames

```bash
# Process exactly 100 frames then stop
python live_inference_professional.py \
    --headless \
    --max-frames 100 \
    --material glossy_red
```

### Save Every Nth Frame

```bash
# Save every 10th frame (reduces disk usage)
python live_inference_professional.py \
    --headless \
    --save-every 10 \
    --max-frames 500 \
    --material glitter_pink
```

### Custom Output Directory

```bash
# Save to specific directory
python live_inference_professional.py \
    --headless \
    --output-dir /path/to/my/renders \
    --material chrome_mirror
```

---

## 📊 Example Output

```bash
$ python live_inference_professional.py --headless --max-frames 5 --save-every 1

============================================================
✨ PROFESSIONAL NAIL AR - Photo-Realistic Rendering
============================================================

🖥️  HEADLESS MODE - Saving frames to disk
   Output: renders/session_20251123_032838/
   Saving every 1 frames
   Max frames: 5

📦 Loading PyTorch Mobile model...
✅ Model loaded
🎨 Initializing professional renderer...
✅ Renderer initialized
💅 Material: glossy_red
📷 Opening camera 0...
✅ Camera opened

[    1] Saved frame_00001.jpg | 0 nails | Inference: 241.7ms | Render: 0.2ms | Total: 242.0ms
[    2] Saved frame_00002.jpg | 0 nails | Inference: 239.9ms | Render: 0.2ms | Total: 240.1ms
[    3] Saved frame_00003.jpg | 2 nails | Inference: 238.1ms | Render: 45.3ms | Total: 283.4ms
[    4] Saved frame_00004.jpg | 2 nails | Inference: 237.8ms | Render: 44.9ms | Total: 282.7ms
[    5] Saved frame_00005.jpg | 2 nails | Inference: 238.2ms | Render: 45.1ms | Total: 283.3ms

✅ Reached max frames limit (5)

============================================================
STATISTICS
============================================================
Total frames: 5
Processed frames: 5
Avg inference: 239.14ms
Avg render: 27.14ms
Total pipeline: 266.28ms
Avg FPS: 3.8
Saved frames: 5
Output directory: renders/session_20251123_032838
============================================================
```

---

## 📁 Output Structure

```
renders/
└── session_20251123_032838/
    ├── frame_00001.jpg
    ├── frame_00002.jpg
    ├── frame_00003.jpg
    ├── frame_00004.jpg
    └── frame_00005.jpg
```

Each session creates a timestamped subdirectory to avoid overwriting previous renders.

---

## ⚙️ Command-Line Options

### Required (Auto-detected)
- None! The script auto-detects headless environment

### Headless-Specific Options

| Option | Default | Description |
|--------|---------|-------------|
| `--headless` | False | Force headless mode |
| `--output-dir` | `renders` | Directory for output frames |
| `--save-every` | 10 | Save every N processed frames |
| `--max-frames` | None | Stop after N frames (unlimited if not set) |

### General Options (Work in Both Modes)

| Option | Default | Description |
|--------|---------|-------------|
| `--material` | `glossy_red` | Material preset to use |
| `--threshold` | 0.2 | Confidence threshold for detection |
| `--skip-frames` | 1 | Process every N camera frames |
| `--threads` | 4 | Number of CPU threads |
| `--camera` | 0 | Camera device index |

---

## 🎬 Use Cases

### 1. Testing on Remote Server

```bash
# SSH into server
ssh user@server

# Run headless test
cd /path/to/nail-project
python live_inference_professional.py \
    --headless \
    --max-frames 20 \
    --save-every 5 \
    --material metallic_gold

# Download results
# (from local machine)
scp -r user@server:/path/to/nail-project/renders/ ./
```

### 2. Batch Processing

```bash
# Process 1000 frames with different materials
for material in glossy_red matte_black metallic_gold; do
    python live_inference_professional.py \
        --headless \
        --max-frames 1000 \
        --save-every 50 \
        --material $material \
        --output-dir renders_$material
done
```

### 3. Create Dataset

```bash
# Generate training/testing dataset
python live_inference_professional.py \
    --headless \
    --max-frames 5000 \
    --save-every 1 \
    --material glossy_red \
    --output-dir dataset/glossy_red_renders
```

### 4. Performance Benchmarking

```bash
# Test different configurations
for skip in 1 2 3; do
    python live_inference_professional.py \
        --headless \
        --skip-frames $skip \
        --max-frames 100 \
        --save-every 100 \
        --material glossy_red \
        --output-dir benchmark_skip_$skip
done
```

---

## 🎥 Creating Videos from Frames

If you want to compile saved frames into a video:

### Using FFmpeg

```bash
# Install ffmpeg if needed
sudo apt install ffmpeg

# Create video from frames
cd renders/session_20251123_032838/
ffmpeg -framerate 30 -pattern_type glob -i 'frame_*.jpg' \
    -c:v libx264 -pix_fmt yuv420p \
    output_video.mp4
```

### Using Python (OpenCV)

```python
import cv2
import glob
from pathlib import Path

def frames_to_video(frame_dir, output_path, fps=30):
    # Get all frames
    frames = sorted(glob.glob(f"{frame_dir}/frame_*.jpg"))

    if not frames:
        print("No frames found!")
        return

    # Read first frame to get dimensions
    first_frame = cv2.imread(frames[0])
    height, width = first_frame.shape[:2]

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Write frames
    for frame_path in frames:
        frame = cv2.imread(frame_path)
        out.write(frame)
        print(f"Added {Path(frame_path).name}")

    out.release()
    print(f"Video saved to {output_path}")

# Usage
frames_to_video("renders/session_20251123_032838", "output.mp4", fps=10)
```

---

## 🐛 Troubleshooting

### Issue: "No display detected" but I have X11 forwarding

**Solution:** Force GUI mode by NOT using `--headless`:

```bash
# Enable X11 forwarding
ssh -X user@server

# Run without --headless
python live_inference_professional.py --material glossy_red
```

### Issue: Camera not opening

**Check camera permissions:**
```bash
# List video devices
ls -l /dev/video*

# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again
```

**Or use video file instead:**
```python
# Modify script to use video file
cap = cv2.VideoCapture("input_video.mp4")
```

### Issue: Frames not saving

**Check permissions:**
```bash
# Ensure output directory is writable
mkdir -p renders
chmod 755 renders

# Run script
python live_inference_professional.py --headless
```

### Issue: Disk filling up too fast

**Solution:** Increase `--save-every`:

```bash
# Save every 50 frames instead of every 10
python live_inference_professional.py \
    --headless \
    --save-every 50
```

---

## 📈 Performance Tips

### Optimize for Headless Processing

1. **Increase frame skipping:**
   ```bash
   --skip-frames 3  # Process every 3rd frame
   ```

2. **Reduce save frequency:**
   ```bash
   --save-every 20  # Save less often
   ```

3. **Use more CPU threads:**
   ```bash
   --threads 8  # Use more cores
   ```

4. **Lower camera resolution:**
   ```bash
   --width 640 --height 480  # Smaller frames = faster
   ```

### Example: Maximum Speed

```bash
python live_inference_professional.py \
    --headless \
    --skip-frames 3 \
    --save-every 50 \
    --threads 8 \
    --max-frames 1000
```

---

## ✅ Comparison: GUI vs Headless

| Feature | GUI Mode | Headless Mode |
|---------|----------|---------------|
| **Display** | Live window | Saved frames |
| **Interaction** | Keyboard controls | Command-line only |
| **Material switching** | Press 'n' | Restart with new `--material` |
| **Screenshot** | Press 's' | Automatic (every N frames) |
| **Performance** | Slightly slower (rendering to screen) | Faster (no display overhead) |
| **SSH compatible** | No (requires X11 forwarding) | ✅ Yes |
| **Docker compatible** | No | ✅ Yes |
| **Batch processing** | Manual | ✅ Easy scripting |

---

## 🎉 Summary

**Headless mode makes the professional nail AR system work anywhere:**

✅ SSH/remote servers
✅ Docker containers
✅ Cloud instances
✅ CI/CD pipelines
✅ Batch processing scripts

**Just add `--headless` and you're good to go!**

```bash
python live_inference_professional.py --headless --material glossy_red
```

---

*For GUI mode documentation, see [QUICKSTART_PROFESSIONAL_AR.md](QUICKSTART_PROFESSIONAL_AR.md)*
