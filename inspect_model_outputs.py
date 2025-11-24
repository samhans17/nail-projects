"""
Quick script to inspect what the PyTorch Mobile model actually outputs
"""

import torch
import numpy as np

MODEL_PATH = "./pytorch_mobile_models/rfdetr_nails.pt"

print("📦 Loading model...")
model = torch.jit.load(MODEL_PATH)
model.eval()

print("✅ Model loaded\n")

# Create dummy input
dummy_input = torch.randn(1, 3, 432, 432)

print("🔍 Running inference with dummy input...")
with torch.no_grad():
    outputs = model(dummy_input)

print(f"\n📊 Output structure:")
print(f"Type: {type(outputs)}")

if isinstance(outputs, tuple):
    print(f"Number of outputs: {len(outputs)}")
    print("\nOutput shapes:")
    for i, output in enumerate(outputs):
        if isinstance(output, torch.Tensor):
            print(f"  [{i}] Shape: {output.shape}, dtype: {output.dtype}")
        else:
            print(f"  [{i}] Type: {type(output)}")

    # Try to identify which output contains masks
    print("\n🔍 Looking for mask output (likely [B, N, H, W] or [B, H, W])...")
    for i, output in enumerate(outputs):
        if isinstance(output, torch.Tensor):
            shape = output.shape
            # Masks are typically [1, num_detections, height, width]
            if len(shape) == 4 and shape[2] > 50 and shape[3] > 50:
                print(f"  ✓ Index {i} looks like masks: {shape}")
elif isinstance(outputs, torch.Tensor):
    print(f"Single tensor output: {outputs.shape}")
else:
    print(f"Unexpected output type: {type(outputs)}")
