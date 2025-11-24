"""
Optimized Live Inference with PyTorch Mobile RF-DETR Model
Multiple optimizations to reduce inference latency
"""

import torch
import cv2
import numpy as np
from PIL import Image
import time
import argparse
from collections import deque

MODEL_PATH = "./pytorch_mobile_models/rfdetr_nails.pt"

class NailSegmentationOptimized:
    def __init__(self, model_path, confidence_threshold=0.2, input_size=432):
        """Initialize with optimizations"""
        print(f"📦 Loading PyTorch Mobile model from: {model_path}")

        try:
            self.model = torch.jit.load(model_path)
            self.model.eval()

            # Enable optimizations
            torch.set_num_threads(4)  # Use multiple CPU threads
            torch.set_grad_enabled(False)  # Disable gradient computation

            print("✅ Model loaded with optimizations")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

        self.confidence_threshold = confidence_threshold
        # Model was trained at 432×432, can't change input size
        # But we can reduce camera resolution for faster preprocessing
        self.input_size = 432  # Fixed by model architecture
        self.camera_downsample = input_size  # We'll downsample camera feed

        print(f"⚡ Model input size: 432×432 (fixed by architecture)")
        print(f"⚡ Camera processing: {self.camera_downsample}×{self.camera_downsample}")

        # Warmup model
        print("🔥 Warming up model...")
        dummy = torch.randn(1, 3, 432, 432)
        for _ in range(3):
            _ = self.model(dummy)
        print("✅ Model warmed up")

        # Colors for visualization
        self.colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255),
            (255, 255, 0), (255, 0, 255), (0, 255, 255),
        ]

        # Performance tracking
        self.inference_times = deque(maxlen=30)

        # Frame skipping
        self.frame_skip = 1  # Process every N frames
        self.frame_count = 0
        self.last_overlay = None

    def preprocess(self, frame):
        """Optimized preprocessing"""
        # First downsample camera frame if needed (reduces initial processing)
        if self.camera_downsample < 432:
            frame = cv2.resize(
                frame,
                (self.camera_downsample, self.camera_downsample),
                interpolation=cv2.INTER_AREA
            )

        # Then resize to model input size (432×432)
        resized = cv2.resize(
            frame,
            (432, 432),
            interpolation=cv2.INTER_AREA  # INTER_AREA is fastest for downscaling
        )

        # Convert BGR to RGB and normalize in one go
        rgb_normalized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

        # Transpose to CHW format
        img_array = np.transpose(rgb_normalized, (2, 0, 1))

        # Convert to tensor
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return img_tensor

    def inference(self, img_tensor):
        """Run optimized inference"""
        start_time = time.time()

        # Run inference
        outputs = self.model(img_tensor)

        inference_time = (time.time() - start_time) * 1000
        self.inference_times.append(inference_time)

        # Extract outputs
        if isinstance(outputs, tuple):
            boxes = outputs[0]
            scores = outputs[1]
            mask_tensor = outputs[2]
        else:
            mask_tensor = outputs
            scores = None

        return mask_tensor, scores, inference_time

    def postprocess_fast(self, mask_tensor, scores, original_frame):
        """Faster post-processing with optimizations"""
        # Get mask data
        masks = mask_tensor.squeeze(0).numpy()
        num_detections, mask_h, mask_w = masks.shape

        frame_h, frame_w = original_frame.shape[:2]

        # Get confidence scores
        if scores is not None:
            class_scores = scores.squeeze(0).numpy()
            confidence_scores = class_scores[:, 1]
        else:
            confidence_scores = None

        # Pre-filter detections by confidence (faster)
        if confidence_scores is not None:
            valid_indices = np.where(confidence_scores > self.confidence_threshold)[0]
        else:
            valid_indices = range(min(10, num_detections))  # Process max 10 detections

        overlay = original_frame.copy()
        detected_nails = 0

        for idx in valid_indices:
            mask = masks[idx]
            confidence = confidence_scores[idx] if confidence_scores is not None else 1.0

            # Resize mask (use INTER_NEAREST for speed)
            mask_resized = cv2.resize(
                mask,
                (frame_w, frame_h),
                interpolation=cv2.INTER_NEAREST
            )

            # Threshold mask
            binary_mask = (mask_resized > 0.5).astype(np.uint8)

            # Skip if mask is too small
            if np.sum(binary_mask) < 100:
                continue

            detected_nails += 1

            # Create colored mask
            color = self.colors[detected_nails % len(self.colors)]
            colored_mask = np.zeros_like(original_frame)
            colored_mask[binary_mask == 1] = color

            # Blend
            overlay = cv2.addWeighted(overlay, 1, colored_mask, 0.4, 0)

            # Draw contours (simplified)
            contours, _ = cv2.findContours(
                binary_mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            if len(contours) > 0:
                cv2.drawContours(overlay, contours, -1, color, 2)

                # Draw confidence
                M = cv2.moments(contours[0])
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    cv2.putText(
                        overlay, f"{confidence:.2f}",
                        (cx - 20, cy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 255), 2, cv2.LINE_AA
                    )

        return overlay, detected_nails

    def get_avg_fps(self):
        """Get average FPS"""
        if not self.inference_times:
            return 0
        avg_time = sum(self.inference_times) / len(self.inference_times)
        return 1000 / avg_time if avg_time > 0 else 0

def main():
    parser = argparse.ArgumentParser(description='Optimized live nail segmentation')
    parser.add_argument('--model', type=str, default=MODEL_PATH, help='Model path')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--threshold', type=float, default=0.2, help='Confidence threshold')
    parser.add_argument('--width', type=int, default=640, help='Camera width')
    parser.add_argument('--height', type=int, default=480, help='Camera height')
    parser.add_argument('--camera-size', type=int, default=432,
                        help='Camera downsample size (320=faster preprocessing, 432=no downsample)')
    parser.add_argument('--skip-frames', type=int, default=2,
                        help='Process every N frames (2=half speed, faster)')
    parser.add_argument('--threads', type=int, default=4,
                        help='Number of CPU threads for inference')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("⚡ OPTIMIZED Live Nail Segmentation")
    print("="*60 + "\n")

    # Set thread count
    torch.set_num_threads(args.threads)

    # Initialize
    try:
        segmentation = NailSegmentationOptimized(
            args.model,
            args.threshold,
            args.camera_size
        )
        segmentation.frame_skip = args.skip_frames
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
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency

    print(f"✅ Camera opened")
    print("\n" + "="*60)
    print("OPTIMIZATIONS ENABLED:")
    print(f"  • Model input: 432×432 (fixed)")
    print(f"  • Camera downsample: {args.camera_size}×{args.camera_size}")
    print(f"  • Frame skip: {args.skip_frames}")
    print(f"  • CPU threads: {args.threads}")
    print(f"  • Fast interpolation: INTER_AREA/NEAREST")
    print("\nCONTROLS:")
    print("  'q'/'ESC' - Quit")
    print("  'SPACE'   - Pause/Resume")
    print("  's'       - Save screenshot")
    print("  '+'/'-'   - Adjust threshold")
    print("  'f'       - Toggle frame skip (current: 1/{})".format(args.skip_frames))
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
                should_process = (total_frames % segmentation.frame_skip == 0)

                if should_process:
                    frame_num += 1

                    # Preprocess
                    img_tensor = segmentation.preprocess(frame)

                    # Inference
                    mask_tensor, scores, inference_time = segmentation.inference(img_tensor)

                    # Post-process
                    overlay, num_nails = segmentation.postprocess_fast(mask_tensor, scores, frame)

                    segmentation.last_overlay = overlay
                else:
                    # Reuse last result
                    overlay = segmentation.last_overlay if segmentation.last_overlay is not None else frame

                # Add info
                avg_fps = segmentation.get_avg_fps()
                effective_fps = avg_fps / segmentation.frame_skip if segmentation.frame_skip > 0 else avg_fps

                info = [
                    f"Inference: {segmentation.inference_times[-1] if segmentation.inference_times else 0:.1f}ms",
                    f"FPS: {avg_fps:.1f}",
                    f"Effective FPS: {effective_fps:.1f}",
                    f"Nails: {num_nails if should_process else '...'}",
                    f"Skip: 1/{segmentation.frame_skip}",
                ]

                y = 30
                for text in info:
                    cv2.putText(
                        overlay, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0), 2, cv2.LINE_AA
                    )
                    y += 30

                cv2.putText(
                    overlay, "OPTIMIZED MODE",
                    (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 255), 1, cv2.LINE_AA
                )

                display_frame = overlay

            cv2.imshow('Nail Segmentation - OPTIMIZED', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord(' '):
                paused = not paused
                print("⏸️  PAUSED" if paused else "▶️  RESUMED")
            elif key == ord('s'):
                filename = f"nail_seg_opt_{int(time.time())}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"📸 Saved: {filename}")
            elif key == ord('+') or key == ord('='):
                segmentation.confidence_threshold = min(1.0, segmentation.confidence_threshold + 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")
            elif key == ord('-') or key == ord('_'):
                segmentation.confidence_threshold = max(0.0, segmentation.confidence_threshold - 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")
            elif key == ord('f'):
                segmentation.frame_skip = 1 if segmentation.frame_skip > 1 else 2
                print(f"Frame skip: 1/{segmentation.frame_skip}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Total frames: {total_frames}")
        print(f"Processed frames: {frame_num}")
        if segmentation.inference_times:
            times = list(segmentation.inference_times)
            print(f"Avg inference: {np.mean(times):.2f}ms")
            print(f"Min inference: {np.min(times):.2f}ms")
            print(f"Max inference: {np.max(times):.2f}ms")
            print(f"Avg FPS: {1000/np.mean(times):.1f}")
        print("="*60)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
