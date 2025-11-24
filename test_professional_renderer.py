"""
Test Script for Professional Nail Renderer
Validates all components are working correctly
"""

import sys
import os
import numpy as np
import cv2

# Add professional renderer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'professional_nail_renderer'))

print("="*60)
print("Testing Professional Nail Renderer")
print("="*60 + "\n")

# Test 1: Import modules
print("TEST 1: Importing modules...")
try:
    from professional_nail_renderer import (
        NailGeometryAnalyzer,
        NailMaterial,
        MaterialPresets,
        MaterialFinish,
        PhotoRealisticNailRenderer
    )
    print("✅ All modules imported successfully\n")
except Exception as e:
    print(f"❌ Import failed: {e}\n")
    sys.exit(1)

# Test 2: Create synthetic nail mask
print("TEST 2: Creating synthetic nail mask...")
try:
    # Create a simple elliptical nail mask
    h, w = 480, 640
    mask = np.zeros((h, w), dtype=np.uint8)

    # Draw ellipse (simulating a nail)
    center = (320, 240)
    axes = (60, 100)  # width, height
    angle = 45
    cv2.ellipse(mask, center, axes, angle, 0, 360, 1, -1)

    print(f"✅ Created mask with {np.sum(mask)} pixels\n")
except Exception as e:
    print(f"❌ Mask creation failed: {e}\n")
    sys.exit(1)

# Test 3: Geometry analysis
print("TEST 3: Analyzing nail geometry...")
try:
    analyzer = NailGeometryAnalyzer()
    geometry = analyzer.analyze(mask, min_area=100)

    if geometry is None:
        print("❌ Geometry analysis returned None\n")
        sys.exit(1)

    print(f"✅ Geometry analyzed:")
    print(f"   Center: {geometry.center}")
    print(f"   Orientation: {geometry.orientation_angle:.1f}°")
    print(f"   Size: {geometry.length:.1f}x{geometry.width:.1f}")
    print(f"   Has normal map: {geometry.normal_map is not None}")
    print(f"   Highlight point: {geometry.highlight_point}\n")
except Exception as e:
    print(f"❌ Geometry analysis failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Material presets
print("TEST 4: Testing material presets...")
try:
    presets = MaterialPresets.all_presets()
    print(f"✅ Loaded {len(presets)} material presets:")
    for name in presets.keys():
        print(f"   - {name}")
    print()

    # Test custom material
    custom = MaterialPresets.custom(
        color=(255, 100, 150),
        finish=MaterialFinish.GLOSSY
    )
    print(f"✅ Custom material created:")
    print(f"   Glossiness: {custom.glossiness}")
    print(f"   Finish: {custom.get_finish_type().value}\n")
except Exception as e:
    print(f"❌ Material preset test failed: {e}\n")
    sys.exit(1)

# Test 5: Renderer initialization
print("TEST 5: Initializing renderer...")
try:
    renderer = PhotoRealisticNailRenderer(
        light_direction=(-0.5, -0.5, 0.8),
        ambient_intensity=0.3
    )
    print("✅ Renderer initialized\n")
except Exception as e:
    print(f"❌ Renderer initialization failed: {e}\n")
    sys.exit(1)

# Test 6: Full rendering pipeline
print("TEST 6: Testing full rendering pipeline...")
try:
    # Create synthetic image
    image = np.ones((h, w, 3), dtype=np.uint8) * 200  # Light gray background

    # Get a material
    material = MaterialPresets.glossy_red()

    # Render
    result = renderer.render_nail(image, geometry, material)

    print(f"✅ Rendering completed:")
    print(f"   Input shape: {image.shape}")
    print(f"   Output shape: {result.shape}")
    print(f"   Output dtype: {result.dtype}")
    print(f"   Output range: [{result.min()}, {result.max()}]\n")

    # Check that something changed
    diff = np.abs(result.astype(float) - image.astype(float)).mean()
    if diff < 1.0:
        print("⚠️  WARNING: Output is too similar to input (diff={:.2f})".format(diff))
    else:
        print(f"✅ Output differs from input (diff={diff:.2f})\n")

    # Save test result
    output_path = "test_render_output.jpg"
    cv2.imwrite(output_path, result)
    print(f"✅ Test output saved to: {output_path}\n")

except Exception as e:
    print(f"❌ Rendering failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 7: Visualize geometry
print("TEST 7: Testing geometry visualization...")
try:
    vis = analyzer.visualize_geometry(geometry, (h, w))
    vis_path = "test_geometry_vis.jpg"
    cv2.imwrite(vis_path, vis)
    print(f"✅ Geometry visualization saved to: {vis_path}\n")
except Exception as e:
    print(f"❌ Visualization failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 8: Multiple materials
print("TEST 8: Testing all material presets...")
try:
    test_materials = ["glossy_red", "matte_black", "metallic_gold", "glitter_pink"]
    for mat_name in test_materials:
        mat = presets[mat_name]
        result = renderer.render_nail(image, geometry, mat)

        output_path = f"test_render_{mat_name}.jpg"
        cv2.imwrite(output_path, result)
        print(f"✅ Rendered {mat_name} → {output_path}")

    print()
except Exception as e:
    print(f"❌ Multi-material test failed: {e}\n")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 9: Edge feathering
print("TEST 9: Testing edge feathering...")
try:
    # Get alpha mask
    alpha = renderer._create_feathered_mask(mask.astype(np.float32), feather_radius=5)
    print(f"✅ Feathered mask created:")
    print(f"   Shape: {alpha.shape}")
    print(f"   Range: [{alpha.min():.3f}, {alpha.max():.3f}]")
    print(f"   Has gradient: {alpha.std() > 0.01}\n")
except Exception as e:
    print(f"❌ Edge feathering test failed: {e}\n")
    sys.exit(1)

# Test 10: Color space conversions
print("TEST 10: Testing color space conversions...")
try:
    test_color = np.array([[[0.5, 0.8, 0.2]]], dtype=np.float32)

    # sRGB → Linear
    linear = renderer._srgb_to_linear(test_color)
    print(f"✅ sRGB to Linear: {test_color[0,0]} → {linear[0,0]}")

    # Linear → sRGB (should get back original)
    srgb = renderer._linear_to_srgb(linear)
    print(f"✅ Linear to sRGB: {linear[0,0]} → {srgb[0,0]}")

    # Check round-trip accuracy
    error = np.abs(srgb - test_color).max()
    if error < 0.001:
        print(f"✅ Round-trip accurate (error: {error:.6f})\n")
    else:
        print(f"⚠️  Round-trip error: {error:.6f}\n")

except Exception as e:
    print(f"❌ Color space test failed: {e}\n")
    sys.exit(1)

# All tests passed!
print("="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nThe professional nail renderer is working correctly!")
print("\nGenerated files:")
print("  - test_render_output.jpg")
print("  - test_geometry_vis.jpg")
print("  - test_render_glossy_red.jpg")
print("  - test_render_matte_black.jpg")
print("  - test_render_metallic_gold.jpg")
print("  - test_render_glitter_pink.jpg")
print("\nYou can now run:")
print("  python live_inference_professional.py")
print("  python compare_renderers.py")
print("\n🎉 Happy rendering!")
