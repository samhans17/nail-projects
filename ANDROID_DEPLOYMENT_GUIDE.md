# Android Deployment Guide for RF-DETR Nail Segmentation

## ✅ Model Export Complete

Your RF-DETR model has been successfully exported for Android:

**File:** [`pytorch_mobile_models/rfdetr_nails.pt`](pytorch_mobile_models/rfdetr_nails.pt)
**Size:** 129.88 MB
**Format:** PyTorch Mobile (TorchScript)

---

## Why PyTorch Mobile Instead of TFLite?

RF-DETR is a complex transformer-based model that uses:
- Multi-scale deformable attention
- Vision transformer (DINOv2) backbone
- Advanced segmentation head

**These operations are not supported in TFLite**, but work perfectly with PyTorch Mobile.

**Advantages of PyTorch Mobile:**
- ✅ Full RF-DETR support (no operator limitations)
- ✅ Official Android support by Meta/PyTorch team
- ✅ Good performance with NNAPI acceleration
- ✅ Same accuracy as training
- ✅ Already optimized with TorchScript

---

## Android Studio Setup

### Step 1: Add Dependencies

Add to your `app/build.gradle`:

```gradle
android {
    ...
    packagingOptions {
        pickFirst 'lib/x86/libc++_shared.so'
        pickFirst 'lib/x86_64/libc++_shared.so'
        pickFirst 'lib/armeabi-v7a/libc++_shared.so'
        pickFirst 'lib/arm64-v8a/libc++_shared.so'
    }
}

dependencies {
    // PyTorch Android
    implementation 'org.pytorch:pytorch_android:2.1.0'
    implementation 'org.pytorch:pytorch_android_torchvision:2.1.0'

    // For camera
    implementation 'androidx.camera:camera-core:1.3.0'
    implementation 'androidx.camera:camera-camera2:1.3.0'
    implementation 'androidx.camera:camera-lifecycle:1.3.0'
    implementation 'androidx.camera:camera-view:1.3.0'
}
```

### Step 2: Copy Model to Assets

```bash
# In your nail-project directory
cp pytorch_mobile_models/rfdetr_nails.pt \
   /path/to/YourAndroidApp/app/src/main/assets/
```

Or in Android Studio:
1. Right-click on `app/src/main` folder
2. New → Folder → Assets Folder
3. Copy `rfdetr_nails.pt` into the assets folder

---

## Java/Kotlin Implementation

### Load Model (One-time, in Activity onCreate)

**Java:**
```java
import org.pytorch.Module;
import org.pytorch.Tensor;
import org.pytorch.IValue;
import org.pytorch.torchvision.TensorImageUtils;
import android.graphics.Bitmap;

public class MainActivity extends AppCompatActivity {
    private Module model;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Load model from assets
        try {
            model = Module.load(assetFilePath(this, "rfdetr_nails.pt"));
            Log.d("Model", "RF-DETR model loaded successfully");
        } catch (IOException e) {
            Log.e("Model", "Error loading model", e);
        }
    }

    private String assetFilePath(Context context, String assetName) throws IOException {
        File file = new File(context.getFilesDir(), assetName);
        if (file.exists() && file.length() > 0) {
            return file.getAbsolutePath();
        }

        try (InputStream is = context.getAssets().open(assetName)) {
            try (OutputStream os = new FileOutputStream(file)) {
                byte[] buffer = new byte[4 * 1024];
                int read;
                while ((read = is.read(buffer)) != -1) {
                    os.write(buffer, 0, read);
                }
                os.flush();
            }
            return file.getAbsolutePath();
        }
    }
}
```

**Kotlin:**
```kotlin
import org.pytorch.Module
import org.pytorch.Tensor
import org.pytorch.IValue
import org.pytorch.torchvision.TensorImageUtils
import android.graphics.Bitmap

class MainActivity : AppCompatActivity() {
    private lateinit var model: Module

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Load model
        try {
            model = Module.load(assetFilePath(this, "rfdetr_nails.pt"))
            Log.d("Model", "RF-DETR model loaded successfully")
        } catch (e: IOException) {
            Log.e("Model", "Error loading model", e)
        }
    }

    private fun assetFilePath(context: Context, assetName: String): String {
        val file = File(context.filesDir, assetName)
        if (file.exists() && file.length() > 0) {
            return file.absolutePath
        }

        context.assets.open(assetName).use { inputStream ->
            FileOutputStream(file).use { outputStream ->
                val buffer = ByteArray(4 * 1024)
                var read: Int
                while (inputStream.read(buffer).also { read = it } != -1) {
                    outputStream.write(buffer, 0, read)
                }
                outputStream.flush()
            }
        }
        return file.absolutePath
    }
}
```

### Run Inference

