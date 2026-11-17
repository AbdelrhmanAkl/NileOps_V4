import os
import sys
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2
import arabic_reshaper
from bidi.algorithm import get_display

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "synthetic_cards"))
os.makedirs(OUTPUT_DIR, exist_ok=True)


def resolve_font(name: str = 'tahoma.ttf', size: int = 24):
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
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()

FONT_PATH = resolve_font('tahoma.ttf', 24)
NID_FONT_PATH = resolve_font('arial.ttf', 26)


# 40 Synthetic Identities with Egyptian Geographic and Demographic Realism
IDENTITIES_40 = [
    # 01..10: Clean (10)
    {"id": "card_01_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "28804150101234", "name": "طارق محمود حسن علي", "addr": "١٢ شارع قصر العيني - السيدة زينب - القاهرة", "fc": "TK8472910", "gov": "القاهرة", "bdate": "1988-04-15", "sex": "MALE"},
    {"id": "card_02_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29210200201856", "name": "مصطفى كمال إبراهيم الشناوي", "addr": "٤٥ طريق الجيش - محطة الرمل - الإسكندرية", "fc": "MK3910248", "gov": "الإسكندرية", "bdate": "1992-10-20", "sex": "MALE"},
    {"id": "card_03_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29505140101234", "name": "أحمد منصور إبراهيم عبد الله", "addr": "١٥ شارع طلعت حرب - قصر النيل - القاهرة", "fc": "ED2676749", "gov": "القاهرة", "bdate": "1995-05-14", "sex": "MALE"},
    {"id": "card_04_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29003102102456", "name": "فاطمة الزهراء علي حسن", "addr": "٨ شارع التحرير - الدقي - الجيزة", "fc": "FZ5820194", "gov": "الجيزة", "bdate": "1990-03-10", "sex": "FEMALE"},
    {"id": "card_05_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "30107250103789", "name": "عمر خالد يوسف النجار", "addr": "٢٢ شارع عباس العقاد - مدينة نصر - القاهرة", "fc": "OK9103847", "gov": "القاهرة", "bdate": "2001-07-25", "sex": "MALE"},
    {"id": "card_06_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "28512051201923", "name": "سعيد عبد الرحمن محمد خليل", "addr": "١٠ شارع الجمهورية - المنصورة - الدقهلية", "fc": "SR4729105", "gov": "الدقهلية", "bdate": "1985-12-05", "sex": "MALE"},
    {"id": "card_07_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29402181401345", "name": "إسلام مدحت صابر غنيم", "addr": "٥ شارع سعد زغلول - بنها - القليوبية", "fc": "IM8201948", "gov": "القليوبية", "bdate": "1994-02-18", "sex": "MALE"},
    {"id": "card_08_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29709121601789", "name": "حسام عادل لطفي البنا", "addr": "١٨ شارع الجيش - طنطا - الغربية", "fc": "HA4920183", "gov": "الغربية", "bdate": "1997-09-12", "sex": "MALE"},
    {"id": "card_09_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "28911221301456", "name": "وليد شريف فهمي رضوان", "addr": "٣٠ شارع الجلاء - الزقازيق - الشرقية", "fc": "WS9384720", "gov": "الشرقية", "bdate": "1989-11-22", "sex": "MALE"},
    {"id": "card_10_clean", "cond": "clean", "dtl": {"type": "pristine"}, "nid": "29306141801678", "name": "عمرو جلال توفيق البدري", "addr": "٧ شارع عبد السلام عارف - دمنهور - البحيرة", "fc": "AJ5839201", "gov": "البحيرة", "bdate": "1993-06-14", "sex": "MALE"},

    # 11..16: Blur (6)
    {"id": "card_11_blur_r10", "cond": "blur", "dtl": {"radius": 1.0}, "nid": "29308180104567", "name": "حازم شريف إسماعيل بركات", "addr": "١٤ شارع النصر - المعادي - القاهرة", "fc": "HS1928374", "gov": "القاهرة", "bdate": "1993-08-18", "sex": "MALE"},
    {"id": "card_12_blur_r18", "cond": "blur", "dtl": {"radius": 1.8}, "nid": "29702220202345", "name": "كريم مدحت سامي الجوهري", "addr": "٧ شارع بورسعيد - سيدي جابر - الإسكندرية", "fc": "KM8273645", "gov": "الإسكندرية", "bdate": "1997-02-22", "sex": "MALE"},
    {"id": "card_13_blur_r25", "cond": "blur", "dtl": {"radius": 2.5}, "nid": "29111112101456", "name": "وليد عادل شكري فودة", "addr": "٣٠ شارع فيصل - العشرين - الجيزة", "fc": "WA9384720", "gov": "الجيزة", "bdate": "1991-11-11", "sex": "MALE"},
    {"id": "card_14_blur_r32", "cond": "blur", "dtl": {"radius": 3.2}, "nid": "28906300103210", "name": "ياسر جلال توفيق البدري", "addr": "٥ شارع الأهرام - مصر الجديدة - القاهرة", "fc": "YJ5839201", "gov": "القاهرة", "bdate": "1989-06-30", "sex": "MALE"},
    {"id": "card_15_blur_r40", "cond": "blur", "dtl": {"radius": 4.0}, "nid": "28604052601234", "name": "محمود صفوت خيري النحاس", "addr": "١٢ شارع أسيوط سوهاج - مركز طهطا - سوهاج", "fc": "MS4820194", "gov": "سوهاج", "bdate": "1986-04-05", "sex": "MALE"},
    {"id": "card_16_blur_r50", "cond": "blur", "dtl": {"radius": 5.0}, "nid": "29809152701890", "name": "عاطف نبيل كمال الأبنودي", "addr": "٣ شارع المحطة - نجع حمادي - قنا", "fc": "AN5920183", "gov": "قنا", "bdate": "1998-09-15", "sex": "MALE"},

    # 17..24: Rotation / Perspective (8)
    {"id": "card_17_rot_pos3", "cond": "rotation_perspective", "dtl": {"angle": 3.0}, "nid": "29409120101678", "name": "ماجد رفعت صبحي الديب", "addr": "١٨ شارع شبرا - دوران شبرا - القاهرة", "fc": "MR3019482", "gov": "القاهرة", "bdate": "1994-09-12", "sex": "MALE"},
    {"id": "card_18_rot_neg3", "cond": "rotation_perspective", "dtl": {"angle": -3.0}, "nid": "29604080202890", "name": "نادر ممدوح كمال زهران", "addr": "١١ شارع المشير إسماعيل - سيدي بشر - الإسكندرية", "fc": "NM4920183", "gov": "الإسكندرية", "bdate": "1996-04-08", "sex": "MALE"},
    {"id": "card_19_rot_pos6", "cond": "rotation_perspective", "dtl": {"angle": 6.0}, "nid": "28701252101789", "name": "سامح فؤاد إبراهيم علام", "addr": "٢٥ شارع مراد - ميدان الجيزة - الجيزة", "fc": "SF6920184", "gov": "الجيزة", "bdate": "1987-01-25", "sex": "MALE"},
    {"id": "card_20_rot_neg6", "cond": "rotation_perspective", "dtl": {"angle": -6.0}, "nid": "29812150102345", "name": "أشرف بهاء الدين عبد العزيز", "addr": "٩ شارع الثورة - الكوربة - القاهرة", "fc": "AB8201948", "gov": "القاهرة", "bdate": "1998-12-15", "sex": "MALE"},
    {"id": "card_21_rot_pos10", "cond": "rotation_perspective", "dtl": {"angle": 10.0}, "nid": "29011301201678", "name": "شريف رمزي وفيق حمودة", "addr": "٤ شارع السكة الجديدة - المنصورة - الدقهلية", "fc": "SR7102948", "gov": "الدقهلية", "bdate": "1990-11-30", "sex": "MALE"},
    {"id": "card_22_rot_neg10", "cond": "rotation_perspective", "dtl": {"angle": -10.0}, "nid": "29507181402345", "name": "هاني طلعت مراد السعدني", "addr": "١٦ شارع كلية العلوم - شبرا الخيمة - القليوبية", "fc": "HT3920194", "gov": "القليوبية", "bdate": "1995-07-18", "sex": "MALE"},
    {"id": "card_23_rot_pos14", "cond": "rotation_perspective", "dtl": {"angle": 14.0}, "nid": "28908221601234", "name": "أيمن وجيه فتحي غراب", "addr": "٢٨ شارع الفاتح - المحلة الكبرى - الغربية", "fc": "AW8192049", "gov": "الغربية", "bdate": "1989-08-22", "sex": "MALE"},
    {"id": "card_24_perspective_tilt", "cond": "rotation_perspective", "dtl": {"perspective": "keystone_tilt"}, "nid": "29205100103456", "name": "باهر رشاد شكري المناوي", "addr": "٦ شارع شريف - باب اللوق - القاهرة", "fc": "BR1928475", "gov": "القاهرة", "bdate": "1992-05-10", "sex": "MALE"},

    # 25..29: Glare (5)
    {"id": "card_25_glare_topright", "cond": "glare", "dtl": {"region": "top_right"}, "nid": "29103150201234", "name": "مدحت صبحي فخري الدسوقي", "addr": "٢٠ شارع الإقبال - لوران - الإسكندرية", "fc": "MS9102834", "gov": "الإسكندرية", "bdate": "1991-03-15", "sex": "MALE"},
    {"id": "card_26_glare_center", "cond": "glare", "dtl": {"region": "center_hotspot"}, "nid": "29408200102456", "name": "وائل رسمي زكي الجمل", "addr": "٣٥ شارع مصطفى النحاس - مدينة نصر - القاهرة", "fc": "WR4820193", "gov": "القاهرة", "bdate": "1994-08-20", "sex": "MALE"},
    {"id": "card_27_glare_diagonal", "cond": "glare", "dtl": {"region": "diagonal_washout"}, "nid": "28812102101678", "name": "عصام فوزي سليم العيوطي", "addr": "١٤ شارع مراد - ميدان الجيزة - الجيزة", "fc": "EF8201948", "gov": "الجيزة", "bdate": "1988-12-10", "sex": "MALE"},
    {"id": "card_28_glare_bottom_stripe", "cond": "glare", "dtl": {"region": "bottom_stripe"}, "nid": "29606251201890", "name": "خالد صابر عبد الحميد راضي", "addr": "٨ شارع قناة السويس - المنصورة - الدقهلية", "fc": "KS5920183", "gov": "الدقهلية", "bdate": "1996-06-25", "sex": "MALE"},
    {"id": "card_29_glare_photo_corner", "cond": "glare", "dtl": {"region": "photo_corner"}, "nid": "29309050103789", "name": "نبيل توفيق رؤوف شاهين", "addr": "٥٠ شارع الخليفة المأمون - روكسي - القاهرة", "fc": "NT7102948", "gov": "القاهرة", "bdate": "1993-09-05", "sex": "MALE"},

    # 30..35: Low-Light / Noise (6)
    {"id": "card_30_lowlight_b45", "cond": "low_light_noise", "dtl": {"brightness": 0.45}, "nid": "28608140101567", "name": "هشام كمال توفيق غانم", "addr": "١٢ شارع رمسيس - غمرة - القاهرة", "fc": "HK7102948", "gov": "القاهرة", "bdate": "1986-08-14", "sex": "MALE"},
    {"id": "card_31_lowlight_b35", "cond": "low_light_noise", "dtl": {"brightness": 0.35}, "nid": "29903030202678", "name": "عادل صفوت فوزي منصور", "addr": "٦٠ طريق الكورنيش - الشاطبي - الإسكندرية", "fc": "AS3920194", "gov": "الإسكندرية", "bdate": "1999-03-03", "sex": "MALE"},
    {"id": "card_32_gaussian_noise25", "cond": "low_light_noise", "dtl": {"noise_sigma": 25.0}, "nid": "29109090103890", "name": "باسم عزت فاروق حمزة", "addr": "٧٧ شارع مصطفى النحاس - مدينة نصر - القاهرة", "fc": "BE8192049", "gov": "القاهرة", "bdate": "1991-09-09", "sex": "MALE"},
    {"id": "card_33_salt_pepper_noise", "cond": "low_light_noise", "dtl": {"sp_amount": 0.04}, "nid": "28704202101456", "name": "معتز سراج الدين رضوان", "addr": "١٩ شارع الهرم - محطة مشعل - الجيزة", "fc": "MS3847291", "gov": "الجيزة", "bdate": "1987-04-20", "sex": "MALE"},
    {"id": "card_34_low_contrast18", "cond": "low_light_noise", "dtl": {"contrast": 0.40, "brightness": 0.60}, "nid": "29511111201234", "name": "علاء شكري كامل المنشاوي", "addr": "١١ شارع المشاية السفلية - المنصورة - الدقهلية", "fc": "AS4910283", "gov": "الدقهلية", "bdate": "1995-11-11", "sex": "MALE"},
    {"id": "card_35_dim_noisy", "cond": "low_light_noise", "dtl": {"brightness": 0.40, "noise_sigma": 18.0}, "nid": "29207071401890", "name": "صفوت إبراهيم خيري البرنس", "addr": "٢٤ شارع فريد ندا - بنها - القليوبية", "fc": "SI5920184", "gov": "القليوبية", "bdate": "1992-07-07", "sex": "MALE"},

    # 36..40: Partial Occlusion (5)
    {"id": "card_36_occlusion_tape_address", "cond": "partial_occlusion", "dtl": {"type": "sticker_address"}, "nid": "29307200103456", "name": "إيهاب عصام شفيق غنيم", "addr": "٥٠ شارع الخليفة المأمون - روكسي - القاهرة", "fc": "IE4820194", "gov": "القاهرة", "bdate": "1993-07-20", "sex": "MALE"},
    {"id": "card_37_occlusion_thumb_corner", "cond": "partial_occlusion", "dtl": {"type": "thumb_bottom_left"}, "nid": "29511282101890", "name": "عماد فتحي لطفي رضوان", "addr": "١٦ شارع جامعة الدول العربية - المهندسين - الجيزة", "fc": "EF5920183", "gov": "الجيزة", "bdate": "1995-11-28", "sex": "MALE"},
    {"id": "card_38_occlusion_header_bar", "cond": "partial_occlusion", "dtl": {"type": "dark_bar_header"}, "nid": "29005050201234", "name": "رامي وجدي حسني هلال", "addr": "٣٣ شارع الإقبال - لوران - الإسكندرية", "fc": "RW1928475", "gov": "الإسكندرية", "bdate": "1990-05-05", "sex": "MALE"},
    {"id": "card_39_occlusion_clip_top", "cond": "partial_occlusion", "dtl": {"type": "paper_clip_top"}, "nid": "29801201601456", "name": "سامي وحيد توفيق الزيات", "addr": "١٣ شارع البحر - طنطا - الغربية", "fc": "SW8201948", "gov": "الغربية", "bdate": "1998-01-20", "sex": "MALE"},
    {"id": "card_40_occlusion_id_tail_bar", "cond": "partial_occlusion", "dtl": {"type": "barcode_sticker_id"}, "nid": "29410100101678", "name": "أيمن رمزي وفيق حمودة", "addr": "٧ شارع القصر العيني - وسط البلد - القاهرة", "fc": "AR3920194", "gov": "القاهرة", "bdate": "1994-10-10", "sex": "MALE"},
]

def draw_pyramid_background(draw: ImageDraw.Draw, width: int, height: int):
    """Draw coded geometric subtle pyramid wireframe lines on background."""
    # Apex at (width * 0.48, 140)
    apex = (int(width * 0.48), 130)
    b_left = (int(width * 0.18), height - 70)
    b_right = (int(width * 0.82), height - 70)
    b_mid = (int(width * 0.45), height - 60)

    # Pyramid edge lines in subtle pastel green-tinted gray
    wire_color = (218, 230, 222)
    step_color = (226, 236, 230)

    # 1. Main outer triangles
    draw.polygon([apex, b_left, b_mid], outline=wire_color, width=1)
    draw.polygon([apex, b_mid, b_right], outline=wire_color, width=1)

    # 2. Horizontal stepping / masonry lines
    for factor in [0.20, 0.35, 0.50, 0.65, 0.80, 0.92]:
        y_step = int(apex[1] + factor * (b_mid[1] - apex[1]))
        xl = int(apex[0] - factor * (apex[0] - b_left[0]))
        xm = int(apex[0] - factor * (apex[0] - b_mid[0]))
        xr = int(apex[0] + factor * (b_right[0] - apex[0]))
        draw.line([(xl, y_step), (xm, int(y_step + 4))], fill=step_color, width=1)
        draw.line([(xm, int(y_step + 4)), (xr, y_step)], fill=step_color, width=1)

    # 3. Microprint / Guilloche subtle horizontal wavy reference track
    for y_wave in range(110, height - 80, 28):
        pts = [(x, int(y_wave + 3 * math.sin(x / 45.0))) for x in range(30, width - 30, 15)]
        draw.line(pts, fill=(234, 241, 237), width=1)

def draw_neutral_avatar(draw: ImageDraw.Draw, photo_box: list):
    """Draw neutral gray silhouette avatar instead of an authentic face."""
    x0, y0 = photo_box[0]
    x1, y1 = photo_box[1]
    pw = x1 - x0
    ph = y1 - y0

    # Background photo rectangle
    draw.rectangle(photo_box, fill=(224, 230, 226), outline=(175, 188, 182), width=2)

    # Silhouette center
    cx = x0 + pw // 2
    cy = y0 + ph // 2

    # Head (circle)
    head_r = int(pw * 0.22)
    draw.ellipse([(cx - head_r, cy - int(ph * 0.26)), (cx + head_r, cy - int(ph * 0.26) + head_r * 2)], fill=(160, 175, 168))

    # Shoulders (arc / chord)
    sw = int(pw * 0.72)
    sh = int(ph * 0.38)
    draw.chord([(cx - sw // 2, cy + int(ph * 0.05)), (cx + sw // 2, cy + int(ph * 0.05) + sh * 2)], start=180, end=0, fill=(160, 175, 168))

    # Text stamp
    stamp_font = resolve_font('arial.ttf', 11)
    draw.text((cx, y1 - 18), "PHOTO FIXTURE", fill=(110, 130, 120), font=stamp_font, anchor="mm")

def render_base_card(gt: dict) -> Image.Image:
    width, height = 850, 540
    img = Image.new("RGB", (width, height), color=(243, 247, 244))
    draw = ImageDraw.Draw(img)

    # Background Pyramids
    draw_pyramid_background(draw, width, height)

    # Outer border
    draw.rounded_rectangle([(15, 15), (width - 15, height - 15)], radius=18, outline=(180, 200, 190), width=3)
    draw.rounded_rectangle([(25, 25), (width - 25, height - 25)], radius=12, outline=(210, 225, 218), width=1)

    # Header bar
    draw.rectangle([(30, 30), (width - 30, 95)], fill=(225, 238, 230))
    draw.line([(30, 95), (width - 30, 95)], fill=(160, 190, 175), width=2)

    # Fonts
    title_font = resolve_font('tahoma.ttf', 24)
    sub_font = resolve_font('tahoma.ttf', 16)
    label_font = resolve_font('tahoma.ttf', 16)
    nid_font = resolve_font('arial.ttf', 26)
    body_font = resolve_font('tahoma.ttf', 22)
    stamp_font = resolve_font('arial.ttf', 14)

    def prep(txt: str) -> str:
        return get_display(arabic_reshaper.reshape(txt))

    # Header Text
    draw.text((width - 45, 40), prep("جمهورية مصر العربية"), fill=(20, 60, 40), font=title_font, anchor="ra")
    draw.text((width - 45, 68), prep("بطاقة تحقيق الشخصية"), fill=(40, 80, 55), font=sub_font, anchor="ra")
    draw.text((45, 50), "SYNTHETIC FIXTURE", fill=(160, 110, 30), font=stamp_font, anchor="la")

    # Photo Box with Avatar Silhouette
    photo_box = [(45, 120), (195, 310)]
    draw_neutral_avatar(draw, photo_box)

    # 1. Name Band
    draw.text((width - 50, 130), prep("الاسم :"), fill=(80, 100, 90), font=label_font, anchor="ra")
    draw.text((width - 50, 160), prep(gt["name"]), fill=(15, 25, 20), font=body_font, anchor="ra")

    # 2. Address Band
    draw.text((width - 50, 215), prep("العنوان :"), fill=(80, 100, 90), font=label_font, anchor="ra")
    draw.text((width - 50, 248), prep(gt["addr"]), fill=(15, 25, 20), font=body_font, anchor="ra")

    # 3. National ID Band
    draw.text((width - 50, 310), prep("الرقم القومي :"), fill=(80, 100, 90), font=label_font, anchor="ra")
    draw.text((width - 50, 340), gt["nid"], fill=(10, 20, 15), font=nid_font, anchor="ra")

    # 4. Factory code
    draw.text((50, 360), gt["fc"], fill=(50, 70, 60), font=nid_font, anchor="la")

    # Watermark Notice
    draw.text((width // 2, height - 35), "FOR LOCAL SIMULATION ONLY — NEVER AN AUTHENTIC DOCUMENT", fill=(180, 100, 100), font=stamp_font, anchor="mm")

    return img

def apply_condition_transform(img: Image.Image, item: dict) -> Image.Image:
    cond = item["cond"]
    dtl = item["dtl"]

    if cond == "clean":
        return img

    elif cond == "blur":
        r = dtl.get("radius", 2.0)
        return img.filter(ImageFilter.GaussianBlur(radius=r))

    elif cond == "rotation_perspective":
        if "angle" in dtl:
            ang = dtl["angle"]
            return img.rotate(ang, expand=True, fillcolor=(255, 255, 255), resample=Image.BICUBIC)
        elif dtl.get("perspective") == "keystone_tilt":
            # Apply 3D keystone projective warp using OpenCV
            arr = np.array(img)
            h, w = arr.shape[:2]
            src_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            dst_pts = np.float32([[w * 0.04, h * 0.06], [w * 0.94, h * 0.02], [w * 0.98, h * 0.95], [w * 0.02, h * 0.98]])
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(arr, matrix, (w, h), borderValue=(255, 255, 255))
            return Image.fromarray(warped)

    elif cond == "glare":
        out = img.copy()
        draw = ImageDraw.Draw(out, "RGBA")
        region = dtl.get("region")
        if region == "top_right":
            # Glare ellipse near top right header
            draw.ellipse([(550, 20), (840, 140)], fill=(255, 255, 255, 175))
        elif region == "center_hotspot":
            # Center bright flash
            draw.ellipse([(320, 180), (580, 340)], fill=(255, 255, 255, 180))
        elif region == "diagonal_washout":
            # Diagonal light band
            draw.polygon([(200, 0), (450, 0), (750, 540), (500, 540)], fill=(255, 255, 255, 120))
        elif region == "bottom_stripe":
            # Bottom light glare over factory code / watermark
            draw.rectangle([(20, 340), (400, 480)], fill=(255, 255, 255, 150))
        elif region == "photo_corner":
            # Glare over photo and name edge
            draw.ellipse([(120, 90), (320, 220)], fill=(255, 255, 255, 160))
        return out

    elif cond == "low_light_noise":
        out = img.copy()
        if "brightness" in dtl and "noise_sigma" not in dtl and "contrast" not in dtl:
            enh = ImageEnhance.Brightness(out)
            out = enh.enhance(dtl["brightness"])
        elif "noise_sigma" in dtl and "brightness" not in dtl:
            arr = np.array(out).astype(np.float32)
            noise = np.random.normal(0, dtl["noise_sigma"], arr.shape)
            noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
            out = Image.fromarray(noisy)
        elif "sp_amount" in dtl:
            arr = np.array(out)
            h, w, c = arr.shape
            num_sp = int(dtl["sp_amount"] * h * w)
            coords = [np.random.randint(0, i - 1, num_sp) for i in (h, w)]
            arr[tuple(coords)] = 255
            coords = [np.random.randint(0, i - 1, num_sp) for i in (h, w)]
            arr[tuple(coords)] = 0
            out = Image.fromarray(arr)
        elif "contrast" in dtl:
            enh_c = ImageEnhance.Contrast(out)
            out = enh_c.enhance(dtl["contrast"])
            enh_b = ImageEnhance.Brightness(out)
            out = enh_b.enhance(dtl.get("brightness", 0.60))
        elif "brightness" in dtl and "noise_sigma" in dtl:
            enh = ImageEnhance.Brightness(out)
            dim = enh.enhance(dtl["brightness"])
            arr = np.array(dim).astype(np.float32)
            noise = np.random.normal(0, dtl["noise_sigma"], arr.shape)
            noisy = np.clip(arr + noise, 0, 255).astype(np.uint8)
            out = Image.fromarray(noisy)
        return out

    elif cond == "partial_occlusion":
        out = img.copy()
        draw = ImageDraw.Draw(out, "RGBA")
        t = dtl.get("type")
        if t == "sticker_address":
            # Yellow masking tape over right half of address
            draw.rectangle([(420, 235), (820, 280)], fill=(245, 235, 170, 240))
            draw.text((620, 257), "OCCLUDED", fill=(120, 100, 30, 255), font=resolve_font('arial.ttf', 13), anchor="mm")
        elif t == "thumb_bottom_left":
            # Dark thumb shadow covering factory code
            draw.ellipse([(15, 320), (170, 470)], fill=(28, 24, 24, 245))
        elif t == "dark_bar_header":
            # Dark bar over top-left header
            draw.rectangle([(30, 35), (280, 105)], fill=(35, 35, 35, 235))
        elif t == "paper_clip_top":
            # Metallic paper clip at top center edge
            draw.rounded_rectangle([(380, 8), (420, 85)], radius=12, fill=(190, 195, 200, 250), outline=(90, 95, 100), width=3)
            draw.rounded_rectangle([(390, 22), (410, 72)], radius=8, outline=(90, 95, 100), width=2)
        elif t == "barcode_sticker_id":
            # Barcode sticker over right 5 digits of ID
            draw.rectangle([(640, 325), (825, 375)], fill=(255, 255, 255, 250), outline=(50, 50, 50), width=1)
            # Simulated barcode vertical lines
            for bx in range(650, 815, 4):
                draw.line([(bx, 330), (bx, 370)], fill=(20, 20, 20), width=2)
        return out

    return img

def main():
    np.random.seed(42)
    manifest = []

    print(f"Generating 40 improved synthetic cards in {OUTPUT_DIR}...")
    for item in IDENTITIES_40:
        cid = item["id"]
        base = render_base_card(item)
        final_img = apply_condition_transform(base, item)

        filename = f"{cid}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        final_img.save(filepath, format="PNG")

        entry = {
            "card_id": cid,
            "filename": filename,
            "file_path": os.path.relpath(filepath, os.path.abspath(os.path.join(OUTPUT_DIR, "..", ".."))).replace("\\", "/"),
            "condition": item["cond"],
            "condition_details": item["dtl"],
            "ground_truth": {
                "national_id": item["nid"],
                "masked_id": item["nid"][:7] + "****" + item["nid"][-3:],
                "name": item["name"],
                "address": item["addr"],
                "factory_code": item["fc"],
                "governorate": item["gov"],
                "birth_date": item["bdate"],
                "gender": item["sex"],
            }
        }
        manifest.append(entry)
        print(f"Generated [{item['cond']:22s}]: {filename}")

    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nSaved updated manifest with {len(manifest)} entries to {manifest_path}")

if __name__ == "__main__":
    main()

