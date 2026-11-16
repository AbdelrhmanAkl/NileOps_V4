"""Authentication Endpoints & Demo Seeder."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, log_audit_event
from app.core.config import settings
from app.core.exceptions import AuthenticationException
from app.core.rate_limit import limiter
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.banking import Account, Transaction
from app.models.complaint import Complaint
from app.models.kyc import KycVerification
from app.models.policy import PolicyDocument
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password, returning JWT and user profile."""
    # 1. Check Rate Limit & Account Lockout Guard
    clean_email = credentials.email.lower().strip()
    await limiter.check_rate_limit(
        request,
        endpoint_tag="auth_login",
        max_requests=settings.RATE_LIMIT_LOGIN_MAX,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
        identifier_override=f"{clean_email}_{limiter._get_client_ip(request)}",
    )
    await limiter.check_login_lockout(clean_email)

    stmt = select(User).where(User.email == clean_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        await limiter.record_login_attempt(clean_email, success=False)
        raise AuthenticationException("Invalid email address or password.")

    if not user.is_active:
        await limiter.record_login_attempt(clean_email, success=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    # Successful login: reset lockout counters
    await limiter.record_login_attempt(clean_email, success=True)

    # Create signed JWT token
    token = create_access_token(
        subject=user.id,
        claims={
            "email": user.email,
            "role": user.role,
            "user_type": user.user_type,
            "full_name": user.full_name,
        },
    )

    await log_audit_event(
        db,
        action="LOGIN",
        resource_type="AUTH",
        resource_id=user.id,
        user=user,
        details={"email": user.email, "role": user.role},
    )

    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve currently authenticated user profile."""
    return UserOut.model_validate(current_user)


@router.post("/seed", tags=["Demo Simulation"])
async def seed_demo_data(db: AsyncSession = Depends(get_db)):
    """Seed synthetic NileOps Demo Bank database with canonical users, accounts, policies, and complaints."""
    # Check if already seeded
    existing = await db.execute(select(User))
    if existing.scalars().first():
        return {"status": "already_seeded", "message": "Demo database already populated."}

    now = datetime.now(timezone.utc)

    # 1. Canonical 5 Staff Roles + 2 Retail Customers
    default_pass = get_password_hash("NileOps2026!")
    cust_pass = get_password_hash("Customer2026!")

    users_data = [
        # Canonical Staff
        User(
            id="usr-admin-01",
            email="admin@nileops.demo",
            hashed_password=default_pass,
            full_name="Mahmoud Farouk",
            role="admin",
            user_type="employee",
            phone_number="+20 100 111 2233",
        ),
        User(
            id="usr-ops-01",
            email="ops@nileops.demo",
            hashed_password=default_pass,
            full_name="Sarah El-Sayed",
            role="operations_officer",
            user_type="employee",
            phone_number="+20 100 222 3344",
        ),
        User(
            id="usr-cs-01",
            email="cs@nileops.demo",
            hashed_password=default_pass,
            full_name="Tarek El-Ghandour",
            role="customer_service",
            user_type="employee",
            phone_number="+20 100 333 4455",
        ),
        User(
            id="usr-comp-01",
            email="compliance@nileops.demo",
            hashed_password=default_pass,
            full_name="Nourhan Kamel",
            role="compliance_reviewer",
            user_type="employee",
            phone_number="+20 100 444 5566",
        ),
        User(
            id="usr-mgr-01",
            email="manager@nileops.demo",
            hashed_password=default_pass,
            full_name="Sherif Osman",
            role="branch_manager",
            user_type="employee",
            phone_number="+20 100 555 6677",
        ),
        # Retail Customers
        User(
            id="usr-cust-01",
            email="customer1@nileops.demo",
            hashed_password=cust_pass,
            full_name="Ahmed Mansour",
            role="customer",
            user_type="customer",
            phone_number="+20 102 777 8899",
        ),
        User(
            id="usr-cust-02",
            email="customer2@nileops.demo",
            hashed_password=cust_pass,
            full_name="Layla Hassan",
            role="customer",
            user_type="customer",
            phone_number="+20 102 888 9900",
        ),
    ]
    for u in users_data:
        db.add(u)
    await db.flush()

    # 2. Synthetic Accounts for Customer 1 (Ahmed Mansour)
    acc1 = Account(
        id="acc-001",
        user_id="usr-cust-01",
        account_number="EG98000100010000000012345678",
        account_type="current",
        currency="EGP",
        balance=45250.75,
        interest_rate=0.0,
        status="ACTIVE",
    )
    acc2 = Account(
        id="acc-002",
        user_id="usr-cust-01",
        account_number="EG98000100020000000087654321",
        account_type="savings",
        currency="EGP",
        balance=185400.00,
        interest_rate=12.5,
        status="ACTIVE",
    )
    acc3 = Account(
        id="acc-003",
        user_id="usr-cust-01",
        account_number="EG98000100030000000099887766",
        account_type="certificate",
        currency="EGP",
        balance=500000.00,
        interest_rate=23.5,
        status="ACTIVE",
    )
    # Synthetic Accounts for Customer 2 (Layla Hassan)
    acc4 = Account(
        id="acc-004",
        user_id="usr-cust-02",
        account_number="EG98000100010000000055443322",
        account_type="current",
        currency="EGP",
        balance=12400.50,
        interest_rate=0.0,
        status="ACTIVE",
    )
    db.add_all([acc1, acc2, acc3, acc4])
    await db.flush()

    # 3. Synthetic Transactions for Ahmed Mansour (Chronologically spaced timestamps)
    txns = [
        Transaction(
            id="txn-001",
            account_id="acc-001",
            reference_number="TXN-20261101-001",
            transaction_type="DEPOSIT",
            amount=35000.00,
            currency="EGP",
            description="Monthly Salary Transfer — Nile Tech Solutions",
            description_ar="تحويل راتب شهري — شركة نايل تك",
            counterparty="Nile Tech Payroll",
            status="COMPLETED",
            timestamp=datetime(2026, 11, 1, 9, 30, 0, tzinfo=timezone.utc),
        ),
        Transaction(
            id="txn-002",
            account_id="acc-001",
            reference_number="TXN-20261103-002",
            transaction_type="BILL_PAYMENT",
            amount=-1250.00,
            currency="EGP",
            description="Electricity & Utilities Bill (Fawry Payment)",
            description_ar="سداد فاتورة الكهرباء والمرافق (فوري)",
            counterparty="South Cairo Electricity Co.",
            status="COMPLETED",
            timestamp=datetime(2026, 11, 3, 14, 15, 0, tzinfo=timezone.utc),
        ),
        Transaction(
            id="txn-003",
            account_id="acc-001",
            reference_number="TXN-20261105-003",
            transaction_type="WITHDRAWAL",
            amount=-3000.00,
            currency="EGP",
            description="ATM Cash Withdrawal — Zamalek Branch ATM #04",
            description_ar="سحب نقدي من الصراف الآلي — فرع الزمالك #04",
            counterparty="NileOps ATM Zamalek",
            status="COMPLETED",
            timestamp=datetime(2026, 11, 5, 18, 45, 0, tzinfo=timezone.utc),
        ),
        Transaction(
            id="txn-004",
            account_id="acc-002",
            reference_number="TXN-20261106-004",
            transaction_type="INTEREST_CREDIT",
            amount=1931.25,
            currency="EGP",
            description="Monthly High-Yield Savings Interest Credit",
            description_ar="إضافة العائد الشهري لحساب التوفير عالي العائد",
            counterparty="NileOps Treasury Operations",
            status="COMPLETED",
            timestamp=datetime(2026, 11, 6, 0, 1, 0, tzinfo=timezone.utc),
        ),
    ]
    db.add_all(txns)

    # 4. Synthetic Complaints
    c1 = Complaint(
        id="cmp-001",
        ticket_number="CMP-2026-0101",
        customer_id="usr-cust-01",
        category="ATM_CARD",
        category_ar="بطاقات الصراف الآلي",
        subject="ATM debited amount without dispensing cash",
        details="Attempted to withdraw 2,000 EGP at Zamalek ATM on Nov 4. The ATM timed out and debited my balance but did not dispense cash.",
        status="IN_PROGRESS",
        priority="HIGH",
        assigned_to_id="usr-cs-01",
        staff_notes="Sent inquiry to Cash Logistics Team for ATM journal reconciliation.",
    )
    c2 = Complaint(
        id="cmp-002",
        ticket_number="CMP-2026-0102",
        customer_id="usr-cust-01",
        category="MOBILE_BANKING",
        category_ar="الخدمات المصرفية عبر الهاتف",
        subject="Delayed InstaPay instant transfer confirmation",
        details="Transferred 500 EGP to Fawry wallet. Status showed processing for 10 minutes before confirming.",
        status="RESOLVED",
        priority="LOW",
        assigned_to_id="usr-cs-01",
        staff_notes="InstaPay gateway had brief downstream network latency.",
        resolution_notes="Transaction confirmed successfully; customer notified via SMS.",
    )
    db.add_all([c1, c2])

    # 5. Synthetic Policy Knowledge Base Documents across 12 Policy Domains
    p1 = PolicyDocument(
        id="pol-001",
        code="POL-RETAIL-001",
        title_en="Retail Deposit Accounts Opening & Minimum Balance Guidelines",
        title_ar="إرشادات فتح حسابات الودائع للأفراد والحد الأدنى للرصيد",
        domain="retail_banking",
        content_en="Retail customers may open Current and Savings accounts in EGP. The minimum opening balance for Classic Current Accounts is 2,500 EGP. Minimum balance for High-Yield Monthly Savings is 10,000 EGP. A monthly maintenance fee of 25 EGP applies if the balance falls below the minimum requirement.",
        content_ar="يجوز للعملاء الأفراد فتح حسابات جارية وحسابات توفير بالجنيه المصري. الحد الأدنى لفتح الحساب الجاري الكلاسيكي هو 2,500 جنيه مصري، والحد الأدنى لحساب التوفير عالي العائد هو 10,000 جنيه مصري. تطبق رسوم صيانة دورية قدرها 25 جنيهاً مصرياً إذا انخفض الرصيد عن الحد الأدنى.",
        version="1.0.0",
        status="INDEXED",
        created_by_id="usr-ops-01",
        approved_by_id="usr-comp-01",
        approved_at=now,
        approval_notes="Fully compliant with Central Bank of Egypt Retail Banking Regulations 2026.",
    )
    p2 = PolicyDocument(
        id="pol-002",
        code="POL-KYC-001",
        title_en="Customer Due Diligence & Synthetic Egyptian National ID Standards",
        title_ar="معايير العناية الواجبة وتدقيق بطاقات الرقم القومي الاصطناعية",
        domain="kyc_aml",
        content_en="National ID verification requires checking the 14-digit format: digit 1 indicates century (2 for 1900-1999, 3 for 2000-2099); digits 2-7 denote birth date (YYMMDD); digits 8-9 denote governorate code (01 for Cairo, 02 for Alexandria, 03 for Port Said, etc.); digit 14 serves as checksum. Strictly synthetic document fixtures must be used for testing and QA.",
        content_ar="يتطلب التحقق من الرقم القومي فحص الهيكل المكون من 14 رقماً: الرقم الأول يعبر عن القرن (2 لمواليد 1900-1999، 3 لمواليد 2000-2099)؛ الأرقام 2 إلى 7 تعبر عن تاريخ الميلاد (سنة شهر يوم)؛ الرقمان 8 و9 يعبران عن كود محافظة الميلاد (01 القاهرة، 02 الإسكندرية، 03 بورسعيد، إلخ)؛ الرقم 14 يمثل رقم التدقيق الحسابي. يجب قصر الاختبارات تماماً على وثائق وبيانات اصطناعية.",
        version="1.0.0",
        status="APPROVED",
        created_by_id="usr-ops-01",
        approved_by_id="usr-comp-01",
        approved_at=now,
        approval_notes="Approved under compliance review protocols.",
    )
    p3 = PolicyDocument(
        id="pol-003",
        code="POL-DIGITAL-001",
        title_en="InstaPay & Fast Transfer Daily Limits and Operations",
        title_ar="حدود وعمليات التحويل اللحظي عبر شبكة المدفوعات اللحظية إنستاباي",
        domain="digital_channels",
        content_en="In accordance with National Payments Council directives, the maximum single transaction limit on InstaPay is 70,000 EGP, with a daily cap of 120,000 EGP and monthly aggregate ceiling of 400,000 EGP per customer. Zero transfer fees are charged for retail peer-to-peer transfers.",
        content_ar="وفقاً لتعليمات المجلس القومي للمدفوعات، فإن الحد الأقصى للعملية الواحدة عبر إنستاباي هو 70,000 جنيه مصري، بحد أقصى يومي 120,000 جنيه ومجموع شهري 400,000 جنيه للعميل الواحد. لا تفرض أي رسوم تحويل على المعاملات بين الأفراد.",
        version="1.1.0",
        status="PENDING_APPROVAL",
        created_by_id="usr-ops-01",
    )
    db.add_all([p1, p2, p3])

    # 6. Synthetic KYC Record
    kyc1 = KycVerification(
        id="kyc-001",
        tracking_number="KYC-2026-0042",
        customer_id="usr-cust-01",
        synthetic_national_id="29005120101234",
        document_type="EGYPTIAN_NATIONAL_ID_SYNTHETIC",
        status="VERIFIED_SYNTHETIC",
        extracted_data_json='{"name": "Ahmed Mansour", "governorate": "Cairo (01)", "dob": "1990-05-12", "gender": "Male", "source": "SYNTHETIC_FIXTURE_APPROVED"}',
        reviewer_id="usr-comp-01",
        reviewer_notes="Verified synthetic fixture under Table 7.1.1 Document AI criteria.",
    )
    db.add(kyc1)

    await db.commit()
    return {
        "status": "success",
        "message": "NileOps Demo Bank successfully seeded with canonical staff, customers, accounts, complaints, and policies.",
    }

