# 🚀 Deployment Checklist - Professional Nail AR

Use this checklist to deploy your professional nail AR system to production.

---

## ✅ Pre-Deployment Validation

### 1. Test Installation
```bash
cd /home/usama-naveed/nail-project
python test_professional_renderer.py
```
**Expected:** All 10 tests pass ✅

### 2. Verify Live Demo Works
```bash
python live_inference_professional.py --material glossy_red
```
**Expected:**
- Window opens showing webcam
- Nails are detected
- Photo-realistic rendering appears
- Can cycle materials with 'n'

### 3. Run Comparison
```bash
python compare_renderers.py
```
**Expected:**
- Side-by-side comparison appears
- Professional rendering clearly better than basic

### 4. Check Generated Files
```bash
ls test_render_*.jpg
```
**Expected:** 4+ test render files exist

---

## 📦 Backend Integration

### Step 1: Add Rendering Endpoint

Edit `backend/main.py`:

```python
# Add imports at top
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'professional_nail_renderer'))

from professional_nail_renderer import (
    NailGeometryAnalyzer,
    PhotoRealisticNailRenderer,
    MaterialPresets
)

# Initialize globally (after model loading)
print("Initializing professional renderer...")
geometry_analyzer = NailGeometryAnalyzer()
professional_renderer = PhotoRealisticNailRenderer(
    light_direction=(-0.3, -0.5, 0.8),
    ambient_intensity=0.4
)
print("Professional renderer ready!")

# Add new endpoint
@app.post("/api/nails/render-professional")
async def render_professional(
    file: UploadFile = File(...),
    material: str = "glossy_red"
):
    """
    Render nails with professional photo-realistic materials

    Args:
        file: Image file upload
        material: Material preset name (see /api/materials)

    Returns:
        Image with professional nail polish rendering
    """
    # Load image
    raw = await file.read()
    img = read_image_from_bytes(raw)
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Run RT-DETR segmentation
    detections = model.predict(img, threshold=0.5)

    # Get material
    presets = MaterialPresets.all_presets()
    if material not in presets:
        material = "glossy_red"  # Default fallback
    material_obj = presets[material]

    # Render each nail
    result = frame.copy()
    nail_count = 0

    if detections.mask is not None:
        for idx in range(len(detections)):
            mask = detections.mask[idx]

            # Analyze geometry
            geometry = geometry_analyzer.analyze(mask, min_area=100)
            if geometry is None:
                continue

            # Render professionally
            result = professional_renderer.render_nail(
                result,
                geometry,
                material_obj
            )
            nail_count += 1

    # Convert back to RGB
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    result_pil = Image.fromarray(result_rgb)

    # Encode to bytes
    import io
    img_byte_arr = io.BytesIO()
    result_pil.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)

    return StreamingResponse(
        img_byte_arr,
        media_type="image/jpeg",
        headers={
            "X-Nail-Count": str(nail_count),
            "X-Material": material
        }
    )

# Add materials list endpoint
@app.get("/api/materials")
async def get_materials():
    """Get list of available material presets"""
    presets = MaterialPresets.all_presets()

    materials = []
    for name, mat in presets.items():
        materials.append({
            "name": name,
            "finish": mat.get_finish_type().value,
            "glossiness": mat.glossiness,
            "metallic": mat.metallic,
            "has_glitter": mat.has_glitter
        })

    return {"materials": materials}
```

### Step 2: Test Backend

```bash
# Start backend
cd backend
uvicorn main:app --reload

# Test materials endpoint
curl http://localhost:8000/api/materials

# Test rendering (from another terminal)
curl -X POST http://localhost:8000/api/nails/render-professional \
  -F "file=@test_hand.jpg" \
  -F "material=glossy_red" \
  --output result_professional.jpg
```

**Expected:**
- Materials endpoint returns list of 11+ materials
- Rendering endpoint returns image with professional rendering
- Headers include nail count and material name

---

## 🎨 Frontend Integration

### Step 1: Add Material Selector

