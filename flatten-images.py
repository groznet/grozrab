import sys
import shutil
from pathlib import Path

ROOT = Path("content/news").resolve()

if not ROOT.exists():
    print(f"Error: Directory target does not exist -> {ROOT}")
    sys.exit(1)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp",
    ".gif", ".bmp", ".tif", ".tiff",
    ".avif", ".svg"
}

# Find all 'images' directories
images_dirs = [d for d in ROOT.rglob("images") if d.is_dir()]

print(f"Found {len(images_dirs)} target 'images' directories.")

for images_dir in images_dirs:
    # Find image files
    images = [
        f for f in images_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not images:
        print(f"Skipped (no matching images): {images_dir}")
        continue

    # Pick only the first image
    image = images[0]
    destination = images_dir.parent / image.name

    if destination.exists():
        print(f"Skipped file (already exists in destination): {destination}")
        continue

    try:
        shutil.move(str(image), str(destination))
        print(f"Moved 1 image: {image.name} -> {destination}")
    except Exception as e:
        print(f"Failed to move {image}: {e}")

    # Remove folder ONLY if it's completely empty now
    try:
        # Clear hidden files like .DS_Store
        for extra in images_dir.iterdir():
            if extra.is_file() and extra.name.startswith("."):
                extra.unlink()

        images_dir.rmdir()
        print(f"Removed empty folder: {images_dir}")
    except OSError:
        # Expected if other images/files remain inside
        pass

print("Done.")