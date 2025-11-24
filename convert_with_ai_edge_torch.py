"""
Convert RF-DETR to TFLite using AI Edge Torch (Google's official converter)
This approach bypasses ONNX and converts PyTorch directly to TFLite
"""

import torch
import os
import sys

CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
OUTPUT_DIR = "./tflite_models"

def main():
    print("\n" + "="*60)
    print("RF-DETR to TFLite via AI Edge Torch")
    print("="*60 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: Install ai-edge-torch if needed
    print("📦 Checking ai-edge-torch installation...")
    try:
        import ai_edge_torch
        print(f"✅ ai-edge-torch {ai_edge_torch.__version__} installed")
    except ImportError:
        print("⚙️ Installing ai-edge-torch...")
        os.system("pip install -q ai-edge-torch")
        import ai_edge_torch
        print("✅ ai-edge-torch installed")

    # Step 2: Load RF-DETR model
    print("\n📦 Loading RF-DETR model...")
    from rfdetr import RFDETRSegPreview

    model = RFDETRSegPreview(pretrain_weights=CHECKPOINT_PATH)
    print("✅ Model loaded")

    # Get the underlying PyTorch model (eager mode, not traced)
    if hasattr(model, 'model') and hasattr(model.model, 'model'):
        pytorch_model = model.model.model
        print("✅ Extracted PyTorch model (eager mode)")
    else:
        print("❌ Could not extract model")
        return 1

    pytorch_model.eval()

    # Step 3: Create sample input
    sample_input = (torch.randn(1, 3, 432, 432),)
    print(f"✅ Created sample input: {sample_input[0].shape}")

    # Step 4: Convert to TFLite
    tflite_path = os.path.join(OUTPUT_DIR, "rfdetr_nails.tflite")
    print(f"\n🔄 Converting to TFLite: {tflite_path}")
    print("   This may take several minutes...")

    try:
        # Convert with ai_edge_torch
        edge_model = ai_edge_torch.convert(
            pytorch_model,
            sample_input
        )

        # Export to TFLite
        edge_model.export(tflite_path)

        print("✅ TFLite conversion successful!")

        # Check file size
        file_size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
        print(f"📊 TFLite model size: {file_size_mb:.2f} MB")

        # Test the model
        print("\n🧪 Testing TFLite model...")
        import tensorflow as tf

        interpreter = tf.lite.Interpreter(model_path=tflite_path)
        interpreter.allocate_tensors()

        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print(f"✅ Model loaded in TFLite interpreter")
        print(f"\nInput details:")
        for detail in input_details:
            print(f"  - {detail['name']}: {detail['shape']} ({detail['dtype']})")

        print(f"\nOutput details:")
        for detail in output_details:
            print(f"  - {detail['name']}: {detail['shape']} ({detail['dtype']})")

        print("\n" + "="*60)
        print("🎉 CONVERSION SUCCESSFUL!")
        print("="*60)
        print(f"\n📁 Output file: {tflite_path}")
        print(f"📊 Size: {file_size_mb:.2f} MB")
        print("\n✅ Ready for Android deployment!")

        return 0

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        print("\n⚠️ ai-edge-torch might not support all RF-DETR operations")
        print("\nTrying fallback: Convert with quantization...")

        # Try with quantization (might help with some ops)
        try:
            edge_model = ai_edge_torch.convert(
                pytorch_model,
                sample_input,
                quant_config=ai_edge_torch.config.QuantConfig(
                    pt2e_quantizer=ai_edge_torch.quantize.PT2EQuantizer.quantizer_mode_int8_dynamic_activation
                )
            )

            edge_model.export(tflite_path)
            print("✅ TFLite conversion with quantization successful!")

            file_size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
            print(f"📊 TFLite model size: {file_size_mb:.2f} MB")

            return 0

        except Exception as e2:
            print(f"❌ Quantized conversion also failed: {e2}")
            import traceback
            traceback.print_exc()

            print("\n" + "="*60)
            print("ALTERNATIVE SOLUTION FOR ANDROID")
            print("="*60)
            print("\nSince RF-DETR is too complex for TFLite, consider:")
            print("\n1. PyTorch Mobile for Android:")
            print("   - Full RF-DETR support")
            print("   - Export your model:")
            print("     model.optimize_for_inference()")
            print("     torch.jit.save(model.model.inference_model, 'model.ptl')")
            print("   - Use in Android: https://pytorch.org/mobile/android/")
            print("\n2. Train a simpler model:")
            print("   - YOLOv8-seg (has official TFLite support)")
            print("   - Use your RF-DETR dataset for training")
            print("\n3. Run inference on server:")
            print("   - Keep RF-DETR on backend")
            print("   - Android app sends images via API")

            return 1

if __name__ == "__main__":
    sys.exit(main())
