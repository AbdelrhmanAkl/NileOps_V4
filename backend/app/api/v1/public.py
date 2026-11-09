"""Public Banking Products, Branches, and FAQs."""

from typing import List
from fastapi import APIRouter
from app.schemas.banking import BranchInfo, FAQItem, ProductInfo

router = APIRouter(prefix="/public", tags=["Public Banking Services"])

PRODUCTS_DATA = [
    ProductInfo(
        id="prod-01",
        category="ACCOUNTS",
        name_en="Classic Current Account",
        name_ar="الحساب الجاري الكلاسيكي",
        description_en="Daily transactional account with free debit card and mobile banking access.",
        description_ar="حساب يومي للمعاملات المصرفية مع بطاقة خصم مباشر مجانية وتطبيق الهاتف المحمول.",
        interest_rate=0.0,
        min_balance=2500.0,
        term_months=None,
        features_en=["Free Visa Debit Card", "Cheque Book availability", "InstaPay support"],
        features_ar=["بطاقة فيزا للخصم المباشر مجاناً", "إمكانية إصدار دفتر شيكات", "دعم كامل لشبكة إنستاباي"],
    ),
    ProductInfo(
        id="prod-02",
        category="SAVINGS",
        name_en="High-Yield Monthly Savings Account",
        name_ar="حساب التوفير عالي العائد الشهري",
        description_en="Tiered interest calculated on minimum monthly balance and paid monthly.",
        description_ar="عائد تصاعدي يحتسب على أدنى رصيد شهري ويصرف شهرياً في الحساب.",
        interest_rate=12.5,
        min_balance=10000.0,
        term_months=None,
        features_en=["Monthly payout", "Tiered returns up to 14%", "No penalty for partial withdrawal"],
        features_ar=["صرف العائد شهرياً", "عائد تصاعدي يصل إلى 14%", "لا توجد غرامات على السحب الجزئي"],
    ),
    ProductInfo(
        id="prod-03",
        category="CERTIFICATES",
        name_en="Nile Platinum 3-Year Certificate of Deposit",
        name_ar="شهادة النيل البلاتينية الثلاثية",
        description_en="Fixed 23.5% annual return with monthly interest credit for 36 months.",
        description_ar="عائد سنوي ثابت 23.5% يصرف شهرياً لمدة 36 شهراً.",
        interest_rate=23.5,
        min_balance=1000.0,
        term_months=36,
        features_en=["Fixed return for 3 years", "Borrowing up to 90% of value", "Credit card against certificate"],
        features_ar=["عائد ثابت طوال 3 سنوات", "إمكانية الاقتراض بضمان حتى 90%", "إصدار بطاقة ائتمانية بضمان الشهادة"],
    ),
]

BRANCHES_DATA = [
    BranchInfo(
        id="br-01",
        code="CAI-01",
        name_en="Zamalek Main Branch",
        name_ar="فرع الزمالك الرئيسي",
        city_en="Cairo",
        city_ar="القاهرة",
        address_en="26 July Street, Zamalek, Cairo",
        address_ar="شارع 26 يوليو، الزمالك، القاهرة",
        working_hours="8:30 AM - 3:00 PM (Sun-Thu)",
        phone="+20 2 2736 1000",
        has_atm=True,
    ),
    BranchInfo(
        id="br-02",
        code="CAI-02",
        name_en="New Cairo 5th Settlement",
        name_ar="فرع التجمع الخامس",
        city_en="Cairo",
        city_ar="القاهرة",
        address_en="90th Street North, 5th Settlement, New Cairo",
        address_ar="شارع التسعين الشمالي، التجمع الخامس، القاهرة الجديدة",
        working_hours="8:30 AM - 4:00 PM (Sun-Thu)",
        phone="+20 2 2810 2000",
        has_atm=True,
    ),
    BranchInfo(
        id="br-03",
        code="ALX-01",
        name_en="Alexandria Smouha Branch",
        name_ar="فرع سموحة الإسكندرية",
        city_en="Alexandria",
        city_ar="الإسكندرية",
        address_en="Fawzy Moaz St, Smouha, Alexandria",
        address_ar="شارع فوزي معاذ، سموحة، الإسكندرية",
        working_hours="8:30 AM - 3:00 PM (Sun-Thu)",
        phone="+20 3 429 3000",
        has_atm=True,
    ),
]

