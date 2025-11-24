"""
Live Inference with Original RF-DETR Model (Python API)
This uses the Python RF-DETR library directly (not the mobile model)
Faster and more accurate for testing
"""

import cv2
import numpy as np
from PIL import Image
import time
import argparse

CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"

class NailSegmentationOriginal:
    def __init__(self, checkpoint_path, confidence_threshold=0.5):
        """Initialize with original RF-DETR model"""
        print(f"📦 Loading RF-DETR model from: {checkpoint_path}")

        try:
            from rfdetr import RFDETRSegPreview

            self.model = RFDETRSegPreview(pretrain_weights=checkpoint_path)
            self.model.optimize_for_inference()
            print("✅ Model loaded and optimized")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

        self.confidence_threshold = confidence_threshold

        # Colors for visualization (BGR format for OpenCV)
        self.colors = [
            (255, 0, 0),    # Blue
            (0, 255, 0),    # Green
            (0, 0, 255),    # Red
            (255, 255, 0),  # Cyan
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Yellow
        ]

        # Performance tracking
        self.inference_times = []

    def process_frame(self, frame):
        """Process a single frame"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        # Run inference
        start_time = time.time()
        detections = self.model.predict(pil_image, threshold=self.confidence_threshold)
        inference_time = (time.time() - start_time) * 1000

        self.inference_times.append(inference_time)
        if len(self.inference_times) > 30:
            self.inference_times.pop(0)

        return detections, inference_time

    def visualize(self, frame, detections):
        """Visualize detections on frame"""
        overlay = frame.copy()

        if detections.mask is None or len(detections) == 0:
            return overlay, 0

        frame_h, frame_w = frame.shape[:2]

        for i in range(len(detections)):
            mask = detections.mask[i]
            confidence = detections.confidence[i]

            if confidence > self.confidence_threshold:
                # Resize mask to frame size
                mask_h, mask_w = mask.shape
                mask_resized = cv2.resize(
                    mask.astype(np.float32),
                    (frame_w, frame_h),
                    interpolation=cv2.INTER_LINEAR
                )

                # Threshold mask
                binary_mask = (mask_resized > 0.5).astype(np.uint8)

                # Create colored mask
                color = self.colors[i % len(self.colors)]
                colored_mask = np.zeros_like(frame)
                colored_mask[binary_mask == 1] = color

                # Blend with overlay
                overlay = cv2.addWeighted(overlay, 1, colored_mask, 0.4, 0)

                # Draw contours
                contours, _ = cv2.findContours(
                    binary_mask,
                    cv2.RETR_EXTERNAL,
                    cv2.CHAIN_APPROX_SIMPLE
                )
                cv2.drawContours(overlay, contours, -1, color, 2)

                # Draw confidence
                if len(contours) > 0:
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

        return overlay, len(detections)

    def get_avg_fps(self):
        """Get average FPS"""
        if not self.inference_times:
            return 0
        avg_time = sum(self.inference_times) / len(self.inference_times)
        return 1000 / avg_time if avg_time > 0 else 0

def main():
    parser = argparse.ArgumentParser(description='Live nail segmentation with original RF-DETR')
    parser.add_argument('--checkpoint', type=str, default=CHECKPOINT_PATH, help='Path to checkpoint')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--threshold', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--width', type=int, default=640, help='Camera width')
    parser.add_argument('--height', type=int, default=480, help='Camera height')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("Live Nail Segmentation with RF-DETR (Original)")
    print("="*60 + "\n")

    # Initialize
    try:
        segmentation = NailSegmentationOriginal(args.checkpoint, args.threshold)
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

    print(f"✅ Camera opened")
    print("\n" + "="*60)
    print("CONTROLS:")
    print("  'q' or 'ESC' - Quit")
    print("  'SPACE'      - Pause/Resume")
    print("  's'          - Save screenshot")
    print("  '+'/'-'      - Adjust threshold")
    print("="*60 + "\n")

    paused = False
    frame_count = 0

    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Process frame
                detections, inference_time = segmentation.process_frame(frame)

                # Visualize
                overlay, num_nails = segmentation.visualize(frame, detections)

                # Add info text
                avg_fps = segmentation.get_avg_fps()
                info = [
                    f"FPS: {avg_fps:.1f}",
                    f"Inference: {inference_time:.1f}ms",
                    f"Nails: {num_nails}",
                    f"Threshold: {segmentation.confidence_threshold:.2f}",
                ]

                y = 30
                for text in info:
                    cv2.putText(
                        overlay, text, (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 0), 2, cv2.LINE_AA
                    )
                    y += 30

                cv2.putText(
                    overlay, "RF-DETR (Python)",
                    (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA
                )

                display_frame = overlay

            cv2.imshow('Nail Segmentation - RF-DETR', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:
                break
            elif key == ord(' '):
                paused = not paused
                print("⏸️  PAUSED" if paused else "▶️  RESUMED")
            elif key == ord('s'):
                filename = f"nail_seg_{int(time.time())}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"📸 Saved: {filename}")
            elif key == ord('+') or key == ord('='):
                segmentation.confidence_threshold = min(1.0, segmentation.confidence_threshold + 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")
            elif key == ord('-') or key == ord('_'):
                segmentation.confidence_threshold = max(0.0, segmentation.confidence_threshold - 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")

    finally:
        cap.release()
        cv2.destroyAllWindows()

        print("\n" + "="*60)
        print("STATISTICS")
        print("="*60)
        print(f"Frames: {frame_count}")
        if segmentation.inference_times:
            avg = sum(segmentation.inference_times) / len(segmentation.inference_times)
            print(f"Avg inference: {avg:.2f}ms")
            print(f"Avg FPS: {1000/avg:.1f}")
        print("="*60)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
