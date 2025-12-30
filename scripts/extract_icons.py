"""
Script to extract icons from a composite image.
The image contains multiple icon variations arranged in a grid.
The central icon is the main one.
"""
from PIL import Image
from pathlib import Path
import os

def extract_icons(source_path: str, output_dir: str):
    """Extract icons from composite image."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load source image
    img = Image.open(source_path)
    width, height = img.size
    print(f"Source image: {width}x{height}")
    
    # The image appears to be a 3x3 grid with the main icon in the center
    # Calculate cell size (assuming equal grid)
    # Based on typical Gemini-generated icon sheets, let's detect the grid
    
    # For a 3x3 grid:
    cell_width = width // 3
    cell_height = height // 3
    
    print(f"Grid cell size: {cell_width}x{cell_height}")
    
    # Define icon positions (row, col) and names
    positions = [
        (0, 0, "icon_topleft"),
        (0, 1, "icon_top"),
        (0, 2, "icon_topright"),
        (1, 0, "icon_left"),
        (1, 1, "icon_main"),      # Central = main
        (1, 2, "icon_right"),
        (2, 0, "icon_bottomleft"),
        (2, 1, "icon_bottom"),
        (2, 2, "icon_bottomright"),
    ]
    
    extracted = []
    
    for row, col, name in positions:
        # Calculate crop box
        left = col * cell_width
        top = row * cell_height
        right = left + cell_width
        bottom = top + cell_height
        
        # Crop icon
        icon = img.crop((left, top, right, bottom))
        
        # Save original size
        icon_path = output_path / f"{name}.png"
        icon.save(icon_path, "PNG")
        extracted.append(icon_path)
        print(f"Extracted: {name} ({cell_width}x{cell_height}) -> {icon_path}")
    
    # Generate PWA sizes from main icon
    main_icon = img.crop((
        cell_width,      # col 1
        cell_height,     # row 1
        cell_width * 2,  # to col 2
        cell_height * 2  # to row 2
    ))
    
    pwa_sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    pwa_dir = output_path / "pwa"
    pwa_dir.mkdir(exist_ok=True)
    
    for size in pwa_sizes:
        resized = main_icon.resize((size, size), Image.Resampling.LANCZOS)
        pwa_path = pwa_dir / f"icon-{size}x{size}.png"
        resized.save(pwa_path, "PNG")
        print(f"PWA icon: {size}x{size} -> {pwa_path}")
    
    print(f"\n✅ Done! Extracted {len(extracted)} icons")
    print(f"   PWA icons in: {pwa_dir}")
    
    return extracted


if __name__ == "__main__":
    source = r"f:\DD\Gemini_Generated_Image_i94s8ai94s8ai94s.png"
    output = r"f:\DD\frontend\public\icons"
    
    extract_icons(source, output)
