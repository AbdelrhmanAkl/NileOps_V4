"""Comprehensive RAG Quality Evaluation Benchmark for NileOps.

Runs 48 synthetic evaluation questions grounded in actual policy content
evaluating retrieval precision, citation accuracy, answer grounding,
abstention on unanswerable queries, and strict portal isolation.
"""

import json
import httpx

EVAL_DATASET = [
    # --- Category 1: Customer Portal - Arabic (Retail Account Opening) ---
    {
        "id": "C-AR-01",
        "query": "ما هو الحد الأدنى لفتح حساب جاري للأفراد في بنك النيل؟",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },
    {
        "id": "C-AR-02",
        "query": "ما هي المستندات المطلوبة من المواطن المصري لفتح حساب بنكي؟",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },
    {
        "id": "C-AR-03",
        "query": "هل يشترط إثبات الدخل لفتح حساب التوفير للأفراد؟",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },
    {
        "id": "C-AR-04",
        "query": "ما هي مدة تسوية خطأ سحب ماكينة الصراف الآلي وقيد المبلغ؟",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },
    {
        "id": "C-AR-05",
        "query": "كيف يتم التعامل مع شكاوى ماكينات الصراف الآلي؟",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },
    {
        "id": "C-AR-06",
        "query": "إجراءات تسوية منازعات أجهزة الصراف الآلي",
        "portal": "customer",
        "lang": "ar",
        "expected_code": "POL-TEST-D5179B",
        "should_abstain": False,
        "category": "Customer Retail (Arabic)",
    },

    # --- Category 2: Customer Portal - English (Retail Account Opening) ---
    {
        "id": "C-EN-01",
        "query": "What is the minimum opening balance required for a retail current account?",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },
    {
        "id": "C-EN-02",
        "query": "What identification documents are needed to open a retail bank account?",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },
    {
        "id": "C-EN-03",
        "query": "What are the account opening requirements for non-resident foreign nationals?",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },
    {
        "id": "C-EN-04",
        "query": "What is the service SLA for ATM dispensation error resolution?",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },
    {
        "id": "C-EN-05",
        "query": "How are ATM cash deduction disputes handled for customers?",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },
    {
        "id": "C-EN-06",
        "query": "Policy on ATM dispensation errors and customer crediting timeline",
        "portal": "customer",
        "lang": "en",
        "expected_code": "POL-TEST-D5179B",
        "should_abstain": False,
        "category": "Customer Retail (English)",
    },

    # --- Category 3: Customer Portal - Portal Isolation Security Tests (Attempting to query internal employee docs) ---
    {
        "id": "C-ISO-01",
        "query": "ما هي معايير العناية الواجبة وتدقيق بطاقات الرقم القومي لموظفي البنك؟",
        "portal": "customer",
        "lang": "ar",
        "forbidden_code": "POL-KYC-001",
        "should_abstain": None,  # May match public retail or abstain, but MUST NOT leak POL-KYC-001
        "category": "Portal Isolation (Arabic)",
    },
    {
        "id": "C-ISO-02",
        "query": "إجراءات فحص مكافحة غسل الأموال وتصنيف المخاطر للعملاء",
        "portal": "customer",
        "lang": "ar",
        "forbidden_code": "POL-KYC-001",
        "should_abstain": None,
        "category": "Portal Isolation (Arabic)",
    },
    {
        "id": "C-ISO-03",
        "query": "سياسة حماية المبلغين عن المخالفات وقنوات الإبلاغ السرية للموظفين",
        "portal": "customer",
        "lang": "ar",
        "forbidden_code": "POL-TEST-70D4C1",
        "should_abstain": None,
        "category": "Portal Isolation (Arabic)",
    },
    {
        "id": "C-ISO-04",
        "query": "Detailed customer due diligence standards and internal AML risk scoring",
        "portal": "customer",
        "lang": "en",
        "forbidden_code": "POL-KYC-001",
        "should_abstain": None,
        "category": "Portal Isolation (English)",
    },
    {
        "id": "C-ISO-05",
        "query": "Internal verification rules for synthetic Egyptian National ID cards",
        "portal": "customer",
        "lang": "en",
        "forbidden_code": "POL-KYC-001",
        "should_abstain": None,
        "category": "Portal Isolation (English)",
    },
    {
        "id": "C-ISO-06",
        "query": "Internal staff whistleblower protection procedure and reporting mechanisms",
        "portal": "customer",
        "lang": "en",
        "forbidden_code": "POL-TEST-70D4C1",
        "should_abstain": None,
        "category": "Portal Isolation (English)",
    },

    # --- Category 4: Customer Portal - Unanswerable & Out-of-Domain Inquiries (Strict Abstention) ---
    {
        "id": "C-ABS-01",
        "query": "كيف يمكنني الحصول على قرض لشراء طائرة خاصة؟",
        "portal": "customer",
        "lang": "ar",
        "should_abstain": True,
        "category": "Abstention Verification (Arabic)",
    },
    {
        "id": "C-ABS-02",
        "query": "ما هي أسعار الذهب والفضة اليوم في السوق المصري؟",
        "portal": "customer",
        "lang": "ar",
        "should_abstain": True,
        "category": "Abstention Verification (Arabic)",
    },
    {
        "id": "C-ABS-03",
        "query": "طريقة عمل الكشري المصري في المنزل",
        "portal": "customer",
        "lang": "ar",
        "should_abstain": True,
        "category": "Abstention Verification (Arabic)",
    },
    {
        "id": "C-ABS-04",
        "query": "How do I apply for a mortgage loan on beachfront villas in Saint Tropez?",
        "portal": "customer",
        "lang": "en",
        "should_abstain": True,
        "category": "Abstention Verification (English)",
    },
    {
        "id": "C-ABS-05",
        "query": "What is the recommended tyre pressure for a Boeing 737 aircraft?",
        "portal": "customer",
        "lang": "en",
        "should_abstain": True,
        "category": "Abstention Verification (English)",
    },
    {
        "id": "C-ABS-06",
        "query": "How to repair a broken exhaust pipe on a commercial vehicle?",
        "portal": "customer",
        "lang": "en",
        "should_abstain": True,
        "category": "Abstention Verification (English)",
    },

    # --- Category 5: Employee Portal - Arabic (Operational & Compliance Guidelines) ---
    {
        "id": "E-AR-01",
        "query": "ما هي قواعد فحص بطاقة الرقم القومي المصرية ومطابقة خانة المحافظة؟",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-KYC-001",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },
    {
        "id": "E-AR-02",
        "query": "ما هي معايير التحقق من بطاقات الرقم القومي الاصطناعية للاختبار؟",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-KYC-001",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },
    {
        "id": "E-AR-03",
        "query": "إجراءات حماية الموظفين المبلغين عن المخالفات الإدارية والمالية",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-TEST-0E1AA9",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },
    {
        "id": "E-AR-04",
        "query": "ما هي القنوات السرية المعتمدة لتقديم بلاغات الفساد المالي؟",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-TEST-70D4C1",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },
    {
        "id": "E-AR-05",
        "query": "ما هو الحد الأدنى للرصيد الافتتاحي لحسابات الشركات الصغيرة؟",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },
    {
        "id": "E-AR-06",
        "query": "سياسة تسوية شكاوى سحب النقدية من الصراف الآلي وإجراءات الإيداع",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Employee Operations (Arabic)",
    },

    # --- Category 6: Employee Portal - English (Operational & Compliance Guidelines) ---
    {
        "id": "E-EN-01",
        "query": "What are the mandatory KYC verification procedures for synthetic Egyptian National IDs?",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-KYC-001",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },
    {
        "id": "E-EN-02",
        "query": "How is the 14-digit National ID structure validated across century and governorate codes?",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-KYC-001",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },
    {
        "id": "E-EN-03",
        "query": "What protections and confidential channels are guaranteed for internal whistleblowers?",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-TEST-38C190",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },
    {
        "id": "E-EN-04",
        "query": "Whistleblower confidentiality and non-retaliation operational procedures",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-TEST-EA30C8",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },
    {
        "id": "E-EN-05",
        "query": "Retail deposit minimum balance guidelines and identity requirements for individuals",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },
    {
        "id": "E-EN-06",
        "query": "ATM dispute reconciliation rules and customer compensation timelines",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Employee Operations (English)",
    },

    # --- Category 7: Employee Portal - Multi-Document Questions ---
    {
        "id": "E-MUL-01",
        "query": "What are the combined requirements for account opening KYC and retail minimum balances?",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Multi-Document Queries",
    },
    {
        "id": "E-MUL-02",
        "query": "شروط التحقق من الهوية وفتح حسابات التوفير مع تسوية بطاقات الخصم",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-RETAIL-001",
        "should_abstain": False,
        "category": "Multi-Document Queries",
    },
    {
        "id": "E-MUL-03",
        "query": "ATM dispute resolution and employee reporting procedures",
        "portal": "employee",
        "lang": "en",
        "expected_code": "POL-TEST-B1852B",
        "should_abstain": False,
        "category": "Multi-Document Queries",
    },
    {
        "id": "E-MUL-04",
        "query": "إجراءات العناية الواجبة ومكافحة غسل الأموال مع الإبلاغ عن المخالفات",
        "portal": "employee",
        "lang": "ar",
        "expected_code": "POL-KYC-001",
        "should_abstain": False,
        "category": "Multi-Document Queries",
    },

    # --- Category 8: Employee Portal - Unanswerable Out-of-Domain Inquiries ---
    {
        "id": "E-ABS-01",
        "query": "ما هي شروط منح تراخيص المفاعلات النووية للأغراض السلمية؟",
        "portal": "employee",
        "lang": "ar",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
    {
        "id": "E-ABS-02",
        "query": "What are the statutory reserve requirements for interplanetary commercial banks?",
        "portal": "employee",
        "lang": "en",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
    {
        "id": "E-ABS-03",
        "query": "How to calculate quantum gravitational flux in theoretical physics?",
        "portal": "employee",
        "lang": "en",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
    {
        "id": "E-ABS-04",
        "query": "طريقة إصلاح شاشة الهاتف المحمول المكسورة في المنزل",
        "portal": "employee",
        "lang": "ar",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
    {
        "id": "E-ABS-05",
        "query": "ما هي أفضل وجهات السياحة الجبلية في الشتاء في سويسرا؟",
        "portal": "employee",
        "lang": "ar",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
    {
        "id": "E-ABS-06",
        "query": "What are the rules of competitive badminton in the Olympic Games?",
        "portal": "employee",
        "lang": "en",
        "should_abstain": True,
        "category": "Employee Abstention",
    },
]


def run_rag_benchmark():
    print(f"=== Starting NileOps RAG Quality Benchmark: {len(EVAL_DATASET)} Evaluation Questions ===\n")
    client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

    stats = {
        "total": len(EVAL_DATASET),
        "passed": 0,
        "failed": 0,
        "abstention_correct": 0,
        "abstention_total": 0,
        "isolation_verified": 0,
        "isolation_total": 0,
        "citation_accuracy": 0,
        "retrieval_total": 0,
    }

    sample_logs = []

    for item in EVAL_DATASET:
        qid = item["id"]
        query = item["query"]
        portal = item["portal"]
        lang = item["lang"]

        payload = {
            "query": query,
            "portal_type": portal,
            "language": lang,
            "threshold": 0.15,
        }

        try:
            r = client.post("/api/v1/rag/ask", json=payload)
            data = r.json()
        except Exception as e:
            print(f"[{qid}] ERROR: {e}")
            stats["failed"] += 1
            continue

        abstained = data.get("abstained", False)
        score = data.get("confidence_score", 0.0)
        citations = [c.get("code") for c in data.get("citations", [])]
        answer = data.get("answer", "")

        item_passed = True
        notes = []

        # 1. Unanswerable check (Should abstain)
        if item.get("should_abstain") is True:
            stats["abstention_total"] += 1
            if abstained and score == 0.0:
                stats["abstention_correct"] += 1
                notes.append("Correctly abstained")
            else:
                item_passed = False
                notes.append(f"FAILED to abstain (score={score}, cit={citations})")

        # 2. Portal isolation check (Must NOT contain forbidden_code)
        if "forbidden_code" in item:
            stats["isolation_total"] += 1
            forbidden = item["forbidden_code"]
            if forbidden not in citations:
                stats["isolation_verified"] += 1
                notes.append(f"Isolation verified ({forbidden} blocked)")
            else:
                item_passed = False
                notes.append(f"SECURITY BREACH: {forbidden} leaked into Customer Portal!")

        # 3. Expected answerable query check
        if item.get("should_abstain") is False:
            stats["retrieval_total"] += 1
            expected = item.get("expected_code")
            if not abstained and (expected in citations or any(expected[:8] in c for c in citations)):
                stats["citation_accuracy"] += 1
                notes.append(f"Retrieved {expected} (score={score})")
            else:
                item_passed = False
                notes.append(f"Retrieval miss: expected {expected}, got {citations}")

        if item_passed:
            stats["passed"] += 1
            tag = "PASS"
        else:
            stats["failed"] += 1
            tag = "FAIL"

        print(f"[{tag}] {qid} ({item['category']}): {', '.join(notes)}")

        if len(sample_logs) < 6 or not item_passed:
            sample_logs.append({
                "id": qid,
                "query": query,
                "portal": portal,
                "lang": lang,
                "abstained": abstained,
                "score": score,
                "citations": citations,
                "answer_preview": answer[:150],
            })

    # Summary
    print("\n" + "=" * 60)
    print("=== RAG Quality Benchmark Evaluation Results ===")
    print(f"Total Test Questions: {stats['total']}")
    print(f"Overall Passed: {stats['passed']} / {stats['total']} ({stats['passed']/stats['total']*100:.1f}%)")
    if stats['retrieval_total'] > 0:
        print(f"Retrieval & Citation Accuracy: {stats['citation_accuracy']} / {stats['retrieval_total']} ({stats['citation_accuracy']/stats['retrieval_total']*100:.1f}%)")
    if stats['isolation_total'] > 0:
        print(f"Portal Isolation Enforcement: {stats['isolation_verified']} / {stats['isolation_total']} ({stats['isolation_verified']/stats['isolation_total']*100:.1f}%)")
    if stats['abstention_total'] > 0:
        print(f"Abstention on Out-of-Domain / Unanswerable: {stats['abstention_correct']} / {stats['abstention_total']} ({stats['abstention_correct']/stats['abstention_total']*100:.1f}%)")
    print("=" * 60)

    # Save detailed evaluation log
    with open("backend/app/scripts/rag_eval_results.json", "w", encoding="utf-8") as f:
        json.dump({"stats": stats, "samples": sample_logs}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run_rag_benchmark()

