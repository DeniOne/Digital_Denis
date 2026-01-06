import os
from PIL import Image

# Source image
source_path = r"C:/Users/DeniOne/.gemini/antigravity/brain/56a1ba56-37b7-49f9-ae9b-e73de4d15f3f/uploaded_image_1767707270369.jpg"
# Destination directory
dest_dir = r"f:/DD/frontend/public/icons/pwa/" # Need to make sure this path matches what's in manifest, which seems to be /icons/pwa/

if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

sizes = [72, 96, 128, 144, 152, 192, 384, 512]

try:
    with Image.open(source_path) as img:
        # Convert to RGB if necessary (e.g. if source is RGBA and saving as PNG, though PNG supports RGBA)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        for size in sizes:
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            file_name = f"icon-{size}x{size}.png"
            save_path = os.path.join(dest_dir, file_name)
            resized_img.save(save_path, "PNG")
            print(f"Saved {save_path}")
            
    print("All icons generated successfully.")
except Exception as e:
    print(f"Error generating icons: {e}")