FAQS_DATA = [
    FAQItem(
        id="faq-01",
        category="ONBOARDING",
        question_en="What documents are required to open a retail bank account?",
        question_ar="ما هي المستندات المطلوبة لفتح حساب مصرفي للأفراد؟",
        answer_en="Valid Egyptian National ID card, proof of employment or income (or commercial register for business owners), and initial opening deposit.",
        answer_ar="بطاقة الرقم القومي سارية المفعول، إثبات الدخل أو مفردات المرتب (أو السجل التجاري لأصحاب الأعمال)، والحد الأدنى للإيداع الأولي.",
    ),
    FAQItem(
        id="faq-02",
        category="CERTIFICATES",
        question_en="Can I redeem a Certificate of Deposit before maturity?",
        question_ar="هل يمكن استرداد شهادة الادخار قبل تاريخ الاستحقاق؟",
        answer_en="Yes, redemption is permitted after 6 months from the issuance date according to the bank's early redemption recovery rate schedule.",
        answer_ar="نعم، يجوز الاسترداد بعد مرور 6 أشهر من تاريخ الشراء وفقاً لجدول الاسترداد المبكر المعتمد من البنك المركزي.",
    ),
    FAQItem(
        id="faq-03",
        category="TRANSFERS",
        question_en="How fast are transfers using InstaPay?",
        question_ar="ما هي سرعة التحويلات عبر شبكة إنستاباي؟",
        answer_en="Transfers are executed and settled instantly (within seconds) 24/7 across all participating Egyptian banks and digital wallets.",
        answer_ar="تتم التحويلات وتسوّى لحظياً (خلال ثوانٍ معدودة) على مدار الساعة طوال أيام الأسبوع بين جميع البنوك والمحافظ الإلكترونية المشاركة في مصر.",
    ),
]


@router.get("/products", response_model=List[ProductInfo])
async def list_products():
    """List available simulated banking products and deposit terms."""
    return PRODUCTS_DATA


@router.get("/branches", response_model=List[BranchInfo])
async def list_branches():
    """List simulated bank branch network and working hours."""
    return BRANCHES_DATA


@router.get("/faqs", response_model=List[FAQItem])
async def list_faqs():
    """List bilingual banking customer service FAQs."""
    return FAQS_DATA


CARD_PRODUCTS_DATA = [
    {
        "id": "DEBIT_VISA_CLASSIC",
        "name_en": "Nile Classic Visa Debit Card",
        "name_ar": "بطاقة فيزا الكلاسيكية للخصم المباشر",
        "type": "DEBIT",
        "features_en": ["Instant ATM cash access", "Contactless NFC payments", "Online shopping security with 3D Secure"],
        "features_ar": ["سحب نقدي فوري من الصراف الآلي", "مدفوعات لا تلامسية NFC", "تسوق آمن عبر الإنترنت مع 3D Secure"],
    },
    {
        "id": "DEBIT_MASTERCARD_TITANIUM",
        "name_en": "Nile Titanium Mastercard Debit Card",
        "name_ar": "بطاقة ماستركارد تيتانيوم للخصم المباشر",
        "type": "DEBIT",
        "features_en": ["Airport lounge access (MENA)", "Higher daily withdrawal limits", "Priceless Cities discounts"],
        "features_ar": ["دخول صالات كبار الزوار بالمطارات (الشرق الأوسط)", "حدود سحب يومية أعلى", "خصومات برايسليس"],
    },
    {
        "id": "CREDIT_VISA_PLATINUM",
        "name_en": "Nile Platinum Visa Credit Card",
        "name_ar": "بطاقة فيزا البلاتينية الائتمانية",
        "type": "CREDIT",
        "features_en": ["Up to 55 days interest-free grace period", "Reward points on all purchases", "Purchase protection & extended warranty"],
        "features_ar": ["فترة سماح تصل إلى 55 يوماً بدون فوائد", "نقاط مكافآت على جميع المشتريات", "حماية المشتريات وتمديد الضمان"],
    },
    {
        "id": "PREPAID_MEEZA",
        "name_en": "Nile Meeza National Prepaid Card",
        "name_ar": "بطاقة ميزة الوطنية مسبقة الدفع",
        "type": "PREPAID",
        "features_en": ["Acceptance across all domestic Egyptian merchants", "Instant top-up via mobile banking", "Government payments compliant"],
        "features_ar": ["قبول لدى جميع التجار في جمهورية مصر العربية", "شحن فوري عبر التطبيق المصرفي", "متوافقة مع المدفوعات الحكومية"],
    },
]


@router.get("/cards")
async def list_card_products():
    """List available synthetic payment card products."""
    return CARD_PRODUCTS_DATA