Update `frontend/index.html` (or your React/Vue component):

```html
<!-- Material selector -->
<select id="material-select">
  <option value="glossy_red">Glossy Red</option>
  <option value="glossy_nude">Glossy Nude</option>
  <option value="matte_black">Matte Black</option>
  <option value="matte_pink">Matte Pink</option>
  <option value="metallic_gold">Metallic Gold</option>
  <option value="metallic_silver">Metallic Silver</option>
  <option value="chrome_mirror">Chrome Mirror</option>
  <option value="glitter_pink">Glitter Pink</option>
  <option value="glitter_silver">Glitter Silver</option>
  <option value="holographic">Holographic</option>
  <option value="satin_burgundy">Satin Burgundy</option>
</select>
```

### Step 2: Update JavaScript

```javascript
async function uploadAndRender() {
  const fileInput = document.getElementById('file-input');
  const materialSelect = document.getElementById('material-select');

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('material', materialSelect.value);

  // Show loading state
  showLoading();

  try {
    const response = await fetch('/api/nails/render-professional', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) throw new Error('Rendering failed');

    const blob = await response.blob();
    const imageUrl = URL.createObjectURL(blob);

    // Get metadata from headers
    const nailCount = response.headers.get('X-Nail-Count');
    const material = response.headers.get('X-Material');

    // Display result
    document.getElementById('result-image').src = imageUrl;
    document.getElementById('nail-count').textContent = `${nailCount} nails detected`;
    document.getElementById('used-material').textContent = material;

    hideLoading();
  } catch (error) {
    console.error('Error:', error);
    showError('Failed to render image');
  }
}
```

### Step 3: Test Frontend

```bash
# Open frontend
cd frontend
python -m http.server 8080

# Navigate to http://localhost:8080
# Upload image
# Select material
# Click render
```

**Expected:**
- Material dropdown shows all options
- Uploading + rendering works
- Professional rendering appears
- Nail count displayed

---

## 🔧 Performance Tuning

### Backend Optimization

Add these to your backend for better performance:

```python
# In main.py, after initializing renderer

# Enable multi-threading
import torch
torch.set_num_threads(8)  # Adjust for your server

# Warm up renderer
print("Warming up renderer...")
dummy_mask = np.zeros((480, 640), dtype=np.uint8)
cv2.ellipse(dummy_mask, (320, 240), (60, 100), 45, 0, 360, 1, -1)
dummy_geometry = geometry_analyzer.analyze(dummy_mask)
dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 200

for _ in range(3):
    _ = professional_renderer.render_nail(
        dummy_frame,
        dummy_geometry,
        MaterialPresets.glossy_red()
    )
print("Renderer warmed up!")
```

### Caching (Optional)

For frequently requested materials:

```python
from functools import lru_cache

# Cache material objects
@lru_cache(maxsize=20)
def get_material(name: str):
    presets = MaterialPresets.all_presets()
    return presets.get(name, presets["glossy_red"])

# Use in endpoint
material_obj = get_material(material)
```

---

## 📊 Monitoring

### Add Performance Logging

```python
import time

@app.post("/api/nails/render-professional")
async def render_professional(...):
    start_time = time.time()

    # ... existing code ...

    # Log performance
    total_time = (time.time() - start_time) * 1000
    print(f"Professional render: {total_time:.1f}ms for {nail_count} nails")

    return StreamingResponse(
        ...,
        headers={
            ...,
            "X-Render-Time": f"{total_time:.1f}ms"
        }
    )
```

### Monitor in Production

```bash
# Check average render time
grep "Professional render" logs.txt | awk '{print $3}' | \
  awk '{sum+=$1; count++} END {print "Avg:", sum/count "ms"}'
```

---

## 🚦 Production Checklist

### Pre-Launch
- [ ] All tests pass (`test_professional_renderer.py`)
- [ ] Backend endpoint works (`/api/nails/render-professional`)
- [ ] Frontend integrated with material selector
- [ ] Error handling implemented
- [ ] Performance acceptable (< 500ms per request)
- [ ] Documentation updated

