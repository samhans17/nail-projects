"""
Before/After Comparison Tool
Compare basic rendering vs professional photo-realistic rendering
"""

import torch
import cv2
import numpy as np
import time
import argparse
import sys
import os

# Add professional renderer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'professional_nail_renderer'))

from professional_nail_renderer.nail_geometry import NailGeometryAnalyzer
from professional_nail_renderer.nail_material import MaterialPresets
from professional_nail_renderer.photo_realistic_renderer import PhotoRealisticNailRenderer

MODEL_PATH = "./pytorch_mobile_models/rfdetr_nails.pt"


class BasicRenderer:
    """Original basic rendering for comparison"""

    def __init__(self, color=(0, 0, 255)):
        self.color = color

    def render(self, frame, masks, scores, confidence_threshold=0.2):
        """Basic flat color overlay"""
        overlay = frame.copy()
        num_detections = masks.shape[0]
        frame_h, frame_w = frame.shape[:2]

        if scores is not None:
            class_scores = scores.squeeze(0).numpy()
            confidence_scores = class_scores[:, 1]
        else:
            confidence_scores = None

        # Filter valid detections
        if confidence_scores is not None:
            valid_indices = np.where(confidence_scores > confidence_threshold)[0]
        else:
            valid_indices = range(min(10, num_detections))

        detected = 0
        for idx in valid_indices:
            mask = masks[idx]

            # Resize mask
            mask_resized = cv2.resize(
                mask,
                (frame_w, frame_h),
                interpolation=cv2.INTER_NEAREST
            )

            # Threshold
            binary_mask = (mask_resized > 0.5).astype(np.uint8)

            if np.sum(binary_mask) < 100:
                continue

            detected += 1

            # Create colored mask
            colored_mask = np.zeros_like(frame)
            colored_mask[binary_mask == 1] = self.color

            # Simple blend
            overlay = cv2.addWeighted(overlay, 1, colored_mask, 0.4, 0)

            # Draw contours
            contours, _ = cv2.findContours(
                binary_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            if contours:
                cv2.drawContours(overlay, contours, -1, self.color, 2)

        return overlay, detected


class ProfessionalRenderer:
    """Professional photo-realistic rendering"""

    def __init__(self, material_preset="glossy_red"):
        self.geometry_analyzer = NailGeometryAnalyzer()
        self.renderer = PhotoRealisticNailRenderer(
            light_direction=(-0.3, -0.5, 0.8),
            ambient_intensity=0.4
        )
        presets = MaterialPresets.all_presets()
        self.material = presets.get(material_preset, presets["glossy_red"])

    def render(self, frame, masks, scores, confidence_threshold=0.2):
        """Professional rendering with all effects"""
        num_detections = masks.shape[0]
        frame_h, frame_w = frame.shape[:2]

        if scores is not None:
            class_scores = scores.squeeze(0).numpy()
            confidence_scores = class_scores[:, 1]
        else:
            confidence_scores = None

        # Filter valid detections
        if confidence_scores is not None:
            valid_indices = np.where(confidence_scores > confidence_threshold)[0]
        else:
            valid_indices = range(min(10, num_detections))

        geometries = []
        for idx in valid_indices:
            mask = masks[idx]

            # Resize mask
            mask_resized = cv2.resize(
                mask,
                (frame_w, frame_h),
                interpolation=cv2.INTER_LINEAR
            )

            # Threshold
            binary_mask = (mask_resized > 0.5).astype(np.uint8)

            if np.sum(binary_mask) < 100:
                continue

            # Analyze geometry
            geometry = self.geometry_analyzer.analyze(binary_mask, min_area=100)
            if geometry is not None:
                geometries.append(geometry)

        # Render all nails
        result = frame.copy()
        for geometry in geometries:
            result = self.renderer.render_nail(result, geometry, self.material)

        return result, len(geometries)


def create_comparison_grid(image, basic_result, professional_result):
    """Create a side-by-side comparison grid"""
    h, w = image.shape[:2]

    # Create grid
    grid = np.zeros((h, w * 3, 3), dtype=np.uint8)

    # Original
    grid[:, 0:w] = image

    # Basic
    grid[:, w:w*2] = basic_result

    # Professional
    grid[:, w*2:w*3] = professional_result

    # Add labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    thickness = 2
    color = (255, 255, 255)

    cv2.putText(grid, "ORIGINAL", (10, 40), font, font_scale, color, thickness, cv2.LINE_AA)
    cv2.putText(grid, "BASIC RENDERING", (w + 10, 40), font, font_scale, color, thickness, cv2.LINE_AA)
    cv2.putText(grid, "PROFESSIONAL RENDERING", (w*2 + 10, 40), font, font_scale, color, thickness, cv2.LINE_AA)

    # Add feature labels for professional side
    features = [
        "✓ Curvature shading",
        "✓ Specular highlights",
        "✓ Edge feathering",
        "✓ Ambient occlusion",
        "✓ PBR materials"
    ]

    y_offset = h - 150
    for i, feature in enumerate(features):
        cv2.putText(
            grid, feature,
            (w*2 + 10, y_offset + i * 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            (0, 255, 0), 1, cv2.LINE_AA
        )

    return grid


def main():
    parser = argparse.ArgumentParser(description='Compare basic vs professional rendering')
    parser.add_argument('--model', type=str, default=MODEL_PATH, help='Model path')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--image', type=str, help='Use image file instead of camera')
    parser.add_argument('--threshold', type=float, default=0.2, help='Confidence threshold')
    parser.add_argument('--material', type=str, default='glossy_red', help='Material preset')
    parser.add_argument('--output', type=str, help='Save comparison to file')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("BEFORE/AFTER COMPARISON: Basic vs Professional Rendering")
    print("="*80 + "\n")

    # Load model
    print(f"📦 Loading model...")
    model = torch.jit.load(args.model)
    model.eval()
    torch.set_grad_enabled(False)
    print("✅ Model loaded")

    # Initialize renderers
    print("🎨 Initializing renderers...")
    basic = BasicRenderer(color=(0, 0, 255))  # Red
    professional = ProfessionalRenderer(material_preset=args.material)
    print("✅ Renderers initialized")

    # Get input
    if args.image:
        print(f"📷 Loading image: {args.image}")
        frame = cv2.imread(args.image)
        if frame is None:
            print(f"❌ Failed to load image")
            return 1
        single_frame_mode = True
    else:
        print(f"📷 Opening camera {args.camera}...")
        cap = cv2.VideoCapture(args.camera)
        if not cap.isOpened():
            print("❌ Failed to open camera")
            return 1
        print("✅ Camera opened")
        single_frame_mode = False

    print("\n" + "="*80)
    print("CONTROLS:")
    print("  'q'/'ESC' - Quit")
    print("  's'       - Save comparison screenshot")
    print("  'SPACE'   - Pause/Resume (camera mode)")
    print("="*80 + "\n")

    paused = False

    try:
        while True:
            if not single_frame_mode:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        break
            else:
                # Single frame mode
                pass

            # Preprocess
            resized = cv2.resize(frame, (432, 432), interpolation=cv2.INTER_AREA)
            rgb_normalized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
            img_array = np.transpose(rgb_normalized, (2, 0, 1))
            img_tensor = torch.from_numpy(img_array).unsqueeze(0)

            # Run inference
            print("⚙️  Running inference...")
            start_inference = time.time()
            outputs = model(img_tensor)
            inference_time = (time.time() - start_inference) * 1000

            if isinstance(outputs, tuple):
                boxes = outputs[0]
                scores = outputs[1]
                mask_tensor = outputs[2]
            else:
                mask_tensor = outputs
                scores = None

            masks = mask_tensor.squeeze(0).numpy()
            print(f"✅ Inference: {inference_time:.1f}ms")

            # Basic rendering
            print("🎨 Basic rendering...")
            start_basic = time.time()
            basic_result, basic_count = basic.render(frame, masks, scores, args.threshold)
            basic_time = (time.time() - start_basic) * 1000
            print(f"✅ Basic: {basic_time:.1f}ms ({basic_count} nails)")

            # Professional rendering
            print("✨ Professional rendering...")
            start_pro = time.time()
            professional_result, pro_count = professional.render(frame, masks, scores, args.threshold)
            professional_time = (time.time() - start_pro) * 1000
            print(f"✅ Professional: {professional_time:.1f}ms ({pro_count} nails)")

            # Create comparison
            comparison = create_comparison_grid(frame, basic_result, professional_result)

            # Add timing info
            timing_text = [
                f"Inference: {inference_time:.1f}ms",
                f"Basic render: {basic_time:.1f}ms",
                f"Pro render: {professional_time:.1f}ms",
                f"Speedup: {professional_time/basic_time:.1f}x slower (worth it!)"
            ]

            y = comparison.shape[0] - 100
            for text in timing_text:
                cv2.putText(
                    comparison, text,
                    (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 0), 2, cv2.LINE_AA
                )
                y += 25

            # Display
            # Resize for display if too large
            display_h, display_w = comparison.shape[:2]
            max_width = 1920
            if display_w > max_width:
                scale = max_width / display_w
                new_w = int(display_w * scale)
                new_h = int(display_h * scale)
                comparison_display = cv2.resize(comparison, (new_w, new_h))
            else:
                comparison_display = comparison

            cv2.imshow('Comparison: Basic vs Professional', comparison_display)

            # Save if requested
            if args.output:
                cv2.imwrite(args.output, comparison)
                print(f"📸 Saved comparison to: {args.output}")
                if single_frame_mode:
                    break

            key = cv2.waitKey(1 if not single_frame_mode else 0) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord('s'):
                filename = f"comparison_{int(time.time())}.jpg"
                cv2.imwrite(filename, comparison)
                print(f"📸 Saved: {filename}")
            elif key == ord(' ') and not single_frame_mode:
                paused = not paused
                print("⏸️  PAUSED" if paused else "▶️  RESUMED")

            if single_frame_mode:
                break

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")

    finally:
        if not single_frame_mode:
            cap.release()
        cv2.destroyAllWindows()

        print("\n" + "="*80)
        print("COMPARISON COMPLETE")
        print("="*80)
        print("\nKEY DIFFERENCES:")
        print("  BASIC:        Flat color overlay, hard edges, no depth")
        print("  PROFESSIONAL: 3D curvature, glossy highlights, soft edges, realistic materials")
        print("\n" + "="*80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
