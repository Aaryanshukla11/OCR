import sys
import os
import time

# Set env flags to disable oneDNN / mkldnn in paddle fluid
os.environ['FLAGS_use_onednn'] = '0'
os.environ['FLAGS_use_mkldnn'] = '0'
os.environ['FLAGS_enable_onednn'] = '0'
os.environ['PADDLE_DISABLE_ONEDNN'] = '1'
os.environ['FLAGS_enable_pir_api'] = '0'
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

from PIL import Image, ImageDraw

def test_paddle():
    print("Testing PaddleOCR 3.7.0 imports...")
    import paddle
    
    # Disable MKLDNN programmatically in Paddle if available
    try:
        paddle.fluid.core.set_paddle_lib_path('')
    except Exception:
        pass

    from paddleocr import PaddleOCR
    
    device_use = "GPU" if paddle.is_compiled_with_cuda() and paddle.device.get_device().startswith("gpu") else "CPU"
    print(f"Paddle device: {device_use}")
    
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 40), "Invoice No: INV-1024", fill=(0, 0, 0))
    draw.text((30, 100), "Total: INR 50000", fill=(0, 0, 0))
    
    test_img_path = "test_sample.png"
    img.save(test_img_path)
    
    print("Initializing PaddleOCR...")
    start_t = time.time()
    # Try passing enable_mkldnn=False if supported
    try:
        ocr = PaddleOCR(lang='en', enable_mkldnn=False)
    except Exception:
        ocr = PaddleOCR(lang='en')
        
    init_t = time.time() - start_t
    print(f"PaddleOCR initialized in {init_t:.2f}s")
    
    print("Running OCR on test image...")
    t0 = time.time()
    result = ocr.ocr(test_img_path)
    t1 = time.time() - t0
    print(f"OCR execution took {t1:.4f}s")
    
    print("Result structure:")
    print(f"Result type: {type(result)}, length: {len(result) if result else 0}")
    if result:
        print("Raw result:", result)
        
    if os.path.exists(test_img_path):
        os.remove(test_img_path)

if __name__ == "__main__":
    test_paddle()
