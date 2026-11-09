"""Generate 4 Synthetic Egyptian National ID Card Fixtures for Phase 1b.

Strict Synthetic Non-Real IDs Only — Zero authentic data.
Generated fixtures:
1. clean_synthetic_card.png (Clear, high-contrast, perfectly legible)
2. blurred_synthetic_card.png (Gaussian blurred, tests low-confidence alerts)
3. rotated_synthetic_card.png (Rotated 12 degrees, tests skew handling)
4. partially_obscured_synthetic_card.png (Glare/occlusion bar over address/ID)
"""

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_cards"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT_PATH = r"C:\Windows\Fonts\arial.ttf"

def create_base_synthetic_card() -> Image.Image:
    width, height = 850, 540
    # Create card background (Egyptian ID subtle gradient / pale green-gray)
    img = Image.new("RGB", (width, height), color=(242, 246, 243))
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rounded_rectangle([(15, 15), (width - 15, height - 15)], radius=18, outline=(180, 200, 190), width=3)
    draw.rounded_rectangle([(25, 25), (width - 25, height - 25)], radius=12, outline=(210, 225, 218), width=1)

    # Header bar
    draw.rectangle([(30, 30), (width - 30, 95)], fill=(225, 238, 230))
    draw.line([(30, 95), (width - 30, 95)], fill=(160, 190, 175), width=2)

    # Fonts
    title_font = ImageFont.truetype(FONT_PATH, 24)
    sub_font = ImageFont.truetype(FONT_PATH, 16)
    label_font = ImageFont.truetype(FONT_PATH, 15)
    nid_font = ImageFont.truetype(FONT_PATH, 26)
    body_font = ImageFont.truetype(FONT_PATH, 19)
    stamp_font = ImageFont.truetype(FONT_PATH, 14)

    # Header Text
    draw.text((width - 45, 40), "جمهورية مصر العربية", fill=(20, 60, 40), font=title_font, anchor="ra")
    draw.text((width - 45, 68), "بطاقة تحقيق الشخصية", fill=(40, 80, 55), font=sub_font, anchor="ra")
    draw.text((45, 50), "SYNTHETIC FIXTURE", fill=(160, 110, 30), font=stamp_font, anchor="la")

    # Photo placeholder
    photo_box = [(45, 120), (195, 310)]
    draw.rectangle(photo_box, fill=(215, 225, 220), outline=(170, 185, 180), width=2)
    draw.text((120, 215), "PHOTO\nFIXTURE", fill=(140, 155, 150), font=label_font, anchor="mm", align="center")

    # Citizen Details (Arabic synthetic fixtures)
    # 1. Name
    draw.text((width - 50, 130), "الاسم :", fill=(80, 100, 90), font=label_font, anchor="ra")
    draw.text((width - 50, 155), "أحمد منصور إبراهيم عبد الله", fill=(15, 25, 20), font=body_font, anchor="ra")

    # 2. Address
    draw.text((width - 50, 210), "العنوان :", fill=(80, 100, 90), font=label_font, anchor="ra")
    draw.text((width - 50, 235), "١٥ شارع طلعت حرب - قصر النيل - القاهرة", fill=(15, 25, 20), font=body_font, anchor="ra")

    # 3. National ID (14-digit synthetic Egyptian ID)
    draw.text((width - 50, 300), "الرقم القومي :", fill=(80, 100, 90), font=label_font, anchor="ra")
    # Draw with Western and Eastern digits
    draw.text((width - 50, 330), "29505140101234", fill=(10, 20, 15), font=nid_font, anchor="ra")

    # 4. Factory code
    draw.text((50, 360), "ED2676749", fill=(50, 70, 60), font=nid_font, anchor="la")

    # Watermark Notice across card
    draw.text((width // 2, height - 35), "FOR LOCAL SIMULATION ONLY — NEVER AN AUTHENTIC DOCUMENT", fill=(180, 100, 100), font=stamp_font, anchor="mm")

    return img

def main():
    base = create_base_synthetic_card()

    # 1. Clean
    clean_path = os.path.join(OUTPUT_DIR, "clean_synthetic_card.png")
    base.save(clean_path, format="PNG")
    print(f"Generated clean card: {clean_path}")

    # 2. Blurred
    blurred = base.filter(ImageFilter.GaussianBlur(radius=3.0))
    blurred_path = os.path.join(OUTPUT_DIR, "blurred_synthetic_card.png")
    blurred.save(blurred_path, format="PNG")
    print(f"Generated blurred card: {blurred_path}")

    # 3. Rotated
    rotated = base.rotate(12, expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
    rotated_path = os.path.join(OUTPUT_DIR, "rotated_synthetic_card.png")
    rotated.save(rotated_path, format="PNG")
    print(f"Generated rotated card: {rotated_path}")

    # 4. Partially Obscured
    obscured = base.copy()
    obs_draw = ImageDraw.Draw(obscured, "RGBA")
    # Draw a simulated dark/glare occlusion bar over the address line
    obs_draw.rectangle([(220, 220), (750, 270)], fill=(30, 30, 30, 220))
    obs_draw.text((485, 245), "DATA OBSCURED / UNREADABLE", fill=(255, 255, 255, 240), font=ImageFont.truetype(FONT_PATH, 16), anchor="mm")
    obscured_path = os.path.join(OUTPUT_DIR, "partially_obscured_synthetic_card.png")
    obscured.save(obscured_path, format="PNG")
    print(f"Generated partially obscured card: {obscured_path}")

if __name__ == "__main__":
    main()