**Java:**
```java
public class NailSegmentation {
    private Module model;

    public List<NailMask> detectNails(Bitmap bitmap) {
        // 1. Resize image to model input size (432x432)
        Bitmap resized = Bitmap.createScaledBitmap(bitmap, 432, 432, true);

        // 2. Convert to tensor (normalized to [0, 1])
        Tensor inputTensor = TensorImageUtils.bitmapToFloat32Tensor(
            resized,
            new float[]{0, 0, 0},  // No normalization needed (model expects [0,1])
            new float[]{1, 1, 1}
        );

        // 3. Run inference
        IValue[] outputs = model.forward(IValue.from(inputTensor)).toTuple();

        // 4. Extract masks (last output, index 14)
        // Shape: [1, 200, 108, 108]
        Tensor maskTensor = outputs[14].toTensor();
        float[] maskData = maskTensor.getDataAsFloatArray();
        long[] maskShape = maskTensor.shape();  // [1, 200, 108, 108]

        // 5. Process masks
        int numDetections = (int) maskShape[1];  // 200
        int maskHeight = (int) maskShape[2];     // 108
        int maskWidth = (int) maskShape[3];      // 108

        List<NailMask> nailMasks = new ArrayList<>();

        for (int i = 0; i < numDetections; i++) {
            // Extract mask for detection i
            float[] singleMask = new float[maskHeight * maskWidth];
            System.arraycopy(
                maskData,
                i * maskHeight * maskWidth,
                singleMask,
                0,
                maskHeight * maskWidth
            );

            // Check if mask has significant values (threshold)
            float maxValue = getMaxValue(singleMask);
            if (maxValue > 0.5f) {  // Confidence threshold
                // Resize mask back to original image size
                Bitmap maskBitmap = arrayToGrayscaleBitmap(
                    singleMask, maskWidth, maskHeight
                );
                Bitmap resizedMask = Bitmap.createScaledBitmap(
                    maskBitmap,
                    bitmap.getWidth(),
                    bitmap.getHeight(),
                    true
                );

                nailMasks.add(new NailMask(resizedMask, maxValue));
            }
        }

        return nailMasks;
    }

    private float getMaxValue(float[] array) {
        float max = Float.MIN_VALUE;
        for (float value : array) {
            if (value > max) max = value;
        }
        return max;
    }

    private Bitmap arrayToGrayscaleBitmap(float[] data, int width, int height) {
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ALPHA_8);

        for (int y = 0; y < height; y++) {
            for (int x = 0; x < width; x++) {
                float value = data[y * width + x];
                int gray = (int) (Math.min(Math.max(value, 0), 1) * 255);
                bitmap.setPixel(x, y, Color.argb(gray, 0, 0, 0));
            }
        }

        return bitmap;
    }
}

class NailMask {
    Bitmap mask;
    float confidence;

    public NailMask(Bitmap mask, float confidence) {
        this.mask = mask;
        this.confidence = confidence;
    }
}
```

**Kotlin:**
```kotlin
class NailSegmentation(private val model: Module) {

    fun detectNails(bitmap: Bitmap): List<NailMask> {
        // 1. Resize to 432x432
        val resized = Bitmap.createScaledBitmap(bitmap, 432, 432, true)

        // 2. Convert to tensor
        val inputTensor = TensorImageUtils.bitmapToFloat32Tensor(
            resized,
            floatArrayOf(0f, 0f, 0f),
            floatArrayOf(1f, 1f, 1f)
        )

        // 3. Run inference
        val outputs = model.forward(IValue.from(inputTensor)).toTuple()

        // 4. Extract masks (index 14)
        val maskTensor = outputs[14].toTensor()
        val maskData = maskTensor.dataAsFloatArray
        val maskShape = maskTensor.shape()

        val numDetections = maskShape[1].toInt()  // 200
        val maskHeight = maskShape[2].toInt()     // 108
        val maskWidth = maskShape[3].toInt()      // 108

        // 5. Process masks
        return (0 until numDetections).mapNotNull { i ->
            val singleMask = maskData.copyOfRange(
                i * maskHeight * maskWidth,
                (i + 1) * maskHeight * maskWidth
            )

            val maxValue = singleMask.maxOrNull() ?: 0f

            if (maxValue > 0.5f) {
                val maskBitmap = arrayToGrayscaleBitmap(singleMask, maskWidth, maskHeight)
                val resizedMask = Bitmap.createScaledBitmap(
                    maskBitmap,
                    bitmap.width,
                    bitmap.height,
                    true
                )
                NailMask(resizedMask, maxValue)
            } else null
        }
    }

    private fun arrayToGrayscaleBitmap(data: FloatArray, width: Int, height: Int): Bitmap {
        val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ALPHA_8)

        for (y in 0 until height) {
            for (x in 0 until width) {
                val value = data[y * width + x]
                val gray = (value.coerceIn(0f, 1f) * 255).toInt()
                bitmap.setPixel(x, y, Color.argb(gray, 0, 0, 0))
            }
        }

        return bitmap
    }
}

data class NailMask(
    val mask: Bitmap,
    val confidence: Float
)
```

