"""
Image utility functions for converting and optimizing images to WebP format.
"""
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import os


def convert_to_webp(image_field, quality=85):
    """
    Convert an uploaded image to WebP format.
    
    Args:
        image_field: Django ImageField or uploaded file
        quality: WebP quality (1-100, default 85)
    
    Returns:
        InMemoryUploadedFile: WebP image ready to save
    """
    if not image_field:
        return None
    
    # Open the image
    img = Image.open(image_field)
    
    # Convert RGBA to RGB if necessary (WebP supports both, but RGB is more compatible)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Save to BytesIO as WebP
    output = BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)
    
    # Get original filename and change extension to .webp
    original_name = getattr(image_field, 'name', 'image.webp')
    name_without_ext = os.path.splitext(original_name)[0]
    webp_name = f"{name_without_ext}.webp"
    
    # Create InMemoryUploadedFile
    webp_file = InMemoryUploadedFile(
        output,
        'ImageField',
        webp_name,
        'image/webp',
        output.getbuffer().nbytes,
        None
    )
    
    return webp_file


def get_webp_path(image_path):
    """
    Convert an image path to WebP path.
    
    Args:
        image_path: Original image path
    
    Returns:
        str: Path with .webp extension
    """
    if not image_path:
        return None
    
    name_without_ext = os.path.splitext(image_path)[0]
    return f"{name_without_ext}.webp"