### Launch
- [ ] Deploy backend with professional renderer
- [ ] Deploy frontend with material selector
- [ ] Update API documentation
- [ ] Monitor logs for errors
- [ ] Test with real users

### Post-Launch
- [ ] Monitor render times
- [ ] Collect user feedback on materials
- [ ] A/B test professional vs basic rendering
- [ ] Plan additional material presets

---

## 🎯 Success Metrics

### Technical Metrics
- **Render Time**: < 300ms per image (5 nails)
- **Error Rate**: < 1% of requests
- **Uptime**: > 99%

### User Metrics
- **Engagement**: Higher time-on-site with professional rendering
- **Conversions**: More users trying different materials
- **Satisfaction**: Positive feedback on realistic appearance

---

## 📝 Documentation Updates

### Update API Docs

Add to your OpenAPI/Swagger docs:

```yaml
/api/nails/render-professional:
  post:
    summary: Render nails with professional materials
    description: |
      Applies photo-realistic nail polish rendering with physically-based
      materials including glossy highlights, 3D curvature, and edge feathering.

    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Image file containing hand(s)

      - name: material
        in: formData
        type: string
        default: glossy_red
        enum:
          - glossy_red
          - glossy_nude
          - matte_black
          - matte_pink
          - metallic_gold
          - metallic_silver
          - chrome_mirror
          - glitter_pink
          - glitter_silver
          - holographic
          - satin_burgundy

    responses:
      200:
        description: Rendered image
        content:
          image/jpeg:
            schema:
              type: string
              format: binary
        headers:
          X-Nail-Count:
            schema:
              type: integer
            description: Number of nails detected and rendered
          X-Material:
            schema:
              type: string
            description: Material used for rendering
          X-Render-Time:
            schema:
              type: string
            description: Rendering time in milliseconds

/api/materials:
  get:
    summary: List available materials
    responses:
      200:
        description: List of material presets
        content:
          application/json:
            schema:
              type: object
              properties:
                materials:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      finish:
                        type: string
                      glossiness:
                        type: number
                      metallic:
                        type: number
                      has_glitter:
                        type: boolean
```

---

## 🔒 Security Considerations

### Input Validation

```python
# Validate material parameter
ALLOWED_MATERIALS = set(MaterialPresets.all_presets().keys())

@app.post("/api/nails/render-professional")
async def render_professional(...):
    # Validate material
    if material not in ALLOWED_MATERIALS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid material. Allowed: {list(ALLOWED_MATERIALS)}"
        )

    # ... rest of code
```

### File Size Limits

```python
# In FastAPI app config
app = FastAPI(
    title="Nail AR API",
    max_upload_size=10_000_000  # 10MB max
)
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/nails/render-professional")
@limiter.limit("10/minute")  # Max 10 requests per minute
async def render_professional(...):
    # ... code
```

---

## ✅ Final Checklist

### Development
- [x] Professional renderer implemented
- [x] All tests passing
- [x] Documentation complete
- [x] Demo applications working

### Integration
- [ ] Backend endpoint added
- [ ] Frontend updated
- [ ] API documentation updated
- [ ] Error handling added

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing complete
- [ ] Performance acceptable

### Deployment
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Monitoring enabled
- [ ] Documentation published

### Post-Deployment
- [ ] Users can access new feature
- [ ] Metrics being collected
- [ ] No critical errors
- [ ] Positive user feedback

---

## 🎉 You're Ready!

Once all items are checked, your professional nail AR system is **production ready**!

**Support Resources:**
- [QUICKSTART_PROFESSIONAL_AR.md](QUICKSTART_PROFESSIONAL_AR.md)
- [PROFESSIONAL_RENDERING_GUIDE.md](PROFESSIONAL_RENDERING_GUIDE.md)
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

**Next Steps:**
1. Complete backend integration
2. Update frontend UI
3. Test with real users
4. Monitor and iterate

Good luck with your deployment! 🚀💅✨
