# Integration Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                  (frontend/app-realtime.html)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐         ┌──────────────────┐              │
│  │  Rendering Mode  │         │  Material        │              │
│  │  ○ WebGL (Fast)  │         │  Preset          │              │
│  │  ● Professional  │         │  Dropdown        │              │
│  └──────────────────┘         └──────────────────┘              │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  Color Picker    │  │  Glossiness      │  │  Metallic    │  │
│  │  #FF1493         │  │  [====|----]     │  │  [==|------] │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Canvas Display                         │   │
│  │              (Rendered nail polish result)                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP Request
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                              │
│                    (backend/main.py)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────┐  ┌─────────────────────────┐    │
│  │  /api/nails/segment        │  │  /api/nails/render-     │    │
│  │  (WebGL Mode)              │  │  professional           │    │
│  │                            │  │  (Professional Mode)    │    │
│  │  ┌──────────────────────┐  │  │                         │    │
│  │  │ RF-DETR Inference    │  │  │  ┌────────────────┐     │    │
│  │  │ ↓                    │  │  │  │ RF-DETR        │     │    │
│  │  │ Polygon Extraction   │  │  │  │ Inference      │     │    │
│  │  │ ↓                    │  │  │  │ ↓              │     │    │
│  │  │ Return JSON          │  │  │  │ Geometry       │     │    │
│  │  └──────────────────────┘  │  │  │ Analysis       │     │    │
│  │            │                │  │  │ ↓              │     │    │
│  │            │                │  │  │ Material       │     │    │
│  │            ▼                │  │  │ Selection      │     │    │
│  │      Frontend WebGL        │  │  │ ↓              │     │    │
│  │      Shader Rendering      │  │  │ Professional   │     │    │
│  │                            │  │  │ Rendering      │     │    │
│  └────────────────────────────┘  │  │ (6 Layers)     │     │    │
│                                   │  │ ↓              │     │    │
│  ┌────────────────────────────┐  │  │ Return JPEG    │     │    │
│  │  /api/materials            │  │  └────────────────┘     │    │
│  │  (Material List)           │  │                         │    │
│  │                            │  └─────────────────────────┘    │
│  │  Returns 11 presets        │                                 │
│  └────────────────────────────┘                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Uses
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              PROFESSIONAL NAIL RENDERER                          │
│         (professional_nail_renderer/)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  NailGeometryAnalyzer (nail_geometry.py)                  │   │
│  │  ├─ Contour detection                                     │   │
│  │  ├─ Curvature mapping (distance transform)                │   │
│  │  ├─ Normal map generation                                 │   │
│  │  └─ Highlight point calculation                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                 │                                 │
│                                 ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MaterialPresets (nail_material.py)                       │   │
│  │  ├─ glossy_red, glossy_nude                               │   │
│  │  ├─ matte_black, matte_pink                               │   │
│  │  ├─ metallic_gold, metallic_silver, chrome_mirror        │   │
│  │  └─ glitter_pink, glitter_silver, holographic            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                 │                                 │
│                                 ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PhotoRealisticNailRenderer                               │   │
│  │  (photo_realistic_renderer.py)                            │   │
│  │                                                            │   │
│  │  6-Layer Rendering Pipeline:                              │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │ 1. Base Color      → Solid color fill            │    │   │
│  │  │ 2. Curvature       → 3D depth effect             │    │   │
│  │  │ 3. Specular        → Blinn-Phong highlights      │    │   │
│  │  │ 4. Ambient Occ.    → Contact shadows             │    │   │
│  │  │ 5. Edge Darkening  → Depth at boundaries         │    │   │
│  │  │ 6. Glitter         → Sparkle particles           │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                      ↓                                     │   │
│  │            Alpha Blending + Edge Feathering               │   │
│  │                      ↓                                     │   │
│  │           Photo-Realistic Output Image                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ Uses
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RF-DETR MODEL                               │
│     (checkpoint_best_total.pth / rfdetr_nails.pt)                │
├─────────────────────────────────────────────────────────────────┤
│  ├─ DINOv2 Encoder (windowed small)                             │
│  ├─ 2600 Queries (200 × 13 group_detr)                          │
│  ├─ Patch size: 12×12                                            │
│  ├─ Input: 432×432                                               │
│  └─ Output: Masks [200, 108, 108] + Scores                      │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Comparison

### WebGL Mode (Fast)
```
Frame → Backend → Polygons → Frontend → WebGL Shader → Display
 5ms     180ms      JSON       50ms        10ms         ~245ms total
```

### Professional Mode (High Quality)
```
Frame → Backend → Pro Renderer → Frontend → Display
 5ms     180ms      250-500ms      50ms      ~485-735ms total
                   (per frame)
```

## Request/Response Examples

### WebGL Mode Request
```http
POST /api/nails/segment
Content-Type: multipart/form-data

file: frame.jpg
```

**Response:**
```json
{
  "width": 640,
  "height": 480,
  "nails": [
    {
      "id": 0,
      "score": 0.95,
      "polygon": [120, 150, 125, 148, ...]
    }
  ]
}
```

### Professional Mode Request
```http
POST /api/nails/render-professional
Content-Type: multipart/form-data

file: frame.jpg
material: metallic_gold
glossiness: 0.8
metallic: 0.9
intensity: 0.85
```

**Response:**
```
Content-Type: image/jpeg
X-Nail-Count: 2
X-Material: metallic_gold
X-Glossiness: 0.8
X-Metallic: 0.9

[JPEG Binary Data - Rendered Image]
```

## Technology Stack

```
┌─────────────────────────────────────────┐
│          FRONTEND                        │
├─────────────────────────────────────────┤
│ - HTML5 + Canvas                        │
│ - WebGL 2.0 (for fast mode)             │
│ - Vanilla JavaScript                    │
│ - Real-time video processing            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          BACKEND                         │
├─────────────────────────────────────────┤
│ - FastAPI (Python 3.12)                 │
│ - RF-DETR (rfdetr library)              │
│ - PyTorch                                │
│ - OpenCV (cv2)                           │
│ - NumPy                                  │
│ - PIL/Pillow                             │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│     PROFESSIONAL RENDERER                │
├─────────────────────────────────────────┤
│ - NumPy (array operations)              │
│ - OpenCV (image processing)             │
│ - Custom PBR implementation             │
│ - Blinn-Phong shading model             │
│ - Distance transform algorithms         │
└─────────────────────────────────────────┘
```

## Model Usage

**Both modes use the SAME RF-DETR model:**

| Format | Used By | Purpose |
|--------|---------|---------|
| `.pth` checkpoint | Backend (both modes) | Full model with training weights |
| `.pt` TorchScript | Standalone demos | Mobile-optimized export |

**Key Point:** The backend uses `checkpoint_best_total.pth` loaded via `RFDETRSegPreview` for both WebGL and Professional modes.

## Performance Characteristics

| Aspect | WebGL Mode | Professional Mode |
|--------|-----------|-------------------|
| **Speed** | ⚡⚡⚡⚡⚡ Fast (245ms) | ⚡⚡⚡ Moderate (735ms) |
| **Quality** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent |
| **Realism** | Basic LAB remapping | Full PBR with 6 layers |
| **Highlights** | Simple brightness | Blinn-Phong specular |
| **Edge Quality** | 3px blur | Gaussian feathering |
| **Materials** | Custom colors | 11 presets + custom |
| **Use Case** | Real-time preview | Final output |

---

*This architecture enables seamless switching between fast preview and professional-quality rendering!*
