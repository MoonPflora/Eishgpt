import os
import time
import json
import requests
from PIL import Image, ImageOps, ImageFilter
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

# Configuration
load_dotenv('env/.env')
OCR_API_KEY = os.getenv('OCR_API_KEY')
BASE_DIR = Path('admin_jobs')
STATUS_FILE = BASE_DIR / 'ocr_status.json'

def load_status():
    """Load processing status with default values"""
    default_status = {
        "completed_jobs": [],
        "failed_images": {},
        "language": "eng"  # Start with English only
    }
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return {**default_status, **json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return default_status

def save_status(status):
    """Save current processing status"""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)

def enhance_phone_screenshot(img):
    """Special preprocessing for compressed phone screenshots"""
    # Convert to grayscale if not already
    if img.mode != 'L':
        img = img.convert('L')
    
    # Mild sharpening to compensate for compression
    img = img.filter(ImageFilter.SHARPEN)
    
    # Adaptive contrast enhancement
    img = ImageOps.autocontrast(img, cutoff=2)
    
    return img

def process_image(image_path):
    """Process single compressed screenshot through OCR"""
    try:
        with Image.open(image_path) as img:
            # Special preprocessing for phone screenshots
            img = enhance_phone_screenshot(img)
            
            # Always save as JPEG for API compatibility
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=85)
            img_bytes.seek(0)
            
            # OCR API call with explicit JPEG file type
            response = requests.post(
                'https://api.ocr.space/parse/image',
                files={'file': ('image.jpg', img_bytes, 'image/jpeg')},
                data={
                    'apikey': OCR_API_KEY,
                    'language': load_status()['language'],
                    'OCREngine': 2,
                    'detectOrientation': True,
                    'scale': True,
                    'isTable': False,
                    'filetype': 'JPG'  # Explicitly declare file type
                },
                timeout=30
            )
            
            result = response.json()
            if response.status_code != 200:
                print(f"API Error {response.status_code}")
                return None
                
            if result.get('OCRExitCode') != 1:
                print(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
                return None
                
            text = result['ParsedResults'][0]['ParsedText'].strip()
            return text if text else None
            
    except Exception as e:
        print(f"Processing Error: {str(e)}")
        return None

def process_job_folder(folder_path, status):
    """Process all screenshots in a job folder"""
    job_name = os.path.basename(folder_path)
    print(f"\nProcessing {job_name}...")
    
    if job_name in status["completed_jobs"]:
        print("Already completed")
        return True
        
    # Get all images (case-insensitive)
    images = []
    for f in os.listdir(folder_path):
        lower_f = f.lower()
        if lower_f.endswith(('.jpg', '.jpeg', '.png')):
            images.append(f)
    
    # Sort numerically (image_1.jpg, image_2.jpg, etc.)
    try:
        images.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    except:
        images.sort()  # Fallback alphabetical sort
    
    text_parts = []
    for image_file in images:
        image_path = os.path.join(folder_path, image_file)
        print(f"- {image_file}", end=' ')
        
        text = process_image(image_path)
        if text:
            text_parts.append(text)
            print("✓")
        else:
            print("✗")
        time.sleep(1)  # Rate limiting
    
    if text_parts:
        output_path = os.path.join(folder_path, 'job.txt')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(text_parts))
        status["completed_jobs"].append(job_name)
        print(f"Saved results to {output_path}")
        return True
        
    return False

def main():
    """Main processing loop"""
    status = load_status()
    print(f"Starting OCR processing (Language: {status['language']})...")
    
    try:
        # Process each job folder
        job_folders = [f for f in os.listdir(BASE_DIR) if f.startswith('job')]
        
        for job_folder in sorted(job_folders):
            folder_path = os.path.join(BASE_DIR, job_folder)
            if os.path.isdir(folder_path):  # Additional safety check
                if process_job_folder(folder_path, status):
                    print(f"Completed {job_folder}")
                else:
                    print(f"Failed {job_folder}")
                time.sleep(3)  # Delay between folders
            
    except KeyboardInterrupt:
        print("\nProcessing interrupted")
    finally:
        save_status(status)
        print("\nProcessing complete")

if __name__ == "__main__":
    main()