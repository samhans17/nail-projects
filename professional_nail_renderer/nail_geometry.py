"""
Nail Geometry Analyzer
Extracts curvature information from segmentation masks for realistic rendering
"""

import cv2
import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class NailGeometry:
    """Geometric properties of a nail extracted from mask"""
    contour: np.ndarray  # Main contour points
    center: Tuple[int, int]  # Center point (cx, cy)
    orientation_angle: float  # Nail orientation in degrees
    length: float  # Length along major axis
    width: float  # Width along minor axis
    curvature_map: np.ndarray  # Distance transform for shading
    edge_distance_map: np.ndarray  # Distance from edges
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    mask: np.ndarray  # Binary mask

    # Advanced properties for lighting
    normal_map: Optional[np.ndarray] = None  # Surface normals (for advanced shading)
    highlight_point: Optional[Tuple[int, int]] = None  # Where to place specular highlight


class NailGeometryAnalyzer:
    """Analyzes nail mask to extract geometric properties for realistic rendering"""

    def __init__(self):
        pass

    def analyze(self, mask: np.ndarray, min_area: float = 100.0) -> Optional[NailGeometry]:
        """
        Analyze a binary mask to extract nail geometry.

        Args:
            mask: Binary mask (H, W) with values 0 or 1
            min_area: Minimum contour area to consider

        Returns:
            NailGeometry object or None if no valid nail found
        """
        # Ensure uint8 format
        binary_mask = (mask > 0.5).astype(np.uint8)

        # Find contours
        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        # Get largest contour
        main_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(main_contour)

        if area < min_area:
            return None

        # Calculate center of mass
        M = cv2.moments(main_contour)
        if M["m00"] == 0:
            return None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        # Fit ellipse to get orientation and dimensions
        if len(main_contour) >= 5:
            ellipse = cv2.fitEllipse(main_contour)
            (ex, ey), (minor_axis, major_axis), angle = ellipse
            orientation_angle = angle
            length = major_axis
            width = minor_axis
        else:
            # Fallback for small contours
            x, y, w, h = cv2.boundingRect(main_contour)
            orientation_angle = 0
            length = max(w, h)
            width = min(w, h)

        # Get bounding box
        bbox = cv2.boundingRect(main_contour)

        # Compute distance transform for curvature-aware shading
        # This creates a map where center is brightest, edges are darkest
        curvature_map = cv2.distanceTransform(
            binary_mask,
            cv2.DIST_L2,
            5
        )

        # Normalize curvature map
        if curvature_map.max() > 0:
            curvature_map = curvature_map / curvature_map.max()

        # Compute edge distance map (inverted distance transform)
        # Useful for edge feathering
        edge_distance_map = curvature_map.copy()

        # Calculate highlight point (slightly offset from center along major axis)
        # This simulates where light would reflect most strongly
        highlight_point = self._calculate_highlight_point(
            cx, cy, orientation_angle, length * 0.15
        )

        # Generate simple normal map (gradient-based)
        normal_map = self._generate_normal_map(curvature_map, binary_mask)

        return NailGeometry(
            contour=main_contour,
            center=(cx, cy),
            orientation_angle=orientation_angle,
            length=length,
            width=width,
            curvature_map=curvature_map,
            edge_distance_map=edge_distance_map,
            bbox=bbox,
            mask=binary_mask,
            normal_map=normal_map,
            highlight_point=highlight_point
        )

    def _calculate_highlight_point(
        self,
        cx: int,
        cy: int,
        angle: float,
        offset: float
    ) -> Tuple[int, int]:
        """Calculate where specular highlight should appear"""
        # Convert angle to radians
        angle_rad = np.deg2rad(angle)

        # Offset point along major axis (simulating light from top-left)
        # Adjust angle by -45 degrees for more natural lighting
        light_angle = angle_rad - np.pi / 4

        hx = int(cx + offset * np.cos(light_angle))
        hy = int(cy + offset * np.sin(light_angle))

        return (hx, hy)

    def _generate_normal_map(
        self,
        curvature_map: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        Generate a simple normal map from the curvature/distance transform.
        Normal map encodes surface orientation for lighting calculations.

        Returns:
            Normal map as (H, W, 3) float array with values in [-1, 1]
        """
        # Compute gradients (represents surface slope)
        grad_x = cv2.Sobel(curvature_map, cv2.CV_32F, 1, 0, ksize=5)
        grad_y = cv2.Sobel(curvature_map, cv2.CV_32F, 0, 1, ksize=5)

        # Create normal vectors
        # For a curved surface, normals point outward
        # Z component is positive (pointing toward viewer)
        h, w = curvature_map.shape
        normal_map = np.zeros((h, w, 3), dtype=np.float32)

        # X and Y from gradients (inverted for proper lighting)
        normal_map[:, :, 0] = -grad_x
        normal_map[:, :, 1] = -grad_y

        # Z component (pointing out of screen)
        # Higher curvature = more perpendicular to viewer
        normal_map[:, :, 2] = 1.0 + curvature_map * 2.0

        # Normalize vectors
        norm = np.linalg.norm(normal_map, axis=2, keepdims=True)
        norm = np.maximum(norm, 1e-8)  # Avoid division by zero
        normal_map = normal_map / norm

        # Mask out non-nail regions
        normal_map[mask == 0] = [0, 0, 0]

        return normal_map

    def visualize_geometry(self, geometry: NailGeometry, image_shape: Tuple[int, int]) -> np.ndarray:
        """
        Visualize the extracted geometry for debugging.

        Args:
            geometry: NailGeometry object
            image_shape: (height, width) for output image

        Returns:
            BGR image showing geometry visualization
        """
        h, w = image_shape
        vis = np.zeros((h, w, 3), dtype=np.uint8)

        # Draw curvature map as heatmap
        curvature_colored = cv2.applyColorMap(
            (geometry.curvature_map * 255).astype(np.uint8),
            cv2.COLORMAP_JET
        )
        vis = cv2.addWeighted(vis, 0, curvature_colored, 1, 0)

        # Draw contour
        cv2.drawContours(vis, [geometry.contour], -1, (255, 255, 255), 2)

        # Draw center
        cv2.circle(vis, geometry.center, 5, (0, 255, 0), -1)

        # Draw highlight point
        if geometry.highlight_point:
            cv2.circle(vis, geometry.highlight_point, 8, (255, 255, 0), -1)

        # Draw orientation axis
        angle_rad = np.deg2rad(geometry.orientation_angle)
        end_x = int(geometry.center[0] + geometry.length * 0.5 * np.cos(angle_rad))
        end_y = int(geometry.center[1] + geometry.length * 0.5 * np.sin(angle_rad))
        cv2.arrowedLine(vis, geometry.center, (end_x, end_y), (0, 255, 255), 2)

        # Add text info
        cv2.putText(
            vis,
            f"Angle: {geometry.orientation_angle:.1f}deg",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.putText(
            vis,
            f"Size: {geometry.length:.0f}x{geometry.width:.0f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        return vis


# Utility function for batch processing
def analyze_all_nails(masks: np.ndarray, min_area: float = 100.0) -> Dict[int, NailGeometry]:
    """
    Analyze multiple nail masks.

    Args:
        masks: Array of shape (N, H, W) with N nail masks
        min_area: Minimum area threshold

    Returns:
        Dictionary mapping nail index to NailGeometry
    """
    analyzer = NailGeometryAnalyzer()
    geometries = {}

    for i, mask in enumerate(masks):
        geom = analyzer.analyze(mask, min_area)
        if geom is not None:
            geometries[i] = geom

    return geometries
