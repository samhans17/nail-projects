"""
RF-DETR Segmentation Model to TFLite Conversion Script
Loads checkpoint with exact training configuration and exports to TFLite
"""

import torch
import os
import sys
from pathlib import Path

# Configuration from checkpoint inspection
CHECKPOINT_PATH = "/home/usama-naveed/nail_AR-rfdeter/output/checkpoint_best_total.pth"
OUTPUT_DIR = "./tflite_models"

def load_checkpoint_config():
    """Load and return the configuration from checkpoint"""
    print("📦 Loading checkpoint...")
    checkpoint = torch.load(CHECKPOINT_PATH, map_location='cpu', weights_only=False)

    if 'args' not in checkpoint:
        raise ValueError("Checkpoint does not contain 'args' key with configuration")

    args = checkpoint['args']
    print("✅ Checkpoint loaded successfully")

    # Print key configuration
    print("\n" + "="*60)
    print("MODEL CONFIGURATION:")
    print("="*60)
    print(f"  Encoder: {args.encoder}")
    print(f"  Num queries: {args.num_queries}")
    print(f"  Group DETR: {args.group_detr}")
    print(f"  Actual queries: {args.num_queries * args.group_detr}")
    print(f"  Patch size: {args.patch_size}")
    print(f"  Resolution: {args.resolution}")
    print(f"  Hidden dim: {args.hidden_dim}")
    print(f"  Num classes: {args.num_classes}")
    print(f"  Segmentation head: {args.segmentation_head}")
    print(f"  Decoder layers: {args.dec_layers}")
    print("="*60 + "\n")

    return checkpoint, args

def create_model_from_config(args):
    """Create RF-DETR model instance with exact configuration from checkpoint"""
    print("🔨 Creating model with checkpoint configuration...")

    try:
        from rfdetr import RFDETRSegPreview
    except ImportError:
        print("❌ rfdetr library not found. Installing...")
        os.system("pip install rfdetr")
        from rfdetr import RFDETRSegPreview

    # Create model instance WITHOUT loading pretrain weights (we'll load from checkpoint)
    # We need to pass the key parameters that affect architecture
    model = RFDETRSegPreview(
        pretrain_weights=None,  # Don't load default weights
        num_queries=args.num_queries,
        group_detr=args.group_detr,
        encoder=args.encoder,
        patch_size=args.patch_size,
        resolution=args.resolution,
        hidden_dim=args.hidden_dim,
        num_classes=args.num_classes,
        dec_layers=args.dec_layers,
        segmentation_head=args.segmentation_head,
    )

    print("✅ Model instance created")
    return model

def load_checkpoint_weights(model, checkpoint):
    """Load weights from checkpoint into model"""
    print("⚙️ Loading checkpoint weights...")

    # Get the underlying model
    if hasattr(model, 'model'):
        target_model = model.model
    else:
        target_model = model

    # Load state dict
    state_dict = checkpoint['model']
    missing_keys, unexpected_keys = target_model.load_state_dict(state_dict, strict=False)

    if missing_keys:
        print(f"⚠️ Missing keys: {len(missing_keys)}")
        if len(missing_keys) < 10:
            for key in missing_keys:
                print(f"    - {key}")

    if unexpected_keys:
        print(f"⚠️ Unexpected keys: {len(unexpected_keys)}")
        if len(unexpected_keys) < 10:
            for key in unexpected_keys:
                print(f"    - {key}")

    print("✅ Weights loaded successfully")
    return model

def export_to_onnx(model, resolution, output_path):
    """Export model to ONNX format"""
    print(f"\n📤 Exporting to ONNX: {output_path}")

    # Get the underlying PyTorch model (NOT the TorchScript traced version)
    if hasattr(model, 'model') and hasattr(model.model, 'model'):
        export_model = model.model.model  # Get the actual PyTorch module
        print("  Using model.model.model (PyTorch eager mode) for export")
    elif hasattr(model, 'model'):
        export_model = model.model
        print("  Using model.model for export")
    else:
        export_model = model
        print("  Using model directly for export")

    # Set to eval mode
    if hasattr(export_model, 'eval'):
        export_model.eval()
        print("  Model set to eval mode")

    # Create dummy input with the training resolution
    dummy_input = torch.randn(1, 3, resolution, resolution)

    print(f"  Input shape: {dummy_input.shape}")
    print(f"  Model type: {type(export_model)}")
    print(f"  Model class: {export_model.__class__.__name__}")
    print("  Exporting...")

    try:
        with torch.no_grad():
            # Use dynamo=False to use the legacy (more stable) ONNX exporter
            torch.onnx.export(
                export_model,
                dummy_input,
                output_path,
                export_params=True,
                opset_version=18,  # Use opset 18 for bicubic upsampling support
                do_constant_folding=True,
                input_names=['images'],
                output_names=['output'],  # Use generic output name as model may have multiple outputs
                verbose=False,
                dynamo=False  # Use legacy exporter (more stable for complex models)
            )

        print("✅ ONNX export successful!")

        # Validate ONNX model
        import onnx
        onnx_model = onnx.load(output_path)
        onnx.checker.check_model(onnx_model)
        print("✅ ONNX model is valid")

        # Print model info
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"📊 ONNX model size: {file_size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"❌ ONNX export failed: {e}")
        print(f"\nModel structure debug info:")
        print(f"  model type: {type(model)}")
        if hasattr(model, 'model'):
            print(f"  model.model type: {type(model.model)}")
            if hasattr(model.model, 'model'):
                print(f"  model.model.model type: {type(model.model.model)}")
        import traceback
        traceback.print_exc()
        return False

