# backend/main.py
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import sys
import os
from pathlib import Path
import io
import cv2
import numpy as np

from model_rf_deter import run_inference, get_model
from schemas import NailResponse, NailInstance
from utils import read_image_from_bytes
from cache import segmentation_cache

# Add professional renderer to path
# Get the project root directory (parent of backend/) and add it to sys.path
# This allows importing professional_nail_renderer as a package
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from professional_nail_renderer import (
    NailGeometryAnalyzer,
    PhotoRealisticNailRenderer,
    MaterialPresets,
    NailMaterial,
    MaterialFinish
)

app = FastAPI(title="Virtual Nails RF-DETR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize professional renderer (once at startup)
print("Initializing professional nail renderer...")
geometry_analyzer = NailGeometryAnalyzer()
professional_renderer = PhotoRealisticNailRenderer(
    light_direction=(-0.3, -0.5, 0.8),
    ambient_intensity=0.4
)
print("✅ Professional renderer ready!")


# Helper function
def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


@app.post("/api/nails/segment", response_model=NailResponse)
async def segment_nails(file: UploadFile = File(...)):
    raw = await file.read()

    # Check cache first
    cached_result = segmentation_cache.get(raw)
    if cached_result is not None:
        return cached_result

    # Cache miss - run inference
    img = read_image_from_bytes(raw)
    result = run_inference(img)

    nails = [
        NailInstance(
            id=n["id"],
            score=n["score"],
            polygon=n["polygon"],
        )
        for n in result["nails"]
    ]

    response = NailResponse(
        width=result["width"],
        height=result["height"],
        nails=nails,
    )

    # Cache the result
    segmentation_cache.set(raw, response)

    return response


@app.post("/api/nails/render-professional")
async def render_professional(
    file: UploadFile = File(...),
    material: str = Form("glossy_red"),
    custom_color: Optional[str] = Form(None),
    glossiness: float = Form(0.8),
    metallic: float = Form(0.0),
    intensity: float = Form(0.85)
):
    """
    Segment nails and apply professional photo-realistic rendering

    Args:
        file: Image file
        material: Material preset name (e.g., 'glossy_red', 'metallic_gold')
        custom_color: Optional hex color (e.g., '#FF0000') overrides preset
        glossiness: Glossiness value 0-1
        metallic: Metallic value 0-1
        intensity: Opacity/intensity 0-1

    Returns:
        Rendered image as JPEG with metadata headers
    """
    # Load image
    raw = await file.read()
    img = read_image_from_bytes(raw)

    # Convert to numpy array (BGR for OpenCV)
    frame = np.array(img)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Get model instance and run RF-DETR segmentation with caching
    model_instance = get_model()

    # Use torch.no_grad() for faster inference
    import torch
    with torch.no_grad():
        detections = model_instance.predict(img, threshold=0.2)

    # Get or create material
    presets = MaterialPresets.all_presets()
    if custom_color is not None:
        # Custom material from frontend parameters
        color_rgb = hex_to_rgb(custom_color)
        material_obj = NailMaterial(
            base_color=tuple(c / 255.0 for c in color_rgb),
            glossiness=glossiness,
            metallic=metallic,
            opacity=intensity,
            specular_intensity=1.0 + glossiness * 0.5
        )
    elif material in presets:
        # Use preset
        material_obj = presets[material]
    else:
        # Fallback to glossy red
        material_obj = presets["glossy_red"]

    # Render each nail
    result = frame.copy()
    nail_count = 1

    if detections.mask is not None:
        for idx in range(len(detections)):
            mask = detections.mask[idx]

            # Analyze geometry
            geometry = geometry_analyzer.analyze(mask, min_area=10)
            if geometry is None:
                continue

            # Render professionally
            result = professional_renderer.render_nail(result, geometry, material_obj)
            nail_count += 1

    # Convert back to RGB
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    from PIL import Image as PILImage
    result_pil = PILImage.fromarray(result_rgb)

    # Encode to JPEG
    img_byte_arr = io.BytesIO()
    result_pil.save(img_byte_arr, format='JPEG', quality=95)
    img_byte_arr.seek(0)

    return StreamingResponse(
        img_byte_arr,
        media_type="image/jpeg",
        headers={
            "X-Nail-Count": str(nail_count),
            "X-Material": material,
            "X-Glossiness": str(glossiness),
            "X-Metallic": str(metallic)
        }
    )


@app.get("/api/materials")
async def get_materials():
    """
    Get list of available material presets

    Returns:
        JSON with material preset information
    """
    presets = MaterialPresets.all_presets()
    materials = []

    for name, mat in presets.items():
        materials.append({
            "name": name,
            "display_name": name.replace('_', ' ').title(),
            "finish": mat.get_finish_type().value,
            "glossiness": mat.glossiness,
            "metallic": mat.metallic,
            "has_glitter": mat.has_glitter,
            "base_color_rgb": [int(c * 255) for c in mat.base_color]
        })

    return {"materials": materials}


@app.get("/api/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for monitoring performance

    Returns:
        JSON with cache statistics
    """
    return segmentation_cache.get_stats()


@app.post("/api/cache/clear")
async def clear_cache():
    """
    Clear the segmentation cache

    Returns:
        Success message
    """
    segmentation_cache.clear()
    return {"message": "Cache cleared successfully"}