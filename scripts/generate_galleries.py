import os
import json
import re

# ==========================================
# SITE CONFIGURATION
# ==========================================
SITE_SLUG = "grozrab"
MEDIA_SERVER_BASE = "https://files.groznet.com"
CONTENT_SECTION = "news"

# Path setup relative to script execution
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, f"../content/{CONTENT_SECTION}"))

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif', '.svg')

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def process_post(post_dir):
    # Relative path from content root (e.g., "2026/07/post-1")
    rel_post_path = os.path.relpath(post_dir, CONTENT_DIR).replace('\\', '/')
    
    # 1. Base URL for this post on the remote server
    post_remote_base = f"{MEDIA_SERVER_BASE}/{SITE_SLUG}/{CONTENT_SECTION}/{rel_post_path}"
    
    # 2. Find local featured image in post bundle root
    # (Matches any image directly inside post_dir, ignoring subfolders like images/)
    featured_img_name = None
    for entry in os.scandir(post_dir):
        if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS):
            featured_img_name = entry.name
            break  # Grab the first root image as featured
            
    featured_img_url = f"{post_remote_base}/{featured_img_name}" if featured_img_name else ""

    # 3. Scan local images/ folder for gallery images
    images_dir = os.path.join(post_dir, "images")
    gallery_images = []

    if os.path.exists(images_dir) and os.path.isdir(images_dir):
        for entry in os.scandir(images_dir):
            if entry.is_file() and entry.name.lower().endswith(IMAGE_EXTENSIONS):
                gallery_images.append(entry.name)

    # 4. Generate gallery.json if images exist or featured image is present
    if gallery_images or featured_img_url:
        gallery_images.sort(key=natural_sort_key)
        
        output_data = {
            "remote_base_url": f"{post_remote_base}/images/",
            "featured_image": featured_img_url,
            "images": gallery_images
        }

        json_path = os.path.join(post_dir, "gallery.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)

        print(f"✅ Generated: {CONTENT_SECTION}/{rel_post_path}/gallery.json ({len(gallery_images)} images)")

if __name__ == '__main__':
    print(f"🚀 Scanning local bundle media for site: [{SITE_SLUG}]...")
    
    if not os.path.exists(CONTENT_DIR):
        print(f"❌ Error: Content directory not found at {CONTENT_DIR}")
        exit(1)

    for root, dirs, files in os.walk(CONTENT_DIR):
        # Target folders containing markdown content (Page Bundles)
        if any(f.endswith('.md') and not f.startswith('_index') for f in files):
            process_post(root)