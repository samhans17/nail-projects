"""
Professional Nail Renderer Package
Photo-realistic nail polish rendering for AR applications
"""

from .nail_geometry import NailGeometry, NailGeometryAnalyzer, analyze_all_nails
from .nail_material import (
    NailMaterial,
    MaterialFinish,
    MaterialPresets
)
from .photo_realistic_renderer import PhotoRealisticNailRenderer

__version__ = "1.0.0"

__all__ = [
    "NailGeometry",
    "NailGeometryAnalyzer",
    "analyze_all_nails",
    "NailMaterial",
    "MaterialFinish",
    "MaterialPresets",
    "PhotoRealisticNailRenderer",
]
