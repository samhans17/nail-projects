"""
Professional Live Inference with Photo-Realistic Nail Rendering
Integrates RT-DETR segmentation with professional rendering system

Supports both GUI and headless modes:
- GUI mode: Interactive window with live preview
- Headless mode: Saves frames to disk (for SSH/remote servers)
"""

import torch
import cv2
import numpy as np
from PIL import Image
import time
import argparse
from collections import deque
import sys
import os
from pathlib import Path

# Add professional renderer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'professional_nail_renderer'))

from professional_nail_renderer.nail_geometry import NailGeometryAnalyzer
from professional_nail_renderer.nail_material import NailMaterial, MaterialPresets, MaterialFinish
from professional_nail_renderer.photo_realistic_renderer import PhotoRealisticNailRenderer

MODEL_PATH = "./pytorch_mobile_models/rfdetr_nails.pt"


def detect_display():
    """
    Detect if display/GUI is available.
    Returns True if cv2.imshow() will work, False for headless environment.
    """
    try:
        # Try to create and destroy a test window
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imshow('__test__', test_img)
        cv2.waitKey(1)
        cv2.destroyWindow('__test__')
        cv2.waitKey(1)
        return True
    except:
        return False


class ProfessionalNailAR:
    def __init__(
        self,
        model_path,
        confidence_threshold=0.2,
        material_preset="glossy_red"
    ):
        """Initialize professional nail AR system"""
        print(f"📦 Loading PyTorch Mobile model from: {model_path}")

        try:
            self.model = torch.jit.load(model_path)
            self.model.eval()
            torch.set_num_threads(4)
            torch.set_grad_enabled(False)
            print("✅ Model loaded")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

        self.confidence_threshold = confidence_threshold
        self.input_size = 432

        # Initialize professional rendering system
        print("🎨 Initializing professional renderer...")
        self.geometry_analyzer = NailGeometryAnalyzer()
        self.renderer = PhotoRealisticNailRenderer(
            light_direction=(-0.3, -0.5, 0.8),  # Light from top-left
            ambient_intensity=0.4
        )
        print("✅ Renderer initialized")

        # Load material presets
        self.presets = MaterialPresets.all_presets()
        self.preset_names = list(self.presets.keys())
        self.current_preset_idx = 0

        # Set initial material
        if material_preset in self.presets:
            self.current_material = self.presets[material_preset]
            self.current_preset_idx = self.preset_names.index(material_preset)
        else:
            self.current_material = self.presets["glossy_red"]

        print(f"💅 Material: {self.preset_names[self.current_preset_idx]}")

        # Warmup
        print("🔥 Warming up model...")
        dummy = torch.randn(1, 3, 432, 432)
        for _ in range(3):
            _ = self.model(dummy)
        print("✅ Model warmed up")

        # Performance tracking
        self.inference_times = deque(maxlen=30)
        self.render_times = deque(maxlen=30)

        # Frame skipping
        self.frame_skip = 1
        self.frame_count = 0
        self.last_result = None

    def preprocess(self, frame):
        """Preprocess frame for model input"""
        resized = cv2.resize(frame, (432, 432), interpolation=cv2.INTER_AREA)
        rgb_normalized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        img_array = np.transpose(rgb_normalized, (2, 0, 1))
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)
        return img_tensor

    def inference(self, img_tensor):
        """Run inference"""
        start_time = time.time()
        outputs = self.model(img_tensor)
        inference_time = (time.time() - start_time) * 1000
        self.inference_times.append(inference_time)

        if isinstance(outputs, tuple):
            boxes = outputs[0]
            scores = outputs[1]
            mask_tensor = outputs[2]
        else:
            mask_tensor = outputs
            scores = None

        return mask_tensor, scores, inference_time

    def render_professional(self, mask_tensor, scores, original_frame):
        """
        Professional rendering pipeline with photo-realistic materials
        """
        start_time = time.time()

        # Get masks
        masks = mask_tensor.squeeze(0).numpy()  # [200, 108, 108]
        num_detections = masks.shape[0]
        frame_h, frame_w = original_frame.shape[:2]

        # Get confidence scores
        if scores is not None:
            class_scores = scores.squeeze(0).numpy()
            confidence_scores = class_scores[:, 1]
        else:
            confidence_scores = None

        # Filter valid detections
        if confidence_scores is not None:
            valid_indices = np.where(confidence_scores > self.confidence_threshold)[0]
        else:
            valid_indices = range(min(10, num_detections))

        # Analyze geometry for each valid nail
        geometries = []
        valid_confidences = []

        for idx in valid_indices:
            mask = masks[idx]
            confidence = confidence_scores[idx] if confidence_scores is not None else 1.0

            # Resize mask to frame size
            mask_resized = cv2.resize(
                mask,
                (frame_w, frame_h),
                interpolation=cv2.INTER_LINEAR
            )

            # Threshold
            binary_mask = (mask_resized > 0.5).astype(np.uint8)

            # Skip small masks
            if np.sum(binary_mask) < 100:
                continue

            # Analyze geometry
            geometry = self.geometry_analyzer.analyze(binary_mask, min_area=100)
            if geometry is not None:
                geometries.append(geometry)
                valid_confidences.append(confidence)

        # Render all nails with professional renderer
        result = original_frame.copy()

        for i, geometry in enumerate(geometries):
            # Use the current material for all nails
            # (You can customize this to use different materials per nail)
            result = self.renderer.render_nail(
                result,
                geometry,
                self.current_material
            )

        render_time = (time.time() - start_time) * 1000
        self.render_times.append(render_time)

        return result, len(geometries)

    def next_material(self):
        """Cycle to next material preset"""
        self.current_preset_idx = (self.current_preset_idx + 1) % len(self.preset_names)
        preset_name = self.preset_names[self.current_preset_idx]
        self.current_material = self.presets[preset_name]
        print(f"💅 Material: {preset_name}")

    def previous_material(self):
        """Cycle to previous material preset"""
        self.current_preset_idx = (self.current_preset_idx - 1) % len(self.preset_names)
        preset_name = self.preset_names[self.current_preset_idx]
        self.current_material = self.presets[preset_name]
        print(f"💅 Material: {preset_name}")

    def set_custom_color(self, rgb_color):
        """Set custom color with current finish"""
        finish = self.current_material.get_finish_type()
        self.current_material = MaterialPresets.custom(rgb_color, finish)
        print(f"💅 Custom color: RGB{rgb_color} ({finish.value})")

    def get_avg_fps(self):
        """Get average FPS"""
        if not self.inference_times:
            return 0
        avg_time = sum(self.inference_times) / len(self.inference_times)
        return 1000 / avg_time if avg_time > 0 else 0

    def get_avg_render_time(self):
        """Get average render time"""
        if not self.render_times:
            return 0
        return sum(self.render_times) / len(self.render_times)


