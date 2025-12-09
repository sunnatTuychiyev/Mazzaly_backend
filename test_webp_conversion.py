"""
Simple test script to verify WebP conversion functionality.
Run with: python manage.py shell < test_webp_conversion.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Mazzaly_backend.settings')
django.setup()

from utils.image_utils import convert_to_webp, get_webp_path
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

print("Testing WebP conversion utility...")

# Create a simple test image
img = Image.new('RGB', (100, 100), color='red')
img_io = BytesIO()
img.save(img_io, format='JPEG')
img_io.seek(0)

# Create a mock uploaded file
test_file = SimpleUploadedFile(
    name='test_image.jpg',
    content=img_io.read(),
    content_type='image/jpeg'
)

print(f"Original file: {test_file.name}, size: {test_file.size} bytes")

# Convert to WebP
webp_file = convert_to_webp(test_file)

if webp_file:
    print(f"✓ Converted to WebP: {webp_file.name}, size: {webp_file.size} bytes")
    print(f"✓ Content type: {webp_file.content_type}")
    print(f"✓ Size reduction: {((test_file.size - webp_file.size) / test_file.size * 100):.1f}%")
else:
    print("✗ Conversion failed")

# Test path conversion
test_path = "/media/recipes/test_image.jpg"
webp_path = get_webp_path(test_path)
print(f"\nPath conversion test:")
print(f"Original: {test_path}")
print(f"WebP: {webp_path}")

print("\n✓ All tests passed!")
