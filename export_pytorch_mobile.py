"""
Export RF-DETR to PyTorch Mobile for Android
This is the recommended approach for deploying complex models on Android
"""

import torch
import os
import sys
from pathlib import Path

CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
OUTPUT_DIR = "./pytorch_mobile_models"

def main():
    print("\n" + "="*60)
    print("RF-DETR to PyTorch Mobile Export")
    print("="*60 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load model
    print("📦 Loading RF-DETR model...")
    from rfdetr import RFDETRSegPreview

    model = RFDETRSegPreview(pretrain_weights=CHECKPOINT_PATH)
    print("✅ Model loaded")

    # Optimize for inference (creates TorchScript traced model)
    print("\n⚡ Optimizing for inference...")
    model.optimize_for_inference()
    print("✅ Model optimized")

    # Get the traced model
    if hasattr(model, 'model') and hasattr(model.model, 'inference_model'):
        traced_model = model.model.inference_model
        print("✅ Got traced model")
    else:
        print("❌ Could not get traced model")
        return 1

    # Export for mobile
    mobile_path = os.path.join(OUTPUT_DIR, "rfdetr_nails_mobile.ptl")
    print(f"\n📤 Exporting to PyTorch Mobile: {mobile_path}")

    try:
        # Optimize for mobile
        from torch.utils.mobile_optimizer import optimize_for_mobile

        optimized_model = optimize_for_mobile(traced_model)

        # Save
        optimized_model._save_for_lite_interpreter(mobile_path)

        print("✅ PyTorch Mobile export successful!")

        # Check file size
        file_size_mb = os.path.getsize(mobile_path) / (1024 * 1024)
        print(f"📊 Model size: {file_size_mb:.2f} MB")

        # Test the model
        print("\n🧪 Testing model...")
        test_input = torch.randn(1, 3, 432, 432)

        # Load mobile model
        mobile_model = torch.jit.load(mobile_path)

        # Run inference
        import time
        start = time.time()
        with torch.no_grad():
            output = mobile_model(test_input)
        inference_time = (time.time() - start) * 1000

        print(f"✅ Model test successful!")
        print(f"   Inference time: {inference_time:.2f} ms")
        print(f"   FPS: {1000/inference_time:.1f}")

        if isinstance(output, (tuple, list)):
            print(f"   Number of outputs: {len(output)}")
            for i, out in enumerate(output[:3]):
                if isinstance(out, torch.Tensor):
                    print(f"   Output {i} shape: {out.shape}")

        print("\n" + "="*60)
        print("🎉 EXPORT SUCCESSFUL!")
        print("="*60)
        print(f"\n📁 Output file: {mobile_path}")
        print(f"📊 Size: {file_size_mb:.2f} MB")

        # Print Android integration instructions
        print("\n" + "="*60)
        print("ANDROID INTEGRATION INSTRUCTIONS")
        print("="*60)

        print("\n1️⃣ Add PyTorch Android dependencies to build.gradle:")
        print("""
dependencies {
    implementation 'org.pytorch:pytorch_android:2.0.0'
    implementation 'org.pytorch:pytorch_android_torchvision:2.0.0'
}
""")

        print("\n2️⃣ Copy model to Android assets:")
        print(f"   cp {mobile_path} YourAndroidApp/app/src/main/assets/")

        print("\n3️⃣ Load and run model in Android (Java/Kotlin):")
        print("""
// Java
import org.pytorch.Module;
import org.pytorch.Tensor;
import org.pytorch.torchvision.TensorImageUtils;

// Load model
Module model = Module.load(assetFilePath(this, "rfdetr_nails_mobile.ptl"));

// Prepare input (normalize to [0,1])
Tensor inputTensor = TensorImageUtils.bitmapToFloat32Tensor(
    bitmap,
    TensorImageUtils.TORCHVISION_NORM_MEAN_RGB,
    TensorImageUtils.TORCHVISION_NORM_STD_RGB
);

// Run inference
Tensor[] outputs = model.forward(IValue.from(inputTensor)).toTuple();

// Process outputs
// outputs[14] contains masks (1, 200, 108, 108)
// outputs[0-12] contain detection outputs
""")

        print("\n4️⃣ Preprocessing image:")
        print("""
// Resize image to 432x432
Bitmap resized = Bitmap.createScaledBitmap(original, 432, 432, true);

// Convert to tensor (automatically normalizes to [0,1])
Tensor input = TensorImageUtils.bitmapToFloat32Tensor(resized, ...)
""")

        print("\n5️⃣ Post-processing outputs:")
        print("""
// The model returns 15 outputs (tuple)
// - outputs[0-12]: Various detection outputs
// - outputs[13]: Something else
// - outputs[14]: Segmentation masks [1, 200, 108, 108]

float[] maskData = outputs[14].getDataAsFloatArray();
long[] maskShape = outputs[14].shape(); // [1, 200, 108, 108]
""")

        print("\n📚 Full documentation:")
        print("   https://pytorch.org/mobile/android/")

        print("\n✅ Your model is ready for Android deployment!")

        return 0

    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