def convert_onnx_to_tflite(onnx_path, output_path):
    """Convert ONNX model to TFLite using onnx2tf"""
    print(f"\n🔄 Converting ONNX to TFLite: {output_path}")

    # Check if onnx2tf is installed
    try:
        import subprocess
        result = subprocess.run(['onnx2tf', '--version'], capture_output=True)
        if result.returncode != 0:
            raise FileNotFoundError
    except FileNotFoundError:
        print("⚙️ Installing onnx2tf...")
        os.system("pip install -q onnx2tf")

    # Create temporary directory for SavedModel
    saved_model_dir = os.path.join(OUTPUT_DIR, "tf_saved_model")

    print("  Step 1: Converting ONNX to TensorFlow SavedModel...")
    result = subprocess.run([
        'onnx2tf',
        '-i', onnx_path,
        '-o', saved_model_dir,
        '-osd'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ ONNX to TensorFlow conversion failed:")
        print(result.stderr)
        return False

    print("✅ SavedModel created")

    # Convert SavedModel to TFLite with Float16 quantization
    print("  Step 2: Converting SavedModel to TFLite (Float16)...")

    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.target_spec.supported_types = [tf.float16]

    try:
        tflite_model = converter.convert()

        # Save TFLite model
        with open(output_path, 'wb') as f:
            f.write(tflite_model)

        print("✅ TFLite model created!")

        # Compare sizes
        onnx_size = os.path.getsize(onnx_path) / (1024 * 1024)
        tflite_size = os.path.getsize(output_path) / (1024 * 1024)

        print(f"\n📊 Model Size Comparison:")
        print(f"  ONNX (Float32):   {onnx_size:.2f} MB")
        print(f"  TFLite (Float16): {tflite_size:.2f} MB")
        print(f"  Size reduction:   {(1 - tflite_size/onnx_size)*100:.1f}%")

        return True

    except Exception as e:
        print(f"❌ TFLite conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main conversion pipeline"""
    print("\n" + "="*60)
    print("RF-DETR to TFLite Conversion")
    print("="*60 + "\n")

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Step 1: Load checkpoint and config
    checkpoint, args = load_checkpoint_config()

    # Step 2: Create model with correct architecture
    print("\n⚠️ Note: Model creation with custom parameters may not be supported")
    print("Attempting to use RFDETRSegPreview directly with checkpoint...\n")

    try:
        from rfdetr import RFDETRSegPreview

        # Try loading directly with checkpoint path
        # RFDETRSegPreview should handle the configuration automatically
        print("🔨 Loading model with RFDETRSegPreview...")
        model = RFDETRSegPreview(pretrain_weights=CHECKPOINT_PATH)
        # DO NOT optimize for inference as it creates TorchScript which can't be exported to ONNX
        # model.optimize_for_inference()
        print("✅ Model loaded (keeping as eager mode for ONNX export)")

    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("\nThe model architecture in the checkpoint doesn't match RFDETRSegPreview defaults.")
        print("This requires manual model creation with exact parameters.")
        return 1

    # Step 3: Export to ONNX
    onnx_path = os.path.join(OUTPUT_DIR, "rfdetr_nails.onnx")

    success = export_to_onnx(model, args.resolution, onnx_path)
    if not success:
        print("\n❌ Conversion pipeline failed at ONNX export")
        return 1

    # Step 4: Convert to TFLite
    tflite_path = os.path.join(OUTPUT_DIR, "rfdetr_nails_float16.tflite")

    success = convert_onnx_to_tflite(onnx_path, tflite_path)
    if not success:
        print("\n❌ Conversion pipeline failed at TFLite conversion")
        return 1

    # Success!
    print("\n" + "="*60)
    print("🎉 CONVERSION COMPLETE!")
    print("="*60)
    print(f"\n📁 Output files:")
    print(f"  ONNX:   {onnx_path}")
    print(f"  TFLite: {tflite_path}")
    print("\n✅ Your model is ready for deployment!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
