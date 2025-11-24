"""
Live Inference with PyTorch Mobile RF-DETR Model
Tests the exported Android model on your computer with webcam
"""

import torch
import cv2
import numpy as np
from PIL import Image
import time
import argparse

MODEL_PATH = "./pytorch_mobile_models/rfdetr_nails.pt"

class NailSegmentationLive:
    def __init__(self, model_path, confidence_threshold=0.5):
        """Initialize the nail segmentation model"""
        print(f"📦 Loading PyTorch Mobile model from: {model_path}")

        try:
            self.model = torch.jit.load(model_path)
            self.model.eval()
            print("✅ Model loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

        self.confidence_threshold = confidence_threshold
        self.input_size = 432

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

    def preprocess(self, frame):
        """Preprocess frame for model input"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)

        # Resize to model input size
        resized = pil_image.resize((self.input_size, self.input_size), Image.BILINEAR)

        # Convert to tensor and normalize to [0, 1]
        img_array = np.array(resized).astype(np.float32) / 255.0

        # Transpose to CHW format
        img_array = np.transpose(img_array, (2, 0, 1))

        # Add batch dimension
        img_tensor = torch.from_numpy(img_array).unsqueeze(0)

        return img_tensor, rgb_frame

    def inference(self, img_tensor):
        """Run inference on preprocessed image"""
        with torch.no_grad():
            start_time = time.time()
            outputs = self.model(img_tensor)
            inference_time = (time.time() - start_time) * 1000  # Convert to ms

            self.inference_times.append(inference_time)
            if len(self.inference_times) > 30:
                self.inference_times.pop(0)

        # Extract outputs
        # Model returns tuple of 3 tensors:
        # [0] Bounding boxes: [1, 200, 4]
        # [1] Class scores: [1, 200, 2]
        # [2] Masks: [1, 200, 108, 108]
        if isinstance(outputs, tuple):
            boxes = outputs[0]  # Bounding boxes
            scores = outputs[1]  # Class scores
            mask_tensor = outputs[2]  # Masks
        else:
            mask_tensor = outputs
            scores = None

        return mask_tensor, scores, inference_time

    def postprocess(self, mask_tensor, scores, original_frame):
        """Post-process masks and overlay on frame"""
        # Get mask data
        masks = mask_tensor.squeeze(0).numpy()  # [200, 108, 108]
        num_detections, mask_h, mask_w = masks.shape

        frame_h, frame_w = original_frame.shape[:2]

        # Get class scores if available
        if scores is not None:
            class_scores = scores.squeeze(0).numpy()  # [200, 2]
            # Get foreground class score (index 1)
            confidence_scores = class_scores[:, 1]
        else:
            confidence_scores = None

        # Create overlay
        overlay = original_frame.copy()

        detected_nails = 0

        for i in range(num_detections):
            mask = masks[i]

            # Check confidence score first if available
            if confidence_scores is not None:
                confidence = confidence_scores[i]
                if confidence < self.confidence_threshold:
                    continue
            else:
                # Fall back to checking mask intensity
                max_value = mask.max()
                confidence = max_value
                if max_value < self.confidence_threshold:
                    continue

            # Check if mask is significant
            if True:  # Already filtered above
                detected_nails += 1

                # Resize mask to frame size
                mask_resized = cv2.resize(
                    mask,
                    (frame_w, frame_h),
                    interpolation=cv2.INTER_LINEAR
                )

                # Threshold mask
                binary_mask = (mask_resized > 0.5).astype(np.uint8)

                # Create colored mask
                color = self.colors[detected_nails % len(self.colors)]
                colored_mask = np.zeros_like(original_frame)
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

                # Draw confidence text on mask
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

        return overlay, detected_nails

    def get_avg_fps(self):
        """Get average FPS from recent inferences"""
        if not self.inference_times:
            return 0
        avg_time = sum(self.inference_times) / len(self.inference_times)
        return 1000 / avg_time if avg_time > 0 else 0

def main():
    parser = argparse.ArgumentParser(description='Live nail segmentation inference')
    parser.add_argument('--model', type=str, default=MODEL_PATH, help='Path to PyTorch Mobile model')
    parser.add_argument('--camera', type=int, default=0, help='Camera index (0 for default)')
    parser.add_argument('--threshold', type=float, default=0.2, help='Confidence threshold (0-1)')
    parser.add_argument('--width', type=int, default=1080, help='Camera frame width')
    parser.add_argument('--height', type=int, default=1280, help='Camera frame height')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("Live Nail Segmentation with PyTorch Mobile")
    print("="*60 + "\n")

    # Initialize model
    try:
        segmentation = NailSegmentationLive(args.model, args.threshold)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return 1

    # Open camera
    print(f"📷 Opening camera {args.camera}...")
    cap = cv2.VideoCapture(args.camera)

    if not cap.isOpened():
        print("❌ Failed to open camera")
        return 1

    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"✅ Camera opened: {actual_width}×{actual_height}")
    print("\n" + "="*60)
    print("CONTROLS:")
    print("  'q' or 'ESC' - Quit")
    print("  'SPACE'      - Pause/Resume")
    print("  's'          - Save screenshot")
    print("  '+'/'-'      - Adjust confidence threshold")
    print("="*60 + "\n")

    paused = False
    frame_count = 0

    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break

                frame_count += 1

                # Preprocess
                img_tensor, rgb_frame = segmentation.preprocess(frame)

                # Run inference
                mask_tensor, scores, inference_time = segmentation.inference(img_tensor)

                # Post-process and visualize
                overlay, num_nails = segmentation.postprocess(mask_tensor, scores, frame)

                # Add info text
                avg_fps = segmentation.get_avg_fps()
                info_text = [
                    f"FPS: {avg_fps:.1f}",
                    f"Inference: {inference_time:.1f}ms",
                    f"Nails: {num_nails}",
                    f"Threshold: {segmentation.confidence_threshold:.2f}",
                ]

                y_offset = 30
                for text in info_text:
                    cv2.putText(
                        overlay, text, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 0), 2, cv2.LINE_AA
                    )
                    y_offset += 30

                # Add model info
                cv2.putText(
                    overlay, "PyTorch Mobile RF-DETR",
                    (10, overlay.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (255, 255, 255), 1, cv2.LINE_AA
                )

                display_frame = overlay

            # Display
            cv2.imshow('Nail Segmentation - PyTorch Mobile', display_frame)

            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # 'q' or ESC
                print("\n👋 Quitting...")
                break

            elif key == ord(' '):  # SPACE
                paused = not paused
                status = "⏸️  PAUSED" if paused else "▶️  RESUMED"
                print(f"{status}")

            elif key == ord('s'):  # Save screenshot
                filename = f"nail_segmentation_{int(time.time())}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"📸 Screenshot saved: {filename}")

            elif key == ord('+') or key == ord('='):  # Increase threshold
                segmentation.confidence_threshold = min(1.0, segmentation.confidence_threshold + 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")

            elif key == ord('-') or key == ord('_'):  # Decrease threshold
                segmentation.confidence_threshold = max(0.0, segmentation.confidence_threshold - 0.05)
                print(f"Threshold: {segmentation.confidence_threshold:.2f}")

    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")

    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()

        # Print statistics
        print("\n" + "="*60)
        print("SESSION STATISTICS")
        print("="*60)
        print(f"Total frames: {frame_count}")
        if segmentation.inference_times:
            avg_time = sum(segmentation.inference_times) / len(segmentation.inference_times)
            print(f"Average inference: {avg_time:.2f}ms")
            print(f"Average FPS: {1000/avg_time:.1f}")
            print(f"Min inference: {min(segmentation.inference_times):.2f}ms")
            print(f"Max inference: {max(segmentation.inference_times):.2f}ms")
        print("="*60)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
