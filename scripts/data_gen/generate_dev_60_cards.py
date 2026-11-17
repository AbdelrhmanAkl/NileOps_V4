"""Generate 60 Synthetic Egyptian National ID Cards for Handbook KYC Exception Evaluation.

30 Clean Cards (Zero anomalies, matching governorate and DOB).
30 Exception Cards (Planted mismatches, missing fields, invalid structures, low quality).

All output is saved to data/synthetic_cards/eval_b1/ (git-ignored).
Manifest saved to data/synthetic_cards/eval_b1/manifest.json.
"""

import json
import os
import re
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_cards", "eval_b1"))
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
    draw.text((45, 50), "SYNTHETIC FIXTURE", fill=(160, 110, 30), font=stamp_font, anchor="la")

    # Photo Box
    photo_box = [(45, 120), (195, 310)]
    draw.rectangle(photo_box, fill=(215, 225, 220), outline=(170, 185, 180), width=2)
    draw.text((120, 215), "PHOTO\nFIXTURE", fill=(140, 155, 150), font=label_font, anchor="mm", align="center")

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
    draw.text((width // 2, height - 35), "FOR LOCAL SIMULATION ONLY — NEVER AN AUTHENTIC DOCUMENT", fill=(180, 100, 100), font=stamp_font, anchor="mm")

    # Postprocessing (blur, brightness)
    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)

    return img


# Clean Card Definitions (30 cards: 15 original + 15 enlarged)
CLEAN_SPECS = [
    {"id": "card_clean_01", "name": "أحمد منصور إبراهيم عبد الله", "address": "١٥ شارع طلعت حرب قصر النيل القاهرة", "nid": "29505140101234", "dob": "1995-05-14", "gov": "01", "gov_name": "Cairo"},
    {"id": "card_clean_02", "name": "محمود فريد حسن علي", "address": "١٤ شارع سيدي جابر الإسكندرية", "nid": "29011200205678", "dob": "1990-11-20", "gov": "02", "gov_name": "Alexandria"},
    {"id": "card_clean_03", "name": "سارة فهمي محمود خليل", "address": "٢٢ شارع النيل الدقي الجيزة", "nid": "29803152109876", "dob": "1998-03-15", "gov": "21", "gov_name": "Giza"},
    {"id": "card_clean_04", "name": "كريم يوسف عبد الرحمن", "address": "٨ شارع الجيش المنصورة الدقهلية", "nid": "29207041201122", "dob": "1992-07-04", "gov": "12", "gov_name": "Dakahlia"},
    {"id": "card_clean_05", "name": "نورهان كمال عثمان ناصر", "address": "١٠ شارع المحطة الزقازيق الشرقية", "nid": "29610121303344", "dob": "1996-10-12", "gov": "13", "gov_name": "Ash Sharqia"},
    {"id": "card_clean_06", "name": "عمر شريف سامي الشريف", "address": "٥ شارع البحر طنطا الغربية", "nid": "29104081605566", "dob": "1991-04-08", "gov": "16", "gov_name": "Al Gharbia"},
    {"id": "card_clean_07", "name": "منى إسماعيل فؤاد بدر", "address": "١٢ شارع الجلاء شبين الكوم المنوفية", "nid": "29409191707788", "dob": "1994-09-19", "gov": "17", "gov_name": "Al Monufia"},
    {"id": "card_clean_08", "name": "طارق رشدي حسني حماد", "address": "٧ شارع الجمهورية دمنهور البحيرة", "nid": "28906231809900", "dob": "1989-06-23", "gov": "18", "gov_name": "Al Beheira"},
    {"id": "card_clean_09", "name": "ياسمين عادل مصطفى نور", "address": "٣ شارع فريد ندى بنها القليوبية", "nid": "30101151402233", "dob": "2001-01-15", "gov": "14", "gov_name": "Al Qalyubia"},
    {"id": "card_clean_10", "name": "خالد أمين شفيق سالم", "address": "١٨ شارع المحطة سوهاج", "nid": "29308302604455", "dob": "1993-08-30", "gov": "26", "gov_name": "Sohag"},
    {"id": "card_clean_11", "name": "هاني طلعت رضوان جاد", "address": "٤ شارع كورنيش النيل أسوان", "nid": "28802142806677", "dob": "1988-02-14", "gov": "28", "gov_name": "Aswan"},
    {"id": "card_clean_12", "name": "دينا مدحت شاكر غانم", "address": "٩ شارع محمد علي بورسعيد", "nid": "29712050308899", "dob": "1997-12-05", "gov": "03", "gov_name": "Port Said"},
    {"id": "card_clean_13", "name": "وليد صابر مجدي وهبة", "address": "١١ شارع الجيش الأربعين السويس", "nid": "29005180401235", "dob": "1990-05-18", "gov": "04", "gov_name": "Suez"},
    {"id": "card_clean_14", "name": "رشا ممدوح توفيق كامل", "address": "١٦ شارع الحرية المنيا", "nid": "29511112403456", "dob": "1995-11-11", "gov": "24", "gov_name": "Minya"},
    {"id": "card_clean_15", "name": "حسام أنور متولي صقر", "address": "٢٠ شارع الجمهورية أسيوط", "nid": "28903252505678", "dob": "1989-03-25", "gov": "25", "gov_name": "Asyut"},
    # 15 Additional Clean Cards (Fresh Seed)
    {"id": "card_clean_16", "name": "مروان عماد فهمي يونس", "address": "١٨ شارع شبين الكوم الإسماعيلية", "nid": "29408121901234", "dob": "1994-08-12", "gov": "19", "gov_name": "Ismailia"},
    {"id": "card_clean_17", "name": "فاطمة نبيل جرجس نخلة", "address": "٦ شارع بورسعيد بني سويف", "nid": "29105252204567", "dob": "1991-05-25", "gov": "22", "gov_name": "Beni Suef"},
    {"id": "card_clean_18", "name": "أمير صفوت كرم بطرس", "address": "١٤ شارع الجمهورية الفيوم", "nid": "29309172307890", "dob": "1993-09-17", "gov": "23", "gov_name": "Fayoum"},
    {"id": "card_clean_19", "name": "شريف لطفي عزمي صادق", "address": "٢٥ شارع كوبري دندرة قنا", "nid": "29604032701122", "dob": "1996-04-03", "gov": "27", "gov_name": "Qena"},
    {"id": "card_clean_20", "name": "نادية إبراهيم شحاتة عوض", "address": "٩ شارع خالد بن الوليد الأقصر", "nid": "29710182903344", "dob": "1997-10-18", "gov": "29", "gov_name": "Luxor"},
    {"id": "card_clean_21", "name": "حازم ماجد بركات رضوان", "address": "١٢ شارع الشيراتون الغردقة البحر الأحمر", "nid": "29212083105566", "dob": "1992-12-08", "gov": "31", "gov_name": "Red Sea"},
    {"id": "card_clean_22", "name": "سلوى فؤاد زكي إسكندر", "address": "٥ شارع جمال عبد الناصر الخارجة الوادي الجديد", "nid": "29506143207788", "dob": "1995-06-14", "gov": "32", "gov_name": "New Valley"},
    {"id": "card_clean_23", "name": "بيشوي مرقص أنيس حنا", "address": "٢٠ شارع إسكندرية مرسى مطروح مطروح", "nid": "29007223309900", "dob": "1990-07-22", "gov": "33", "gov_name": "Matrouh"},
    {"id": "card_clean_24", "name": "نجلاء عاطف شوقي فرج", "address": "١٥ شارع الفاتح العريش شمال سيناء", "nid": "29802193402233", "dob": "1998-02-19", "gov": "34", "gov_name": "North Sinai"},
    {"id": "card_clean_25", "name": "إيهاب طلعت غالي واصف", "address": "٨ شارع السلام شرم الشيخ جنوب سيناء", "nid": "28911053504455", "dob": "1989-11-05", "gov": "35", "gov_name": "South Sinai"},
    {"id": "card_clean_26", "name": "زياد وفيق حسانين عبد ربه", "address": "٣٠ شارع عباس العقاد مدينة نصر القاهرة", "nid": "29901010106677", "dob": "1999-01-01", "gov": "01", "gov_name": "Cairo"},
    {"id": "card_clean_27", "name": "هبة يوسف سامي الجوهري", "address": "١١ شارع الإقبال لوران الإسكندرية", "nid": "30004150208899", "dob": "2000-04-15", "gov": "02", "gov_name": "Alexandria"},
    {"id": "card_clean_28", "name": "أشرف حمدي محروس سليم", "address": "٧ شارع مراد ميدان الجيزة الجيزة", "nid": "29307202101235", "dob": "1993-07-20", "gov": "21", "gov_name": "Giza"},
    {"id": "card_clean_29", "name": "داليا كمال الدين سراج", "address": "١٦ شارع المشاية السفلية المنصورة الدقهلية", "nid": "29509111203456", "dob": "1995-09-11", "gov": "12", "gov_name": "Dakahlia"},
    {"id": "card_clean_30", "name": "تامر عبد العزيز شكري عامر", "address": "٢٢ شارع سعيد طنطا الغربية", "nid": "29103281605678", "dob": "1991-03-28", "gov": "16", "gov_name": "Al Gharbia"},
]

# Planted Exception Card Definitions (30 cards: 15 original + 15 enlarged)
MISMATCH_SPECS = [
    # (b) Governorate Mismatch
    {
        "id": "card_mismatch_01",
        "name": "يوسف محمود علي إبراهيم",
        "address": "١٤ شارع جمال عبد الناصر سيدي جابر الإسكندرية",
        "nid": "29505140101234",  # Gov 01 (Cairo) vs Alexandria address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1995-05-14",
    },
    {
        "id": "card_mismatch_02",
        "name": "إبراهيم حسان خليل عيسى",
        "address": "٢٥ شارع البحر طنطا الغربية",
        "nid": "29304152109876",  # Gov 21 (Giza) vs Gharbia address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1993-04-15",
    },
    {
        "id": "card_mismatch_03",
        "name": "مروان عصام سمير عطية",
        "address": "٨ شارع فيصل ميدان الجيزة الجيزة",
        "nid": "29107200205678",  # Gov 02 (Alexandria) vs Giza address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1991-07-20",
    },
    # (a) Date of Birth Mismatch
    {
        "id": "card_mismatch_04",
        "name": "سامح وفيق لطفي عوض",
        "address": "١٦ شارع الجيش المنصورة الدقهلية",
        "nid": "29608101201122",  # DOB from NID: 1996-08-10
        "expected_reasons": ["BIRTH_DATE_MISMATCH"],
        "comparison_dob": "1990-01-01",  # Provided DOB: 1990-01-01
    },
    {
        "id": "card_mismatch_05",
        "name": "نهى صبحي رشاد إمام",
        "address": "٥ شارع الجمهورية دمنهور البحيرة",
        "nid": "29202151803344",  # DOB from NID: 1992-02-15
        "expected_reasons": ["BIRTH_DATE_MISMATCH"],
        "comparison_dob": "1995-10-25",
    },
    {
        "id": "card_mismatch_06",
        "name": "عصام رجب متولي جابر",
        "address": "١٢ شارع المحطة سوهاج",
        "nid": "28811302605566",  # DOB from NID: 1988-11-30
        "expected_reasons": ["BIRTH_DATE_MISMATCH"],
        "comparison_dob": "1988-12-01",  # Off by one day
    },
    # (e) Invalid National ID Structure
    {
        "id": "card_mismatch_07",
        "name": "جمال بهاء شكري يونس",
        "address": "٩ شارع طلعت حرب قصر النيل القاهرة",
        "nid": "19505140101234",  # Invalid Century '1'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_08",
        "name": "منى عاطف فتحي غانم",
        "address": "٢٢ شارع الجلاء شبين الكوم المنوفية",
        "nid": "29513141707788",  # Invalid Month '13'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_09",
        "name": "باهر وجدي نشأت فرج",
        "address": "١١ شارع النيل الدقي الجيزة",
        "nid": "29502292109988",  # 1995 is NOT a leap year -> Feb 29 invalid
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    # (c) Missing Fields
    {
        "id": "card_mismatch_10",
        "name": "",  # Missing Name
        "address": "١٥ شارع طلعت حرب قصر النيل القاهرة",
        "nid": "29403150101234",
        "obscure_name": True,
        "expected_reasons": ["MISSING_FIELD_NAME"],
        "comparison_dob": "1994-03-15",
    },
    {
        "id": "card_mismatch_11",
        "name": "فادي رمزي يوحنا مسعود",
        "address": "",  # Missing Address
        "nid": "29611200105678",
        "obscure_address": True,
        "expected_reasons": ["MISSING_FIELD_ADDRESS"],
        "comparison_dob": "1996-11-20",
    },
    {
        "id": "card_mismatch_12",
        "name": "سامي كمال زكي إسكندر",
        "address": "٨ شارع سيدي جابر الإسكندرية",
        "nid": "",  # Missing National ID
        "obscure_id": True,
        "expected_reasons": ["MISSING_FIELD_NATIONAL_ID"],
        "comparison_dob": "1990-01-01",
    },
    # (d) Low OCR Confidence
    {
        "id": "card_mismatch_13",
        "name": "حاتم إكرامي شوكت واصف",
        "address": "١٤ شارع قصر العيني القاهرة",
        "nid": "29302180109988",
        "blur_radius": 3.8,  # Heavy Gaussian blur triggers low confidence
        "expected_reasons": ["LOW_OCR_CONFIDENCE"],
        "comparison_dob": "1993-02-18",
    },
    {
        "id": "card_mismatch_14",
        "name": "عاطف توفيق سراج الدين",
        "address": "٢٠ شارع الجمهورية أسيوط",
        "nid": "28909102501122",
        "brightness": 0.28,  # Heavy underexposure triggers low confidence
        "expected_reasons": ["LOW_OCR_CONFIDENCE"],
        "comparison_dob": "1989-09-10",
    },
    # Compound Multi-Anomaly Card
    {
        "id": "card_mismatch_15",
        "name": "",  # Missing name
        "address": "٤ شارع كورنيش النيل أسوان",
        "nid": "29514150101234",  # Invalid Month 14 + Gov Mismatch (01 vs Aswan) + Missing Name
        "obscure_name": True,
        "expected_reasons": ["INVALID_ID_STRUCTURE", "GOVERNORATE_MISMATCH", "MISSING_FIELD_NAME"],
        "comparison_dob": None,
    },
    # 15 Additional Exception Cards (Enlarging dataset to 60 cards total)
    {
        "id": "card_mismatch_16",
        "name": "عماد نبيل رمزي واصف",
        "address": "١٨ شارع شبين الكوم الإسماعيلية",
        "nid": "29505140101234",  # Gov 01 (Cairo) vs Ismailia (19) address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1995-05-14",
    },
    {
        "id": "card_mismatch_17",
        "name": "سلوى رؤوف صادق عطالله",
        "address": "٤ شارع كورنيش النيل أسوان",
        "nid": "29011200205678",  # Gov 02 (Alexandria) vs Aswan (28) address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1990-11-20",
    },
    {
        "id": "card_mismatch_18",
        "name": "هيثم أنسي بطرس جرجس",
        "address": "٦ شارع بورسعيد بني سويف",
        "nid": "29307152204567",  # DOB from NID: 1993-07-15
        "expected_reasons": ["BIRTH_DATE_MISMATCH"],
        "comparison_dob": "1998-11-20",  # Provided DOB: 1998-11-20
    },
    {
        "id": "card_mismatch_19",
        "name": "ميرفت صابر لمعي غبريال",
        "address": "١٤ شارع الجمهورية الفيوم",
        "nid": "28504222307890",  # DOB from NID: 1985-04-22
        "expected_reasons": ["BIRTH_DATE_MISMATCH"],
        "comparison_dob": "1991-03-15",
    },
    {
        "id": "card_mismatch_20",
        "name": "أشرف عادل مجدي فرج",
        "address": "٢٥ شارع كوبري دندرة قنا",
        "nid": "49604032701122",  # Invalid Century '4'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_21",
        "name": "دينا وجيه حنا منصور",
        "address": "٩ شارع خالد بن الوليد الأقصر",
        "nid": "29715182903344",  # Invalid Month '15'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_22",
        "name": "رأفت وجدي فوزي عبد المسيح",
        "address": "١٢ شارع الشيراتون الغردقة البحر الأحمر",
        "nid": "29212323105566",  # Invalid Day '32'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_23",
        "name": "مريم أنيس رزق متى",
        "address": "٥ شارع جمال عبد الناصر الخارجة الوادي الجديد",
        "nid": "29506149907788",  # Invalid Governorate '99'
        "expected_reasons": ["INVALID_ID_STRUCTURE"],
        "comparison_dob": None,
    },
    {
        "id": "card_mismatch_24",
        "name": "",  # Missing Name
        "address": "٢٠ شارع إسكندرية مرسى مطروح مطروح",
        "nid": "29007223309900",
        "obscure_name": True,
        "expected_reasons": ["MISSING_FIELD_NAME"],
        "comparison_dob": "1990-07-22",
    },
    {
        "id": "card_mismatch_25",
        "name": "فيكتور بشارة يوسف صليب",
        "address": "",  # Missing Address
        "nid": "29802193402233",
        "obscure_address": True,
        "expected_reasons": ["MISSING_FIELD_ADDRESS"],
        "comparison_dob": "1998-02-19",
    },
    {
        "id": "card_mismatch_26",
        "name": "ميشيل سمير ناشد رزق",
        "address": "٨ شارع السلام شرم الشيخ جنوب سيناء",
        "nid": "",  # Missing National ID
        "obscure_id": True,
        "expected_reasons": ["MISSING_FIELD_NATIONAL_ID"],
        "comparison_dob": "1989-11-05",
    },
    {
        "id": "card_mismatch_27",
        "name": "أيمن رفعت نظيم داود",
        "address": "٣٠ شارع عباس العقاد مدينة نصر القاهرة",
        "nid": "29901010106677",
        "blur_radius": 4.0,  # Heavy Gaussian blur triggers low confidence
        "expected_reasons": ["LOW_OCR_CONFIDENCE"],
        "comparison_dob": "1999-01-01",
    },
    {
        "id": "card_mismatch_28",
        "name": "كريستين عماد عزمي إسكندر",
        "address": "١١ شارع الإقبال لوران الإسكندرية",
        "nid": "30004150208899",
        "brightness": 0.25,  # Heavy underexposure triggers low confidence
        "expected_reasons": ["LOW_OCR_CONFIDENCE"],
        "comparison_dob": "2000-04-15",
    },
    {
        "id": "card_mismatch_29",
        "name": "تامر رفيق مسعود غالي",
        "address": "١٤ شارع طلعت حرب قصر النيل القاهرة",
        "nid": "29505140201234",  # Gov 02 (Alexandria) vs Cairo address
        "expected_reasons": ["GOVERNORATE_MISMATCH"],
        "comparison_dob": "1995-05-14",
    },
    {
        "id": "card_mismatch_30",
        "name": "",  # Compound: Missing name + Invalid Month 16
        "address": "٧ شارع مراد ميدان الجيزة الجيزة",
        "nid": "29316202101235",
        "obscure_name": True,
        "expected_reasons": ["INVALID_ID_STRUCTURE", "MISSING_FIELD_NAME"],
        "comparison_dob": None,
    },
]

def main():
    manifest = []
    print(f"Generating {len(CLEAN_SPECS) + len(MISMATCH_SPECS)} synthetic cards in {OUTPUT_DIR}...")

    # Generate 30 clean cards
    for spec in CLEAN_SPECS:
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
        print(f"  [CLEAN] {cid}.png generated.")

    # Generate 30 planted exception cards
    for spec in MISMATCH_SPECS:
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
        print(f"  [EXCEPTION] {cid}.png generated (Expected: {spec['expected_reasons']}).")

    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\nCompleted! {len(manifest)} cards + manifest saved to {manifest_path}")

if __name__ == "__main__":
    main()
