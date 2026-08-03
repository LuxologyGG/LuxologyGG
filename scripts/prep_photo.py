"""
Step 3a — Prep a photo for ASCII conversion.

1. Remove the background (rembg) so the subject is isolated.
2. Boost local contrast with CLAHE so a flat face gets real highlights/shadows.
3. Composite onto pure white so the background maps to the blank end of the
   ASCII ramp (white -> spaces).

Run once per photo:
    python scripts/prep_photo.py source-photo.png
"""
import sys
import io
import numpy as np
import cv2
from PIL import Image
from rembg import remove

def prep(in_path: str, out_path: str = "source-prepped.png"):
    with open(in_path, "rb") as f:
        input_bytes = f.read()

    # 1. Remove background -> RGBA with subject isolated
    cutout_bytes = remove(input_bytes)
    cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Boost local contrast with CLAHE (grayscale)
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    out = Image.fromarray(contrasted)
    out.save(out_path)
    print(f"wrote {out_path} ({out.size[0]}x{out.size[1]})")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.png"
    prep(src)
