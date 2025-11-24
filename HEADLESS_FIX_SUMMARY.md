# Headless Mode Fix Summary

## Problem
The original `live_inference_professional.py` script crashed in headless environments (SSH, Docker, remote servers) with:

```
cv2.error: The function is not implemented. Rebuild the library with Windows, GTK+ 2.x or Cocoa support.
```

This happened because `cv2.imshow()` and `cv2.destroyAllWindows()` require a display server.

---

## Solution
Added **automatic headless mode detection and support** to the same script.

### What Changed

1. **Auto-Detection**
   - Script now detects if display is available
   - Automatically switches to headless mode if needed
   - Clear message about which mode is active

2. **Headless Mode Features**
   - Saves frames to timestamped directories
   - Prints progress to console
   - Configurable save frequency
   - Optional frame limit
   - No GUI dependencies

3. **New Command-Line Options**
   - `--headless` - Force headless mode
   - `--output-dir DIR` - Where to save frames (default: `renders/`)
   - `--save-every N` - Save every Nth frame (default: 10)
   - `--max-frames N` - Stop after N frames (optional)

---

## Usage

### Automatic (Recommended)

```bash
# Automatically detects and uses appropriate mode
python live_inference_professional.py --material glossy_red
```

**On machine with display:** Opens GUI window
**On headless server:** Saves frames to disk

### Force Headless

```bash
# Force headless even if display available
python live_inference_professional.py \
    --headless \
    --material metallic_gold \
    --max-frames 100 \
    --save-every 10
```

**Output:**
```
🖥️  HEADLESS MODE - Saving frames to disk
   Output: renders/session_20251123_032838/
   Saving every 10 frames
   Max frames: 100

[    1] Saved frame_00001.jpg | 2 nails | Inference: 241.7ms | Render: 45.2ms
[   10] Saved frame_00010.jpg | 3 nails | Inference: 238.1ms | Render: 67.3ms
...
```

---

## Testing

### Test Headless Mode

```bash
# Process 5 frames and save all
python live_inference_professional.py \
    --headless \
    --max-frames 5 \
    --save-every 1 \
    --material glossy_red
```

**Check output:**
```bash
ls renders/session_*/
# Output:
# frame_00001.jpg  frame_00002.jpg  frame_00003.jpg  frame_00004.jpg  frame_00005.jpg
```

---

## Benefits

✅ **Backward Compatible** - Existing usage still works
✅ **Auto-Detection** - No manual mode selection needed
✅ **SSH Compatible** - Works on remote servers
✅ **Docker Compatible** - No display required
✅ **Flexible** - Force mode if needed
✅ **Progress Tracking** - Clear console output
✅ **Organized Output** - Timestamped session directories

---

## Files Modified

- **`live_inference_professional.py`** - Added headless support

## Files Created

- **`HEADLESS_MODE_GUIDE.md`** - Complete usage guide
- **`HEADLESS_FIX_SUMMARY.md`** - This file

---

## Next Steps

1. ✅ **Test it:**
   ```bash
   python live_inference_professional.py --headless --max-frames 10
   ```

2. 📖 **Read the guide:**
   See [HEADLESS_MODE_GUIDE.md](HEADLESS_MODE_GUIDE.md) for advanced usage

3. 🎥 **Create videos:**
   Use ffmpeg or OpenCV to compile saved frames into videos

---

## Example: Complete Workflow

```bash
# 1. Run headless processing
python live_inference_professional.py \
    --headless \
    --material metallic_gold \
    --max-frames 300 \
    --save-every 10

# 2. Check output
ls renders/session_*/

# 3. Create video (optional)
cd renders/session_20251123_032838/
ffmpeg -framerate 10 -pattern_type glob -i 'frame_*.jpg' \
    -c:v libx264 -pix_fmt yuv420p output.mp4

# 4. View video
vlc output.mp4
```

---

**Status:** ✅ **FIXED** - Script now works in all environments!
