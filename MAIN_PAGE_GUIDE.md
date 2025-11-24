# 🏠 Main Landing Page Guide

## What Is It?

The main landing page (`http://localhost:3000/`) is a beautiful dashboard that:

✅ Shows all available versions of the nail AR app
✅ Displays live system status (Backend, WebGL, Camera)
✅ Lets you choose the best version for your device
✅ Provides quick links to all features

---

## How to Access

### Start Everything:
```bash
cd /home/usama-naveed/nail-project
./run.sh
```

Choose option **1** (Start both)

### Open Browser:
```
http://localhost:3000/
```

---

## What You'll See

### 4 Version Cards:

#### 1. ⭐ Optimized Real-Time (RECOMMENDED)
- **URL:** `/app-realtime-optimized.html`
- **Features:**
  - Performance presets (Low/Medium/High)
  - 60 FPS @ 640×480
  - Live stats dashboard
  - Auto re-segmentation
  - WebGL accelerated

**Best for:** Most devices, demos, general use

---

#### 2. Standard Real-Time
- **URL:** `/app-realtime.html`
- **Features:**
  - Full manual control
  - 60 FPS rendering
  - Live performance metrics
  - Adjustable parameters
  - GPU accelerated

**Best for:** Advanced users, custom settings, fast devices

---

#### 3. WebGL Manual
- **URL:** `/app-webgl.html`
- **Features:**
  - Click-to-segment (no auto)
  - Lower resource usage
  - Better battery life
  - WebGL effects

**Best for:** Precision work, slower devices, battery saving

---

#### 4. Basic (Fallback)
- **URL:** `/index-basic.html`
- **Features:**
  - Works on all browsers
  - No WebGL required
  - LAB color space
  - Lightweight

**Best for:** Old browsers, compatibility, no GPU

---

## System Status Checks

The landing page automatically checks:

### ✓ Backend API
- **Green "✓ Running"** = Backend is ready
- **Red "✗ Offline"** = Backend not started

**Fix:** Run `uvicorn main:app --reload` in backend folder

---

### ✓ WebGL Support
- **Green "✓ Supported"** = Your browser supports WebGL 2.0
- **Red "✗ Not Available"** = Use Basic version instead

**Fix:** Update browser or enable hardware acceleration

---

### ✓ Camera Access
- **Green "✓ Available"** = Camera API available
- **Red "✗ Not Available"** = Wrong URL or old browser

**Fix:** Use `localhost`, not IP address

---

## Quick Start Section

The blue info box at the bottom shows:
1. How to start backend
2. Which version to choose
3. Basic usage instructions

---

## Navigation

From the main page, you can:

1. **Click any "Launch" button** to open that version
2. **Check system status** before starting
3. **See which version is recommended** (⭐ badge)
4. **Compare features** of each version

---

## Design Features

### Visual Indicators:
- **⭐ RECOMMENDED** badge on best version
- **Color-coded badges** for each version type
- **Hover effects** on version cards
- **Live status checks** with colors

### Responsive Design:
- Works on desktop and mobile
- Cards stack on small screens
- Status items adapt to screen size

---

## URL Structure

```
http://localhost:3000/
├── (main landing page - index.html)
│
├── app-realtime-optimized.html  ⭐ RECOMMENDED
├── app-realtime.html
├── app-webgl.html
└── index-basic.html
```

---

## Advantages of Using Main Page

✅ **No guessing** - See all options at once
✅ **System check** - Know what's working before you start
✅ **Easy comparison** - See feature lists side-by-side
✅ **One-click launch** - Just click and go
✅ **Status monitoring** - Real-time checks for backend/WebGL/camera

---

## Common Scenarios

### First Time User:
1. Open main page
2. Check system status (all green?)
3. Click "Launch Optimized Version"
4. Start with Medium preset

---

### Advanced User:
1. Open main page
2. Click "Launch Standard Version"
3. Fine-tune all parameters
4. Use custom intervals

---

### Slow Device:
1. Open main page
2. See system status
3. Click "Launch Optimized Version"
4. Use Low preset

---

### Compatibility Issues:
1. Open main page
2. See "WebGL Not Available"
3. Click "Launch Basic Version"
4. Still works without WebGL!

---

## Tips

💡 **Bookmark the main page** - It's your dashboard
💡 **Check status first** - Saves debugging time
💡 **Try recommended version first** - Optimized for most cases
💡 **Use presets** - Easier than manual tuning
💡 **Share the link** - Easy for others to start

---

## Summary

The main landing page is your **control center** for the nail AR system:

- ✅ Shows all versions
- ✅ Checks system status
- ✅ Recommends best option
- ✅ One-click access
- ✅ Beautiful design

**Just open `http://localhost:3000/` and choose your version! 🚀**
