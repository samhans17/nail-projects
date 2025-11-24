"""
Simplified RF-DETR to ONNX Conversion
Uses a wrapper to simplify model outputs for ONNX export
"""

import torch
import torch.nn as nn
import os
import sys

CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
OUTPUT_DIR = "./tflite_models"

class SimplifiedRFDETRWrapper(nn.Module):
    """Wrapper that simplifies RF-DETR output for ONNX export"""
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        # Run the model
        outputs = self.model(x)

        # RF-DETR returns a tuple of many outputs
        # For segmentation, we typically need:
        # - boxes
        # - class logits
        # - masks

        # Return only the first few outputs (adjust based on actual model output)
        if isinstance(outputs, (tuple, list)):
            # Return masks (usually the last output)
            return outputs[-1]  # Masks

        return outputs

def main():
    print("\n" + "="*60)
    print("Simplified RF-DETR to ONNX Conversion")
    print("="*60 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load model
    print("📦 Loading RF-DETR model...")
    from rfdetr import RFDETRSegPreview

    model = RFDETRSegPreview(pretrain_weights=CHECKPOINT_PATH)
    print("✅ Model loaded\n")

    # Get the underlying model
    if hasattr(model, 'model') and hasattr(model.model, 'model'):
        base_model = model.model.model
    else:
        print("❌ Could not extract model")
        return 1

    base_model.eval()

    # Create wrapper
    print("🔧 Creating simplified wrapper...")
    wrapped_model = SimplifiedRFDETRWrapper(base_model)
    wrapped_model.eval()

    # Test with dummy input
    print("🧪 Testing model...")
    dummy_input = torch.randn(1, 3, 432, 432)

    with torch.no_grad():
        try:
            output = wrapped_model(dummy_input)
            print(f"✅ Model test successful!")
            if isinstance(output, torch.Tensor):
                print(f"   Output shape: {output.shape}")
            elif isinstance(output, (tuple, list)):
                print(f"   Number of outputs: {len(output)}")
                for i, out in enumerate(output[:3]):  # Show first 3
                    if isinstance(out, torch.Tensor):
                        print(f"   Output {i} shape: {out.shape}")
        except Exception as e:
            print(f"❌ Model test failed: {e}")
            return 1

    # Export to ONNX
    onnx_path = os.path.join(OUTPUT_DIR, "rfdetr_nails.onnx")
    print(f"\n📤 Exporting to ONNX: {onnx_path}")

    try:
        with torch.no_grad():
            torch.onnx.export(
                wrapped_model,
                dummy_input,
                onnx_path,
                export_params=True,
                opset_version=16,  # Try opset 16
                do_constant_folding=True,
                input_names=['images'],
                output_names=['masks'],
                verbose=False,
                dynamo=False
            )

        print("✅ ONNX export successful!")

        # Validate
        import onnx
        onnx_model = onnx.load(onnx_path)
        onnx.checker.check_model(onnx_model)
        print("✅ ONNX model is valid")

        file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
        print(f"📊 ONNX model size: {file_size_mb:.2f} MB")

        print("\n" + "="*60)
        print("🎉 Conversion successful!")
        print("="*60)
        print(f"\nOutput file: {onnx_path}")

        return 0

    except Exception as e:
        print(f"❌ ONNX export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