def main():
    parser = argparse.ArgumentParser(description='Professional live nail AR')
    parser.add_argument('--model', type=str, default=MODEL_PATH, help='Model path')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--threshold', type=float, default=0.2, help='Confidence threshold')
    parser.add_argument('--width', type=int, default=640, help='Camera width')
    parser.add_argument('--height', type=int, default=480, help='Camera height')
    parser.add_argument('--material', type=str, default='glossy_red',
                        help='Initial material preset')
    parser.add_argument('--skip-frames', type=int, default=1,
                        help='Process every N frames')
    parser.add_argument('--threads', type=int, default=4,
                        help='Number of CPU threads')

    # Headless mode arguments
    parser.add_argument('--headless', action='store_true',
                        help='Force headless mode (no GUI window)')
    parser.add_argument('--output-dir', type=str, default='renders',
                        help='Directory to save frames in headless mode')
    parser.add_argument('--save-every', type=int, default=10,
                        help='Save every N frames in headless mode')
    parser.add_argument('--max-frames', type=int, default=None,
                        help='Stop after processing N frames (optional)')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("✨ PROFESSIONAL NAIL AR - Photo-Realistic Rendering")
    print("="*60 + "\n")

    # Detect display availability
    has_display = detect_display() if not args.headless else False
    headless_mode = args.headless or not has_display

    if headless_mode:
        print("🖥️  HEADLESS MODE - Saving frames to disk")
        if not has_display and not args.headless:
            print("   (No display detected - auto-switched to headless)")

        # Create output directory
        output_dir = Path(args.output_dir)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        session_dir = output_dir / f"session_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"   Output: {session_dir}/")
        print(f"   Saving every {args.save_every} frames")
        if args.max_frames:
            print(f"   Max frames: {args.max_frames}")
    else:
        print("🖥️  GUI MODE - Interactive window")
        session_dir = None

    print()
    torch.set_num_threads(args.threads)

    # Initialize
    try:
        nail_ar = ProfessionalNailAR(
            args.model,
            args.threshold,
            args.material
        )
        nail_ar.frame_skip = args.skip_frames
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1

    # Open camera
    print(f"📷 Opening camera {args.camera}...")
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print("❌ Failed to open camera")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    print(f"✅ Camera opened")
    print("\n" + "="*60)
    print("PROFESSIONAL FEATURES:")
    print("  ✓ Curvature-aware shading (3D appearance)")
    print("  ✓ Phong/Blinn-Phong specular highlights")
    print("  ✓ Edge feathering and anti-aliasing")
    print("  ✓ Ambient occlusion")
    print("  ✓ Multiple material types (glossy, matte, metallic, glitter)")
    print("  ✓ Physically-based color blending")
    if not headless_mode:
        print("\nCONTROLS:")
        print("  'q'/'ESC'  - Quit")
        print("  'SPACE'    - Pause/Resume")
        print("  's'        - Save screenshot")
        print("  'n'        - Next material preset")
        print("  'p'        - Previous material preset")
        print("  'f'        - Toggle frame skip")
        print("  '+'/'-'    - Adjust confidence threshold")
    else:
        print("\nHEADLESS CONTROLS:")
        print("  Ctrl+C     - Stop processing")

    print("\nMATERIAL PRESETS:")
    for i, name in enumerate(nail_ar.preset_names):
        print(f"  {i+1}. {name}")
    print("="*60 + "\n")

    paused = False
    frame_num = 0
    total_frames = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1

            if not paused:
                # Frame skipping logic
                should_process = (total_frames % nail_ar.frame_skip == 0)

                if should_process:
                    frame_num += 1

                    # Preprocess
                    img_tensor = nail_ar.preprocess(frame)

                    # Inference
                    mask_tensor, scores, inference_time = nail_ar.inference(img_tensor)

                    # Professional rendering
                    result, num_nails = nail_ar.render_professional(
                        mask_tensor, scores, frame
                    )

                    nail_ar.last_result = result
                else:
                    # Reuse last result
                    result = nail_ar.last_result if nail_ar.last_result is not None else frame

                # Add info overlay
                avg_fps = nail_ar.get_avg_fps()
                avg_render = nail_ar.get_avg_render_time()

                info = [
                    f"Material: {nail_ar.preset_names[nail_ar.current_preset_idx]}",
                    f"Inference: {nail_ar.inference_times[-1] if nail_ar.inference_times else 0:.1f}ms",
                    f"Render: {avg_render:.1f}ms",
                    f"Total: {nail_ar.inference_times[-1] + avg_render if nail_ar.inference_times else 0:.1f}ms",
                    f"FPS: {avg_fps:.1f}",
                    f"Nails: {num_nails if should_process else '...'}",
                ]

                # Draw semi-transparent background for text
                overlay_h = 30 + len(info) * 30
                overlay_bg = result[0:overlay_h, 0:350].copy()
                overlay_bg = cv2.addWeighted(overlay_bg, 0.3, np.zeros_like(overlay_bg), 0.7, 0)
                result[0:overlay_h, 0:350] = overlay_bg

                y = 30
                for text in info:
                    cv2.putText(
                        result, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (255, 255, 255), 2, cv2.LINE_AA
                    )
                    y += 30

                # Watermark
                cv2.putText(
                    result, "PROFESSIONAL NAIL AR",
                    (10, result.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (200, 200, 255), 1, cv2.LINE_AA
                )

                display_frame = result

            # Mode-specific display and interaction
            if headless_mode:
                # Headless: Save frames to disk
                if should_process and (frame_num % args.save_every == 0):
                    output_path = session_dir / f"frame_{frame_num:05d}.jpg"
                    cv2.imwrite(str(output_path), display_frame)
                    print(f"[{frame_num:5d}] Saved {output_path.name} | "
                          f"{num_nails} nails | "
                          f"Inference: {nail_ar.inference_times[-1]:.1f}ms | "
                          f"Render: {avg_render:.1f}ms | "
                          f"Total: {nail_ar.inference_times[-1] + avg_render:.1f}ms")

                # Check max frames limit
                if args.max_frames and frame_num >= args.max_frames:
                    print(f"\n✅ Reached max frames limit ({args.max_frames})")
                    break

                # Small delay to avoid CPU overload
                time.sleep(0.001)

            else:
                # GUI mode: Display window and handle keyboard
                cv2.imshow('Professional Nail AR', display_frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord('q') or key == 27:
                    break
                elif key == ord(' '):
                    paused = not paused
                    print("⏸️  PAUSED" if paused else "▶️  RESUMED")
                elif key == ord('s'):
                    filename = f"nail_ar_professional_{int(time.time())}.jpg"
                    cv2.imwrite(filename, display_frame)
                    print(f"📸 Saved: {filename}")
                elif key == ord('n'):
                    nail_ar.next_material()
                elif key == ord('p'):
                    nail_ar.previous_material()
                elif key == ord('+') or key == ord('='):
                    nail_ar.confidence_threshold = min(1.0, nail_ar.confidence_threshold + 0.05)
                    print(f"Threshold: {nail_ar.confidence_threshold:.2f}")
                elif key == ord('-') or key == ord('_'):
                    nail_ar.confidence_threshold = max(0.0, nail_ar.confidence_threshold - 0.05)
                    print(f"Threshold: {nail_ar.confidence_threshold:.2f}")
                elif key == ord('f'):
                    nail_ar.frame_skip = 1 if nail_ar.frame_skip > 1 else 2
                    print(f"Frame skip: 1/{nail_ar.frame_skip}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")

    finally:
        cap.release()

        # Only call GUI functions if display is available
        if not headless_mode:
            try:
                cv2.destroyAllWindows()
            except:
                pass

        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total frames: {total_frames}")
        print(f"Processed frames: {frame_num}")
        if nail_ar.inference_times:
            times = list(nail_ar.inference_times)
            print(f"Avg inference: {np.mean(times):.2f}ms")
            print(f"Avg render: {nail_ar.get_avg_render_time():.2f}ms")
            print(f"Total pipeline: {np.mean(times) + nail_ar.get_avg_render_time():.2f}ms")
            print(f"Avg FPS: {1000/(np.mean(times) + nail_ar.get_avg_render_time()):.1f}")

        if headless_mode and session_dir:
            saved_count = len(list(session_dir.glob("*.jpg")))
            print(f"Saved frames: {saved_count}")
            print(f"Output directory: {session_dir}")

        print("="*60)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
