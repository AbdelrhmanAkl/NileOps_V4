"""Generate NEW Held-Out 60 Synthetic Egyptian National ID Cards for Handbook KYC Exception Evaluation.

Uses the UNCHANGED generator logic from scratch/generate_b1_synthetic_cards.py.
Generates 30 Clean and 30 Planted Exception cards with a brand new seed/data partition.
Output saved to data/synthetic_cards/eval_held_out_60/.
"""

import json
import os
import sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_cards", "eval_held_out_60"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_font_path(name='arial.ttf'):
    windir = os.environ.get('WINDIR', r'C:\Windows')
    candidates = [
        os.path.join(windir, 'Fonts', name),
        os.path.join(windir, 'Fonts', 'arial.ttf'),
        os.path.join(windir, 'Fonts', 'tahoma.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

FONT_PATH = get_font_path('arial.ttf')
BOLD_FONT_PATH = get_font_path('arialbd.ttf') or FONT_PATH

def resolve_font(name='arial.ttf', size=24):
    p = get_font_path(name)
    if p and os.path.exists(p):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()



def render_ar(text: str) -> str:
    """Reshape and reorder Arabic text for proper RTL rendering with Pillow."""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def draw_synthetic_card(
    name: str = "",
    address: str = "",
    national_id: str = "",
    factory_code: str = "ED2676749",
    blur_radius: float = 0.0,
    brightness: float = 1.0,
    obscure_id: bool = False,
    obscure_address: bool = False,
    obscure_name: bool = False,
) -> Image.Image:
    width, height = 850, 540
    img = Image.new("RGB", (width, height), color=(244, 247, 245))
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rounded_rectangle([(15, 15), (width - 15, height - 15)], radius=18, outline=(180, 200, 190), width=3)
    draw.rounded_rectangle([(25, 25), (width - 25, height - 25)], radius=12, outline=(210, 225, 218), width=1)

    # Header bar
    draw.rectangle([(30, 30), (width - 30, 95)], fill=(225, 238, 230))
    draw.line([(30, 95), (width - 30, 95)], fill=(160, 190, 175), width=2)

    title_font = resolve_font("arialbd.ttf", 24)
    sub_font = resolve_font('arial.ttf', 16)
    label_font = resolve_font("arial.ttf", 15)
    nid_font = resolve_font('arialbd.ttf', 26)
    body_font = resolve_font('arial.ttf', 20)
    stamp_font = resolve_font("arialbd.ttf", 13)

    # Header
    draw.text((width - 45, 38), render_ar("جمهورية مصر العربية"), fill=(20, 60, 40), font=title_font, anchor="ra")
    draw.text((width - 45, 68), render_ar("بطاقة تحقيق الشخصية"), fill=(40, 80, 55), font=sub_font, anchor="ra")
    draw.text((45, 50), "SYNTHETIC HELD-OUT", fill=(160, 110, 30), font=stamp_font, anchor="la")

    # Photo Box
    photo_box = [(45, 120), (195, 310)]
    draw.rectangle(photo_box, fill=(215, 225, 220), outline=(170, 185, 180), width=2)
    draw.text((120, 215), "PHOTO\nHELD-OUT", fill=(140, 155, 150), font=label_font, anchor="mm", align="center")

    # 1. Citizen Name
    if name and not obscure_name:
        draw.text((width - 50, 125), render_ar("الاسم :"), fill=(80, 100, 90), font=label_font, anchor="ra")
        draw.text((width - 50, 150), render_ar(name), fill=(15, 25, 20), font=body_font, anchor="ra")

    # 2. Residential Address
    if address and not obscure_address:
        draw.text((width - 50, 205), render_ar("العنوان :"), fill=(80, 100, 90), font=label_font, anchor="ra")
        draw.text((width - 50, 230), render_ar(address), fill=(15, 25, 20), font=body_font, anchor="ra")

    # 3. National ID
    if national_id and not obscure_id:
        draw.text((width - 50, 295), render_ar("الرقم القومي :"), fill=(80, 100, 90), font=label_font, anchor="ra")
        draw.text((width - 50, 325), national_id, fill=(10, 20, 15), font=nid_font, anchor="ra")

    # 4. Factory Code
    if factory_code:
        draw.text((50, 360), factory_code, fill=(50, 70, 60), font=nid_font, anchor="la")

    # Footer Disclaimer
    draw.text((width // 2, height - 35), "HELD-OUT SYNTHETIC DATASET — NEVER AN AUTHENTIC DOCUMENT", fill=(180, 100, 100), font=stamp_font, anchor="mm")

    # Postprocessing (blur, brightness)
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    return img


NEW_CLEAN_SPECS = [
    {"id": "ho_clean_01", "name": "سامي عبد الله فؤاد ناصر", "address": "١٢ شارع الجمهورية عابدين القاهرة", "nid": "29403210101567", "dob": "1994-03-21", "gov": "01", "gov_name": "Cairo"},
    {"id": "ho_clean_02", "name": "خالد سمير مرقص حنا", "address": "٢٤ شارع الإقبال لوران الإسكندرية", "nid": "29108140203344", "dob": "1991-08-14", "gov": "02", "gov_name": "Alexandria"},
    {"id": "ho_clean_03", "name": "نهلة وجدي إبراهيم غانم", "address": "٧ شارع ممفيس حي الشرق بورسعيد", "nid": "29701300305566", "dob": "1997-01-30", "gov": "03", "gov_name": "Port Said"},
    {"id": "ho_clean_04", "name": "مصطفى وفيق جابر عامر", "address": "١٥ شارع الجيش حي السويس السويس", "nid": "28912100407788", "dob": "1989-12-10", "gov": "04", "gov_name": "Suez"},
    {"id": "ho_clean_05", "name": "رانيا ممدوح زكي سالم", "address": "٩ شارع سعد زغلول دمياط", "nid": "29605181109900", "dob": "1996-05-18", "gov": "11", "gov_name": "Damietta"},
    {"id": "ho_clean_06", "name": "ياسر كمال أنور خطاب", "address": "٣ شارع المشاية السفلية المنصورة الدقهلية", "nid": "29309251201122", "dob": "1993-09-25", "gov": "12", "gov_name": "Dakahlia"},
    {"id": "ho_clean_07", "name": "مها عادل توفيق منصور", "address": "١٨ شارع القومية الزقازيق الشرقية", "nid": "29502171302233", "dob": "1995-02-17", "gov": "13", "gov_name": "Ash Sharqia"},
    {"id": "ho_clean_08", "name": "حاتم إكرامي شوكت واصف", "address": "٥ شارع فريد ندى بنها القليوبية", "nid": "29206111403344", "dob": "1992-06-11", "gov": "14", "gov_name": "Al Qalyubia"},
    {"id": "ho_clean_09", "name": "سهام صابر محروس شريف", "address": "٢٢ شارع الخليفة المأمون كفر الشيخ", "nid": "29811041504455", "dob": "1998-11-04", "gov": "15", "gov_name": "Kafr El Sheikh"},
    {"id": "ho_clean_10", "name": "هشام مدحت رشوان سليم", "address": "١١ شارع البحر طنطا الغربية", "nid": "29007291605566", "dob": "1990-07-29", "gov": "16", "gov_name": "Al Gharbia"},
    {"id": "ho_clean_11", "name": "إيناس طلعت وهبة رضوان", "address": "٨ شارع صبري أبو علم شبين الكوم المنوفية", "nid": "29704121706677", "dob": "1997-04-12", "gov": "17", "gov_name": "Al Monufia"},
    {"id": "ho_clean_12", "name": "أيمن شعبان عبد الحليم صقر", "address": "١٤ شارع الجمهورية دمنهور البحيرة", "nid": "29310081807788", "dob": "1993-10-08", "gov": "18", "gov_name": "Al Beheira"},
    {"id": "ho_clean_13", "name": "بسمة طارق شفيق حماد", "address": "١٦ شارع محمد علي الإسماعيلية", "nid": "29603151908899", "dob": "1996-03-15", "gov": "19", "gov_name": "Ismailia"},
    {"id": "ho_clean_14", "name": "بهاء عزمي يونس بطرس", "address": "٦ شارع النيل الدقي الجيزة", "nid": "29101222101234", "dob": "1991-01-22", "gov": "21", "gov_name": "Giza"},
    {"id": "ho_clean_15", "name": "شيماء عبد الحميد متولي بدر", "address": "١٠ شارع بورسعيد بني سويف", "nid": "29508302202345", "dob": "1995-08-30", "gov": "22", "gov_name": "Beni Suef"},
    {"id": "ho_clean_16", "name": "نبيل كرم إسكندر بشاي", "address": "١٩ شارع الحرية الفيوم", "nid": "28804192303456", "dob": "1988-04-19", "gov": "23", "gov_name": "Fayoum"},
    {"id": "ho_clean_17", "name": "منى فايز جرجس مقار", "address": "٤ شارع كورنيش النيل المنيا", "nid": "29412052404567", "dob": "1994-12-05", "gov": "24", "gov_name": "Minya"},
    {"id": "ho_clean_18", "name": "عماد صفوت نخلة تاوضروس", "address": "١٣ شارع الجمهورية أسيوط", "nid": "29209142505678", "dob": "1992-09-14", "gov": "25", "gov_name": "Asyut"},
    {"id": "ho_clean_19", "name": "عبير لطفي فهمي حبيب", "address": "١٧ شارع المحطة سوهاج", "nid": "29902282606789", "dob": "1999-02-28", "gov": "26", "gov_name": "Sohag"},
    {"id": "ho_clean_20", "name": "توفيق شريف حسانين درويش", "address": "٢٠ شارع كوبري دندرة قنا", "nid": "29005162707890", "dob": "1990-05-16", "gov": "27", "gov_name": "Qena"},
    {"id": "ho_clean_21", "name": "أمل حسني بركات رضوان", "address": "٢ شارع أبطال التحرير أسوان", "nid": "29707072808901", "dob": "1997-07-07", "gov": "28", "gov_name": "Aswan"},
    {"id": "ho_clean_22", "name": "رمزي يوسف لمعي خزام", "address": "٢١ شارع خالد بن الوليد الأقصر", "nid": "29303032909012", "dob": "1993-03-03", "gov": "29", "gov_name": "Luxor"},
    {"id": "ho_clean_23", "name": "وفاء مجدي شوقي عياد", "address": "٣٠ شارع الشيراتون الغردقة البحر الأحمر", "nid": "29606203101123", "dob": "1996-06-20", "gov": "31", "gov_name": "Red Sea"},
    {"id": "ho_clean_24", "name": "أشرف رشاد أنيس عوض", "address": "١ شارع جمال عبد الناصر الخارجة الوادي الجديد", "nid": "29110103202234", "dob": "1991-10-10", "gov": "32", "gov_name": "New Valley"},
    {"id": "ho_clean_25", "name": "سوزان فخري صادق واصف", "address": "٢٨ شارع الجلاء مرسى مطروح مطروح", "nid": "29501053303345", "dob": "1995-01-05", "gov": "33", "gov_name": "Matrouh"},
    {"id": "ho_clean_26", "name": "وليد صبحي إمام غبريال", "address": "١١ شارع الفاتح العريش شمال سيناء", "nid": "29808263404456", "dob": "1998-08-26", "gov": "34", "gov_name": "North Sinai"},
    {"id": "ho_clean_27", "name": "دينا وجيه كيرلس قزمان", "address": "٧ شارع السلام طور سيناء جنوب سيناء", "nid": "28911153505567", "dob": "1989-11-15", "gov": "35", "gov_name": "South Sinai"},
    {"id": "ho_clean_28", "name": "كريم بهاء الدين شكري عامر", "address": "٣٥ شارع عباس العقاد مدينة نصر القاهرة", "nid": "30105190106678", "dob": "2001-05-19", "gov": "01", "gov_name": "Cairo"},
    {"id": "ho_clean_29", "name": "نورهان فتحي جاد الرب سالم", "address": "١٦ شارع سيدي جابر الإسكندرية", "nid": "30209080207789", "dob": "2002-09-08", "gov": "02", "gov_name": "Alexandria"},
    {"id": "ho_clean_30", "name": "أحمد نشأت متولي قاسم", "address": "٢٧ شارع مراد الجيزة", "nid": "30012122108890", "dob": "2000-12-12", "gov": "21", "gov_name": "Giza"},
]

NEW_MISMATCH_SPECS = [
    # 1-6: Governorate Mismatch
    {"id": "ho_mismatch_01", "name": "يوسف أحمد علي ناصر", "address": "١٥ شارع رشدي الإسكندرية", "nid": "29403210101567", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1994-03-21"},
    {"id": "ho_mismatch_02", "name": "طارق محمود حسن سالم", "address": "١٤ شارع المحطة الفيوم", "nid": "29101222101234", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1991-01-22"},
    {"id": "ho_mismatch_03", "name": "سامح فؤاد إبراهيم بدر", "address": "١٨ شارع البحر طنطا الغربية", "nid": "29309251201122", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1993-09-25"},
    {"id": "ho_mismatch_04", "name": "ماجد سمير رشاد إمام", "address": "٤ شارع كورنيش النيل أسوان", "nid": "29902282606789", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1999-02-28"},
    {"id": "ho_mismatch_05", "name": "حسام عزمي لطفي عوض", "address": "١٠ شارع محمد علي الإسماعيلية", "nid": "29701300305566", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1997-01-30"},
    {"id": "ho_mismatch_06", "name": "إيهاب طلعت غالي واصف", "address": "٩ شارع طلعت حرب قصر النيل القاهرة", "nid": "28912100407788", "expected_reasons": ["GOVERNORATE_MISMATCH"], "comparison_dob": "1989-12-10"},

    # 7-12: Birth Date Mismatch
    {"id": "ho_mismatch_07", "name": "مروان عصام كمال خطاب", "address": "١٢ شارع الجمهورية عابدين القاهرة", "nid": "29403210101567", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1990-01-01"},
    {"id": "ho_mismatch_08", "name": "فاطمة نبيل جرجس نخلة", "address": "٢٤ شارع الإقبال لوران الإسكندرية", "nid": "29108140203344", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1995-12-12"},
    {"id": "ho_mismatch_09", "name": "عمرو شريف سامي الشريف", "address": "٧ شارع ممفيس حي الشرق بورسعيد", "nid": "29701300305566", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1997-01-31"},
    {"id": "ho_mismatch_10", "name": "منى إسماعيل فؤاد بدر", "address": "١٥ شارع الجيش حي السويس السويس", "nid": "28912100407788", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1989-11-10"},
    {"id": "ho_mismatch_11", "name": "وليد صابر مجدي وهبة", "address": "٩ شارع سعد زغلول دمياط", "nid": "29605181109900", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1999-05-18"},
    {"id": "ho_mismatch_12", "name": "رشا ممدوح توفيق كامل", "address": "٣ شارع المشاية السفلية المنصورة الدقهلية", "nid": "29309251201122", "expected_reasons": ["BIRTH_DATE_MISMATCH"], "comparison_dob": "1993-09-26"},

    # 13-18: Invalid ID Structure
    {"id": "ho_mismatch_13", "name": "زياد وفيق حسانين عبد ربه", "address": "١٢ شارع الجمهورية عابدين القاهرة", "nid": "19403210101567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},
    {"id": "ho_mismatch_14", "name": "هبة يوسف سامي الجوهري", "address": "٢٤ شارع الإقبال لوران الإسكندرية", "nid": "29413210101567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},
    {"id": "ho_mismatch_15", "name": "أشرف حمدي محروس سليم", "address": "٧ شارع ممفيس حي الشرق بورسعيد", "nid": "29400210101567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},
    {"id": "ho_mismatch_16", "name": "داليا كمال الدين سراج", "address": "١٥ شارع الجيش حي السويس السويس", "nid": "29403320101567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},
    {"id": "ho_mismatch_17", "name": "تامر عبد العزيز شكري عامر", "address": "٩ شارع سعد زغلول دمياط", "nid": "29502290101567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},
    {"id": "ho_mismatch_18", "name": "شريف لطفي عزمي صادق", "address": "٣ شارع المشاية السفلية المنصورة الدقهلية", "nid": "29403219901567", "expected_reasons": ["INVALID_ID_STRUCTURE"], "comparison_dob": None},

    # 19-24: Missing Fields
    {"id": "ho_mismatch_19", "name": "", "address": "١٢ شارع الجمهورية عابدين القاهرة", "nid": "29403210101567", "obscure_name": True, "expected_reasons": ["MISSING_FIELD_NAME"], "comparison_dob": "1994-03-21"},
    {"id": "ho_mismatch_20", "name": "", "address": "٢٤ شارع الإقبال لوران الإسكندرية", "nid": "29108140203344", "obscure_name": True, "expected_reasons": ["MISSING_FIELD_NAME"], "comparison_dob": "1991-08-14"},
    {"id": "ho_mismatch_21", "name": "نهلة وجدي إبراهيم غانم", "address": "", "nid": "29701300305566", "obscure_address": True, "expected_reasons": ["MISSING_FIELD_ADDRESS"], "comparison_dob": "1997-01-30"},
    {"id": "ho_mismatch_22", "name": "مصطفى وفيق جابر عامر", "address": "", "nid": "28912100407788", "obscure_address": True, "expected_reasons": ["MISSING_FIELD_ADDRESS"], "comparison_dob": "1989-12-10"},
    {"id": "ho_mismatch_23", "name": "رانيا ممدوح زكي سالم", "address": "٩ شارع سعد زغلول دمياط", "nid": "", "obscure_id": True, "expected_reasons": ["MISSING_FIELD_NATIONAL_ID"], "comparison_dob": "1996-05-18"},
    {"id": "ho_mismatch_24", "name": "ياسر كمال أنور خطاب", "address": "٣ شارع المشاية السفلية المنصورة الدقهلية", "nid": "", "obscure_id": True, "expected_reasons": ["MISSING_FIELD_NATIONAL_ID"], "comparison_dob": "1993-09-25"},

    # 25-30: Low OCR Confidence / Optical Degradation
    {"id": "ho_mismatch_25", "name": "مها عادل توفيق منصور", "address": "١٨ شارع القومية الزقازيق الشرقية", "nid": "29502171302233", "blur_radius": 3.8, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1995-02-17"},
    {"id": "ho_mismatch_26", "name": "حاتم إكرامي شوكت واصف", "address": "٥ شارع فريد ندى بنها القليوبية", "nid": "29206111403344", "blur_radius": 4.2, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1992-06-11"},
    {"id": "ho_mismatch_27", "name": "سهام صابر محروس شريف", "address": "٢٢ شارع الخليفة المأمون كفر الشيخ", "nid": "29811041504455", "brightness": 0.35, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1998-11-04"},
    {"id": "ho_mismatch_28", "name": "هشام مدحت رشوان سليم", "address": "١١ شارع البحر طنطا الغربية", "nid": "29007291605566", "brightness": 0.30, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1990-07-29"},
    {"id": "ho_mismatch_29", "name": "إيناس طلعت وهبة رضوان", "address": "٨ شارع صبري أبو علم شبين الكوم المنوفية", "nid": "29704121706677", "blur_radius": 3.0, "brightness": 0.45, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1997-04-12"},
    {"id": "ho_mismatch_30", "name": "أيمن شعبان عبد الحليم صقر", "address": "١٤ شارع الجمهورية دمنهور البحيرة", "nid": "29310081807788", "blur_radius": 4.0, "expected_reasons": ["LOW_OCR_CONFIDENCE"], "comparison_dob": "1993-10-08"},
]

def main():
    manifest = []
    print(f"Generating {len(NEW_CLEAN_SPECS) + len(NEW_MISMATCH_SPECS)} synthetic held-out cards in {OUTPUT_DIR}...")

    # Generate 30 clean cards
    for spec in NEW_CLEAN_SPECS:
        cid = spec["id"]
        img = draw_synthetic_card(
            name=spec["name"],
            address=spec["address"],
            national_id=spec["nid"],
        )
        fpath = os.path.join(OUTPUT_DIR, f"{cid}.png")
        img.save(fpath, format="PNG")

        manifest.append({
            "card_id": cid,
            "filename": f"{cid}.png",
            "condition": "CLEAN",
            "is_anomaly": False,
            "expected_reasons": [],
            "ground_truth": {
                "name": spec["name"],
                "address": spec["address"],
                "national_id": spec["nid"],
                "derived_dob": spec["dob"],
                "governorate_code": spec["gov"],
                "governorate_name": spec["gov_name"],
            },
            "comparison_data": {
                "birth_date": spec["dob"],
            },
        })

    # Generate 30 planted exception cards
    for spec in NEW_MISMATCH_SPECS:
        cid = spec["id"]
        img = draw_synthetic_card(
            name=spec.get("name", ""),
            address=spec.get("address", ""),
            national_id=spec.get("nid", ""),
            blur_radius=spec.get("blur_radius", 0.0),
            brightness=spec.get("brightness", 1.0),
            obscure_id=spec.get("obscure_id", False),
            obscure_address=spec.get("obscure_address", False),
            obscure_name=spec.get("obscure_name", False),
        )
        fpath = os.path.join(OUTPUT_DIR, f"{cid}.png")
        img.save(fpath, format="PNG")

        manifest.append({
            "card_id": cid,
            "filename": f"{cid}.png",
            "condition": "PLANTED_EXCEPTION",
            "is_anomaly": True,
            "expected_reasons": spec["expected_reasons"],
            "ground_truth": {
                "name": spec.get("name", ""),
                "address": spec.get("address", ""),
                "national_id": spec.get("nid", ""),
            },
            "comparison_data": {
                "birth_date": spec.get("comparison_dob"),
            },
        })

    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Completed! {len(manifest)} cards + manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
