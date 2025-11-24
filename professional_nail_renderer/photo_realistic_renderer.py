"""
Photo-Realistic Nail Renderer
Implements professional-quality nail polish rendering with:
- Phong/Blinn-Phong shading
- Curvature-aware lighting
- Specular highlights
- Edge feathering
- Multi-layer compositing
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import random

from .nail_geometry import NailGeometry
from .nail_material import NailMaterial


class PhotoRealisticNailRenderer:
    """
    Professional nail renderer using physically-based shading.
    Achieves results comparable to commercial AR applications like YouCam Nails.
    """

    def __init__(
        self,
        light_direction: Tuple[float, float, float] = (-0.5, -0.5, 0.8),
        light_color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        ambient_intensity: float = 0.3,
    ):
        """
        Initialize renderer with lighting configuration.

        Args:
            light_direction: 3D vector (x, y, z) indicating light direction
            light_color: RGB color of the light source (0-1 range)
            ambient_intensity: Ambient light strength (0-1)
        """
        # Normalize light direction
        light_dir = np.array(light_direction, dtype=np.float32)
        self.light_direction = light_dir / np.linalg.norm(light_dir)
        self.light_color = np.array(light_color, dtype=np.float32)
        self.ambient_intensity = ambient_intensity

        # View direction (camera is looking straight at the nail)
        self.view_direction = np.array([0, 0, 1], dtype=np.float32)

    def render_nail(
        self,
        image: np.ndarray,
        geometry: NailGeometry,
        material: NailMaterial,
        blend_mode: str = "normal"
    ) -> np.ndarray:
        """
        Render a single nail with photo-realistic materials.

        Args:
            image: Background image (H, W, 3) BGR format
            geometry: NailGeometry object with curvature info
            material: NailMaterial defining appearance
            blend_mode: How to blend with background ("normal", "multiply", "screen")

        Returns:
            Rendered image with nail polish applied
        """
        h, w = image.shape[:2]
        result = image.copy()

        # Get mask region
        mask = geometry.mask
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        # LAYER 1: Base Color
        base_layer = self._render_base_color(mask, material, (h, w))

        # LAYER 2: Curvature Shading (makes it look 3D)
        shading_layer = self._render_curvature_shading(geometry, material, (h, w))

        # LAYER 3: Specular Highlights (glossy reflections)
        specular_layer = self._render_specular_highlights(geometry, material, (h, w))

        # LAYER 4: Ambient Occlusion (shadows at edges)
        ao_layer = self._render_ambient_occlusion(geometry, material, (h, w))

        # LAYER 5: Edge Darkening
        edge_layer = self._render_edge_darkening(geometry, material, (h, w))

        # LAYER 6: Glitter/Texture (if applicable)
        if material.has_glitter:
            glitter_layer = self._render_glitter(geometry, material, (h, w))
        else:
            glitter_layer = np.zeros((h, w, 3), dtype=np.float32)

        # COMPOSITE ALL LAYERS
        # Work in linear color space for physically accurate blending
        linear_base = self._srgb_to_linear(base_layer)

        # Apply shading (multiply)
        shaded = linear_base * shading_layer

        # Apply ambient occlusion (multiply)
        shaded = shaded * ao_layer

        # Apply edge darkening (multiply)
        shaded = shaded * edge_layer

        # Add specular highlights (additive)
        shaded = shaded + specular_layer

        # Add glitter (additive with some blending)
        if material.has_glitter:
            shaded = shaded + glitter_layer * 0.6

        # Clamp and convert back to sRGB
        final_color = self._linear_to_srgb(np.clip(shaded, 0, 1))

        # EDGE FEATHERING
        # Create soft alpha mask for smooth blending
        alpha_mask = self._create_feathered_mask(mask, feather_radius=5)

        # Expand alpha to 3 channels
        alpha_3ch = np.stack([alpha_mask] * 3, axis=2)

        # Apply material opacity
        alpha_3ch = alpha_3ch * material.opacity

        # FINAL COMPOSITE
        # Blend nail color with original image
        result = result.astype(np.float32) / 255.0
        result = result * (1 - alpha_3ch) + final_color * alpha_3ch

        # Convert back to uint8
        result = (np.clip(result, 0, 1) * 255).astype(np.uint8)

        return result

    def _render_base_color(
        self,
        mask: np.ndarray,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """Render the base color layer"""
        h, w = image_shape
        base = np.zeros((h, w, 3), dtype=np.float32)

        # Fill with base color (BGR format for OpenCV)
        r, g, b = material.base_color
        base[:, :] = [b, g, r]  # Convert RGB to BGR

        # Mask out non-nail regions
        mask_3ch = np.stack([mask] * 3, axis=2)
        base = base * mask_3ch

        return base

    def _render_curvature_shading(
        self,
        geometry: NailGeometry,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Render curvature-aware shading using distance transform.
        Creates the 3D appearance without needing a full 3D mesh.
        """
        h, w = image_shape
        curvature = geometry.curvature_map

        if curvature.shape != (h, w):
            curvature = cv2.resize(curvature, (w, h), interpolation=cv2.INTER_LINEAR)

        # Create shading based on curvature
        # Center of nail is brightest, edges are darker
        # This simulates the curved surface catching light

        # Apply non-linear mapping for more pronounced effect
        # Higher glossiness = more pronounced shading
        shading_strength = 0.3 + material.glossiness * 0.5

        # Gamma correction for shading curve
        gamma = 1.5 - material.roughness * 0.5
        shading = np.power(curvature, gamma)

        # Map to lighting range (not completely black at edges)
        min_light = 1.0 - shading_strength
        shading = min_light + shading * shading_strength

        # Expand to 3 channels
        shading_3ch = np.stack([shading] * 3, axis=2)

        return shading_3ch.astype(np.float32)

    def _render_specular_highlights(
        self,
        geometry: NailGeometry,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Render specular highlights using Blinn-Phong model.
        Creates the characteristic "shine" of nail polish.
        """
        h, w = image_shape
        highlights = np.zeros((h, w, 3), dtype=np.float32)

        if material.glossiness < 0.1:
            # Matte materials have no specular
            return highlights

        # Use normal map if available, otherwise use curvature-based approximation
        if geometry.normal_map is not None:
            normals = geometry.normal_map
            if normals.shape[:2] != (h, w):
                normals = cv2.resize(normals, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            # Approximate normals from curvature
            normals = self._approximate_normals_from_curvature(geometry, (h, w))

        # Blinn-Phong: halfway vector between light and view
        halfway = self.light_direction + self.view_direction
        halfway = halfway / np.linalg.norm(halfway)

        # Compute N·H for each pixel
        # Reshape halfway for broadcasting
        halfway_reshaped = halfway.reshape(1, 1, 3)

        # Dot product
        n_dot_h = np.sum(normals * halfway_reshaped, axis=2)
        n_dot_h = np.clip(n_dot_h, 0, 1)

        # Specular power (shininess)
        # Glossier materials have sharper, brighter highlights
        shininess = 10 + material.glossiness * 200
        specular = np.power(n_dot_h, shininess)

        # Apply intensity
        specular = specular * material.specular_intensity

        # Apply mask
        mask = geometry.mask
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        specular = specular * mask

        # Color the highlight
        r, g, b = material.specular_tint
        highlights[:, :, 0] = specular * b  # B
        highlights[:, :, 1] = specular * g  # G
        highlights[:, :, 2] = specular * r  # R

        # For metallic materials, tint highlight with base color
        if material.metallic > 0.5:
            base_r, base_g, base_b = material.base_color
            highlights[:, :, 0] = highlights[:, :, 0] * (1 - material.metallic) + highlights[:, :, 0] * base_b * material.metallic
            highlights[:, :, 1] = highlights[:, :, 1] * (1 - material.metallic) + highlights[:, :, 1] * base_g * material.metallic
            highlights[:, :, 2] = highlights[:, :, 2] * (1 - material.metallic) + highlights[:, :, 2] * base_r * material.metallic

        return highlights

    def _render_ambient_occlusion(
        self,
        geometry: NailGeometry,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Render ambient occlusion (contact shadows at nail edges/cuticle).
        Adds depth by darkening areas where ambient light is blocked.
        """
        h, w = image_shape
        ao = np.ones((h, w), dtype=np.float32)

        # Invert distance transform to get edge proximity
        edge_dist = geometry.edge_distance_map
        if edge_dist.shape != (h, w):
            edge_dist = cv2.resize(edge_dist, (w, h), interpolation=cv2.INTER_LINEAR)

        # Edges are close to 0, center is close to 1
        # Invert to get AO (edges are dark)
        ao_map = 1.0 - (1.0 - edge_dist) * material.ao_intensity

        # Smooth the AO
        ao_map = cv2.GaussianBlur(ao_map, (0, 0), sigmaX=2)

        ao = ao_map

        # Expand to 3 channels
        ao_3ch = np.stack([ao] * 3, axis=2)

        return ao_3ch.astype(np.float32)

    def _render_edge_darkening(
        self,
        geometry: NailGeometry,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Darken nail edges for more realistic appearance.
        Simulates edge wear and depth.
        """
        h, w = image_shape
        edge = np.ones((h, w), dtype=np.float32)

        if material.edge_darkness == 0:
            return np.stack([edge] * 3, axis=2)

        # Use edge distance map
        edge_dist = geometry.edge_distance_map
        if edge_dist.shape != (h, w):
            edge_dist = cv2.resize(edge_dist, (w, h), interpolation=cv2.INTER_LINEAR)

        # Create gradient from edge to center
        # Normalize edge distance
        max_dist = edge_dist.max()
        if max_dist > 0:
            edge_normalized = edge_dist / max_dist
        else:
            edge_normalized = edge_dist

        # Apply edge width parameter
        edge_mask = 1.0 - np.clip(edge_normalized / material.edge_width, 0, 1)

        # Apply darkness
        darkening = 1.0 - edge_mask * material.edge_darkness

        # Smooth transition
        darkening = cv2.GaussianBlur(darkening, (0, 0), sigmaX=3)

        edge = darkening

        # Expand to 3 channels
        edge_3ch = np.stack([edge] * 3, axis=2)

        return edge_3ch.astype(np.float32)

    def _render_glitter(
        self,
        geometry: NailGeometry,
        material: NailMaterial,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Render glitter/sparkle particles.
        """
        h, w = image_shape
        glitter = np.zeros((h, w, 3), dtype=np.float32)

        # Get mask bounds
        mask = geometry.mask
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

        # Find nail pixels
        nail_coords = np.argwhere(mask > 0.5)

        if len(nail_coords) == 0:
            return glitter

        # Number of glitter particles
        num_particles = int(len(nail_coords) * material.glitter_density * 0.05)

        # Randomly select positions
        if num_particles > 0:
            random.seed(42)  # Consistent glitter pattern
            particle_indices = random.sample(range(len(nail_coords)), min(num_particles, len(nail_coords)))
            particle_coords = nail_coords[particle_indices]

            # Color
            r, g, b = material.glitter_color

            for y, x in particle_coords:
                # Random brightness
                brightness = random.uniform(0.5, 1.0)

                # Draw glitter particle
                size = int(material.glitter_size)
                cv2.circle(
                    glitter,
                    (x, y),
                    size,
                    (b * brightness, g * brightness, r * brightness),
                    -1,
                    lineType=cv2.LINE_AA
                )

        # Blur slightly for softer glitter
        glitter = cv2.GaussianBlur(glitter, (0, 0), sigmaX=0.5)

        return glitter

    def _create_feathered_mask(self, mask: np.ndarray, feather_radius: int = 5) -> np.ndarray:
        """
        Create a soft-edged mask for smooth blending.
        """
        # Ensure float format
        mask_float = mask.astype(np.float32)

        # Apply Gaussian blur to edges
        feathered = cv2.GaussianBlur(mask_float, (0, 0), sigmaX=feather_radius)

        return feathered

    def _approximate_normals_from_curvature(
        self,
        geometry: NailGeometry,
        image_shape: Tuple[int, int]
    ) -> np.ndarray:
        """Approximate surface normals from distance transform"""
        h, w = image_shape
        curvature = geometry.curvature_map

        if curvature.shape != (h, w):
            curvature = cv2.resize(curvature, (w, h), interpolation=cv2.INTER_LINEAR)

        # Compute gradients
        grad_x = cv2.Sobel(curvature, cv2.CV_32F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(curvature, cv2.CV_32F, 0, 1, ksize=5)

        # Create normal vectors
        normals = np.zeros((h, w, 3), dtype=np.float32)
        normals[:, :, 0] = -grad_x
        normals[:, :, 1] = -grad_y
        normals[:, :, 2] = 1.0

        # Normalize
        norm = np.linalg.norm(normals, axis=2, keepdims=True)
        norm = np.maximum(norm, 1e-8)
        normals = normals / norm

        return normals

    def _srgb_to_linear(self, color: np.ndarray) -> np.ndarray:
        """Convert sRGB to linear color space"""
        linear = np.where(
            color <= 0.04045,
            color / 12.92,
            np.power((color + 0.055) / 1.055, 2.4)
        )
        return linear

    def _linear_to_srgb(self, color: np.ndarray) -> np.ndarray:
        """Convert linear to sRGB color space"""
        srgb = np.where(
            color <= 0.0031308,
            color * 12.92,
            1.055 * np.power(color, 1/2.4) - 0.055
        )
        return srgb

    def render_multiple_nails(
        self,
        image: np.ndarray,
        geometries: list,
        materials: list,
    ) -> np.ndarray:
        """
        Render multiple nails on the same image.

        Args:
            image: Background image
            geometries: List of NailGeometry objects
            materials: List of NailMaterial objects (one per nail)

        Returns:
            Image with all nails rendered
        """
        result = image.copy()

        # Render each nail
        for geometry, material in zip(geometries, materials):
            result = self.render_nail(result, geometry, material)

        return result
