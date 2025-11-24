"""
Export RF-DETR to PyTorch Mobile (Standard TorchScript)
Simpler approach without mobile-specific optimizations
"""

import torch
import os
import sys

CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
OUTPUT_DIR = "./pytorch_mobile_models"

def main():
    print("\n" + "="*60)
    print("RF-DETR to PyTorch Mobile (Simple Export)")
    print("="*60 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load model
    print("📦 Loading RF-DETR model...")
    from rfdetr import RFDETRSegPreview

    model = RFDETRSegPreview(pretrain_weights=CHECKPOINT_PATH)
    print("✅ Model loaded")

    # Optimize for inference
    print("\n⚡ Optimizing for inference...")
    model.optimize_for_inference()
    print("✅ Model optimized with TorchScript")

    # Get the traced model
    if hasattr(model, 'model') and hasattr(model.model, 'inference_model'):
        traced_model = model.model.inference_model
        print("✅ Got TorchScript traced model")
    else:
        print("❌ Could not get traced model")
        return 1

    # Save directly (without mobile optimization)
    output_path = os.path.join(OUTPUT_DIR, "rfdetr_nails.pt")
    print(f"\n📤 Saving model: {output_path}")

    torch.jit.save(traced_model, output_path)

    print("✅ Model saved successfully!")

    # Check file size
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"📊 Model size: {file_size_mb:.2f} MB")

    print("\n" + "="*60)
    print("🎉 EXPORT SUCCESSFUL!")
    print("="*60)
    print(f"\n📁 Output file: {output_path}")
    print(f"📊 Size: {file_size_mb:.2f} MB")
    print("\n✅ Ready for Android deployment with PyTorch Android!")

    # Print usage instructions
    print("\n" + "="*60)
    print("QUICK START FOR ANDROID")
    print("="*60)

    print("\n📱 This model works with PyTorch Android library")
    print("   Full guide created in: ANDROID_DEPLOYMENT_GUIDE.md")

    return 0

if __name__ == "__main__":
    sys.exit(main())
