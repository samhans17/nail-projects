"""
Nail Material System
Defines material properties for photo-realistic nail polish rendering
"""

import numpy as np
from dataclasses import dataclass
from typing import Tuple, Optional
from enum import Enum


class MaterialFinish(Enum):
    """Types of nail polish finishes"""
    GLOSSY = "glossy"
    MATTE = "matte"
    METALLIC = "metallic"
    GLITTER = "glitter"
    CHROME = "chrome"
    SATIN = "satin"


@dataclass
class NailMaterial:
    """
    Material properties for realistic nail polish rendering.
    Based on physically-based rendering (PBR) principles.
    """
    # Base color (RGB, values 0-255 or 0-1)
    base_color: Tuple[float, float, float]

    # Material properties (all in range 0-1)
    glossiness: float = 0.8  # 0=matte, 1=mirror-like
    metallic: float = 0.0    # 0=dielectric, 1=metallic
    roughness: float = 0.2   # 0=smooth, 1=rough (inverse of glossiness)

    # Advanced properties
    opacity: float = 0.85           # 0=transparent, 1=opaque
    specular_intensity: float = 1.0 # Brightness of highlights
    specular_tint: Optional[Tuple[float, float, float]] = None  # Color of highlights

    # Texture properties (for glitter, etc.)
    has_glitter: bool = False
    glitter_density: float = 0.0     # 0-1
    glitter_size: float = 2.0        # pixels
    glitter_color: Optional[Tuple[float, float, float]] = None

    # Edge properties
    edge_darkness: float = 0.3   # How much darker edges should be (0=no darkening)
    edge_width: float = 0.15     # Width of edge darkening (0-1, relative to nail)

    # Ambient occlusion
    ao_intensity: float = 0.4    # Shadow intensity at edges/cuticle

    def __post_init__(self):
        """Validate and normalize values"""
        # Ensure base_color is in 0-1 range
        if max(self.base_color) > 1.0:
            self.base_color = tuple(c / 255.0 for c in self.base_color)

        # Compute roughness from glossiness if not set explicitly
        if self.roughness == 0.2 and self.glossiness != 0.8:
            self.roughness = 1.0 - self.glossiness

        # Default specular tint to slightly bluish white (realistic for polish)
        if self.specular_tint is None:
            self.specular_tint = (1.0, 1.0, 1.0)

        # Default glitter color to gold/silver
        if self.glitter_color is None:
            self.glitter_color = (1.0, 0.9, 0.7)  # Gold

    def get_finish_type(self) -> MaterialFinish:
        """Infer the finish type from material properties"""
        if self.has_glitter:
            return MaterialFinish.GLITTER
        elif self.metallic > 0.7:
            if self.roughness < 0.1:
                return MaterialFinish.CHROME
            else:
                return MaterialFinish.METALLIC
        elif self.glossiness > 0.7:
            return MaterialFinish.GLOSSY
        elif self.glossiness < 0.3:
            return MaterialFinish.MATTE
        else:
            return MaterialFinish.SATIN

    def to_linear_color(self) -> Tuple[float, float, float]:
        """Convert sRGB color to linear space for proper lighting calculations"""
        def srgb_to_linear(c):
            if c <= 0.04045:
                return c / 12.92
            else:
                return ((c + 0.055) / 1.055) ** 2.4

        return tuple(srgb_to_linear(c) for c in self.base_color)

    def to_srgb_color(self, linear_color: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Convert linear color back to sRGB for display"""
        def linear_to_srgb(c):
            if c <= 0.0031308:
                return c * 12.92
            else:
                return 1.055 * (c ** (1/2.4)) - 0.055

        return tuple(np.clip(linear_to_srgb(c), 0, 1) for c in linear_color)


class MaterialPresets:
    """Pre-defined materials for common nail polish types"""

    @staticmethod
    def glossy_red() -> NailMaterial:
        """Classic glossy red nail polish"""
        return NailMaterial(
            base_color=(0.8, 0.1, 0.1),
            glossiness=0.9,
            metallic=0.0,
            roughness=0.1,
            opacity=0.95,
            specular_intensity=1.2,
            edge_darkness=0.35,
        )

    @staticmethod
    def glossy_nude() -> NailMaterial:
        """Natural nude/beige polish"""
        return NailMaterial(
            base_color=(0.92, 0.78, 0.68),
            glossiness=0.85,
            metallic=0.0,
            roughness=0.15,
            opacity=0.75,
            specular_intensity=0.9,
            edge_darkness=0.25,
        )

    @staticmethod
    def matte_black() -> NailMaterial:
        """Matte black polish"""
        return NailMaterial(
            base_color=(0.15, 0.15, 0.15),
            glossiness=0.2,
            metallic=0.0,
            roughness=0.8,
            opacity=0.98,
            specular_intensity=0.3,
            edge_darkness=0.2,
        )

    @staticmethod
    def matte_pink() -> NailMaterial:
        """Matte pink polish"""
        return NailMaterial(
            base_color=(0.95, 0.6, 0.7),
            glossiness=0.25,
            metallic=0.0,
            roughness=0.75,
            opacity=0.85,
            specular_intensity=0.4,
            edge_darkness=0.3,
        )

    @staticmethod
    def metallic_gold() -> NailMaterial:
        """Metallic gold polish"""
        return NailMaterial(
            base_color=(0.85, 0.65, 0.13),
            glossiness=0.75,
            metallic=0.9,
            roughness=0.25,
            opacity=0.95,
            specular_intensity=1.5,
            specular_tint=(1.0, 0.9, 0.6),
            edge_darkness=0.4,
        )

    @staticmethod
    def metallic_silver() -> NailMaterial:
        """Metallic silver/chrome polish"""
        return NailMaterial(
            base_color=(0.75, 0.75, 0.75),
            glossiness=0.85,
            metallic=0.95,
            roughness=0.15,
            opacity=0.98,
            specular_intensity=1.8,
            specular_tint=(0.95, 0.95, 1.0),
            edge_darkness=0.45,
        )

    @staticmethod
    def chrome_mirror() -> NailMaterial:
        """Ultra-reflective chrome finish"""
        return NailMaterial(
            base_color=(0.85, 0.85, 0.9),
            glossiness=0.98,
            metallic=0.98,
            roughness=0.02,
            opacity=0.99,
            specular_intensity=2.5,
            specular_tint=(0.9, 0.95, 1.0),
            edge_darkness=0.5,
        )

    @staticmethod
    def glitter_pink() -> NailMaterial:
        """Pink with gold glitter"""
        return NailMaterial(
            base_color=(0.95, 0.5, 0.65),
            glossiness=0.8,
            metallic=0.1,
            roughness=0.2,
            opacity=0.9,
            specular_intensity=1.0,
            has_glitter=True,
            glitter_density=0.3,
            glitter_size=2.5,
            glitter_color=(1.0, 0.84, 0.0),
            edge_darkness=0.35,
        )

    @staticmethod
    def glitter_silver() -> NailMaterial:
        """Clear with silver glitter"""
        return NailMaterial(
            base_color=(0.95, 0.92, 0.95),
            glossiness=0.85,
            metallic=0.2,
            roughness=0.15,
            opacity=0.7,
            specular_intensity=1.2,
            has_glitter=True,
            glitter_density=0.5,
            glitter_size=3.0,
            glitter_color=(0.9, 0.9, 0.95),
            edge_darkness=0.3,
        )

    @staticmethod
    def holographic() -> NailMaterial:
        """Holographic/iridescent finish"""
        return NailMaterial(
            base_color=(0.85, 0.75, 0.95),
            glossiness=0.95,
            metallic=0.6,
            roughness=0.05,
            opacity=0.92,
            specular_intensity=2.0,
            specular_tint=(0.9, 0.8, 1.0),
            has_glitter=True,
            glitter_density=0.6,
            glitter_size=1.5,
            glitter_color=(1.0, 0.9, 1.0),
            edge_darkness=0.4,
        )

    @staticmethod
    def satin_burgundy() -> NailMaterial:
        """Satin burgundy (between matte and glossy)"""
        return NailMaterial(
            base_color=(0.45, 0.1, 0.15),
            glossiness=0.5,
            metallic=0.0,
            roughness=0.5,
            opacity=0.95,
            specular_intensity=0.7,
            edge_darkness=0.35,
        )

    @staticmethod
    def custom(
        color: Tuple[int, int, int],
        finish: MaterialFinish = MaterialFinish.GLOSSY
    ) -> NailMaterial:
        """
        Create a custom material with specified color and finish.

        Args:
            color: RGB color tuple (0-255)
            finish: MaterialFinish enum value

        Returns:
            NailMaterial configured for the specified finish
        """
        # Normalize color
        normalized_color = tuple(c / 255.0 for c in color)

        # Base material properties by finish type
        finish_properties = {
            MaterialFinish.GLOSSY: {
                "glossiness": 0.9,
                "metallic": 0.0,
                "roughness": 0.1,
                "specular_intensity": 1.2,
            },
            MaterialFinish.MATTE: {
                "glossiness": 0.2,
                "metallic": 0.0,
                "roughness": 0.8,
                "specular_intensity": 0.3,
            },
            MaterialFinish.METALLIC: {
                "glossiness": 0.75,
                "metallic": 0.85,
                "roughness": 0.25,
                "specular_intensity": 1.5,
            },
            MaterialFinish.CHROME: {
                "glossiness": 0.98,
                "metallic": 0.95,
                "roughness": 0.02,
                "specular_intensity": 2.5,
            },
            MaterialFinish.SATIN: {
                "glossiness": 0.5,
                "metallic": 0.0,
                "roughness": 0.5,
                "specular_intensity": 0.7,
            },
            MaterialFinish.GLITTER: {
                "glossiness": 0.8,
                "metallic": 0.2,
                "roughness": 0.2,
                "specular_intensity": 1.0,
                "has_glitter": True,
                "glitter_density": 0.4,
            },
        }

        props = finish_properties[finish]
        return NailMaterial(base_color=normalized_color, **props)

    @staticmethod
    def all_presets() -> dict:
        """Get all preset materials as a dictionary"""
        return {
            "glossy_red": MaterialPresets.glossy_red(),
            "glossy_nude": MaterialPresets.glossy_nude(),
            "matte_black": MaterialPresets.matte_black(),
            "matte_pink": MaterialPresets.matte_pink(),
            "metallic_gold": MaterialPresets.metallic_gold(),
            "metallic_silver": MaterialPresets.metallic_silver(),
            "chrome_mirror": MaterialPresets.chrome_mirror(),
            "glitter_pink": MaterialPresets.glitter_pink(),
            "glitter_silver": MaterialPresets.glitter_silver(),
            "holographic": MaterialPresets.holographic(),
            "satin_burgundy": MaterialPresets.satin_burgundy(),
        }