---

## Real-time Camera Integration

```kotlin
class CameraActivity : AppCompatActivity() {
    private lateinit var model: Module
    private lateinit var cameraExecutor: ExecutorService

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Load model
        model = Module.load(assetFilePath(this, "rfdetr_nails.pt"))

        // Setup camera
        cameraExecutor = Executors.newSingleThreadExecutor()
        startCamera()
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)

        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()

            val preview = Preview.Builder().build()
            val imageAnalyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, NailAnalyzer(model))
                }

            val cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(
                    this, cameraSelector, preview, imageAnalyzer
                )
            } catch (exc: Exception) {
                Log.e("Camera", "Binding failed", exc)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    private class NailAnalyzer(private val model: Module) : ImageAnalysis.Analyzer {
        override fun analyze(image: ImageProxy) {
            val bitmap = image.toBitmap()

            // Run inference
            val nailSegmentation = NailSegmentation(model)
            val masks = nailSegmentation.detectNails(bitmap)

            // Update UI with masks
            // ... overlay masks on camera preview

            image.close()
        }
    }
}
```

---

## Performance Tips

### 1. Use NNAPI Acceleration (Android 8.1+)
```java
// Enable NNAPI backend
model.setUseNNAPI(true);
```

### 2. Run on Background Thread
```java
ExecutorService executor = Executors.newSingleThreadExecutor();
executor.execute(() -> {
    List<NailMask> masks = detectNails(bitmap);
    // Update UI on main thread
    runOnUiThread(() -> displayMasks(masks));
});
```

### 3. Reduce Input Resolution
```java
// Use smaller resolution for faster inference
Bitmap resized = Bitmap.createScaledBitmap(bitmap, 320, 320, true);
```

### 4. Process Every N Frames
```kotlin
private var frameCount = 0

override fun analyze(image: ImageProxy) {
    frameCount++
    if (frameCount % 3 == 0) {  // Process every 3rd frame
        // Run inference
    }
    image.close()
}
```

---

## Testing Performance

Add this to measure inference time:

```java
long startTime = System.currentTimeMillis();
IValue[] outputs = model.forward(IValue.from(inputTensor)).toTuple();
long inferenceTime = System.currentTimeMillis() - startTime;

Log.d("Performance", "Inference time: " + inferenceTime + "ms");
Log.d("Performance", "FPS: " + (1000.0 / inferenceTime));
```

Expected performance:
- **High-end devices** (Snapdragon 8 Gen 2): ~200-300ms (~3-5 FPS)
- **Mid-range devices** (Snapdragon 7 series): ~500-800ms (~1-2 FPS)
- **Low-end devices**: ~1000ms+ (~1 FPS)

---

## Troubleshooting

### Model file too large?
The 130 MB model might be large for some apps. Options:
1. Use on-demand delivery (Android App Bundle)
2. Download model on first run
3. Compress model file in assets

### Out of memory?
```java
// Add to AndroidManifest.xml
<application
    android:largeHeap="true"
    ...>
```

### Slow inference?
- Enable NNAPI
- Reduce input resolution
- Process fewer frames
- Consider server-side inference

---

## Alternative: Server-Side Inference

If on-device inference is too slow, deploy the model on your backend:

### Android App (Client):
```kotlin
// Send image to server
val bitmap = captureImage()
val base64Image = bitmapToBase64(bitmap)

val retrofit = Retrofit.Builder()
    .baseUrl("http://your-server.com/")
    .addConverterFactory(GsonConverterFactory.create())
    .build()

val api = retrofit.create(NailAPI::class.java)
val response = api.detectNails(ImageRequest(base64Image)).execute()

// Display masks from server response
displayMasks(response.body()?.masks)
```

### Backend (Python FastAPI):
Your existing `backend/main.py` already has this implemented!

---

## Summary

### ✅ What You Have:
- **Model file:** `pytorch_mobile_models/rfdetr_nails.pt` (129.88 MB)
- **Format:** PyTorch Mobile (TorchScript)
- **Ready for:** Android deployment

### 📱 Next Steps:
1. Add PyTorch Android dependencies to your app
2. Copy model file to assets folder
3. Implement inference code (examples above)
4. Test on your device
5. Optimize performance as needed

### 📚 Resources:
- **PyTorch Mobile Docs:** https://pytorch.org/mobile/android/
- **Example App:** https://github.com/pytorch/android-demo-app
- **This project:** Use the code examples above

---

## Need Help?

- Check PyTorch Mobile documentation
- Test with smaller images first (320×320)
- Monitor memory usage in Android Profiler
- Consider hybrid approach (critical frames on-device, others on server)
