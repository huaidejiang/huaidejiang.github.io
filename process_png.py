from PIL import Image

def crop_to_content(input_path, output_path=None):
    """Extract non-transparent region and crop to minimal bounding box."""
    if output_path is None:
        output_path = input_path

    img = Image.open(input_path).convert("RGBA")
    bbox = img.getbbox()  # returns (left, upper, right, lower) of non-zero region
    if bbox is None:
        print("Image is fully transparent, nothing to crop.")
        return
    cropped = img.crop(bbox)
    cropped.save(output_path)
    print(f"Cropped from {img.size} to {cropped.size}, saved to {output_path}")

# Usage
crop_to_content("E:\\Personal_Website\\huaidejiang.github.io\\assets\\img\\nus_logo_old.png", "E:\\Personal_Website\\huaidejiang.github.io\\assets\\img\\nus_logo.png")