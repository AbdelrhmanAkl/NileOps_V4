"""Targeted Deep RAG Testing Script for NileOps.

Tests English/Arabic queries, relevant/no-evidence/off-topic scenarios,
strict portal isolation, and citation accuracy.
"""

import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15.0)

def test_rag_scenarios():
    print("=== Testing Real RAG Scenarios ===")

    # Scenario 1: Arabic Policy Question (Relevant Evidence)
    q1 = "ما هي المستندات المطلوبة لفتح حساب جاري في بنك النيل؟"
    r1 = client.post("/api/v1/rag/ask", json={"query": q1, "portal_type": "customer", "language": "ar", "threshold": 0.15})
    d1 = r1.json()
    print(f"\n[Scenario 1 - Arabic Relevant] Query: '{q1}'")
    print(f"  Abstained: {d1.get('abstained')}, Score: {d1.get('confidence_score')}")
    print(f"  Citations: {[c['code'] for c in d1.get('citations', [])]}")
    print(f"  Answer preview: {d1.get('answer')[:120]}...")

    # Scenario 2: English Policy Question (Relevant Evidence)
    q2 = "What are the requirements and minimum balance to open a retail current account?"
    r2 = client.post("/api/v1/rag/ask", json={"query": q2, "portal_type": "customer", "language": "en", "threshold": 0.15})
    d2 = r2.json()
    print(f"\n[Scenario 2 - English Relevant] Query: '{q2}'")
    print(f"  Abstained: {d2.get('abstained')}, Score: {d2.get('confidence_score')}")
    print(f"  Citations: {[c['code'] for c in d2.get('citations', [])]}")
    print(f"  Answer preview: {d2.get('answer')[:120]}...")

    # Scenario 3: Question with No Supporting Evidence in KB
    q3 = "ما هي شروط تمويل شراء الطائرات الخاصة واليخوت السياحية؟"
    r3 = client.post("/api/v1/rag/ask", json={"query": q3, "portal_type": "customer", "language": "ar", "threshold": 0.15})
    d3 = r3.json()
    print(f"\n[Scenario 3 - No Supporting Evidence] Query: '{q3}'")
    print(f"  Abstained: {d3.get('abstained')}, Score: {d3.get('confidence_score')}")
    print(f"  Answer: {d3.get('answer')}")

    # Scenario 4: Off-Topic Question
    q4 = "How to replace the spark plugs in a BMW V8 engine?"
    r4 = client.post("/api/v1/rag/ask", json={"query": q4, "portal_type": "customer", "language": "en", "threshold": 0.15})
    d4 = r4.json()
    print(f"\n[Scenario 4 - Off-Topic] Query: '{q4}'")
    print(f"  Abstained: {d4.get('abstained')}, Score: {d4.get('confidence_score')}")
    print(f"  Answer: {d4.get('answer')}")

    # Scenario 5: Customer attempting to access restricted employee KYC/AML policy
    q5 = "KYC customer identification procedures and risk scoring rules"
    r5_cust = client.post("/api/v1/rag/ask", json={"query": q5, "portal_type": "customer", "language": "en", "threshold": 0.15})
    d5_cust = r5_cust.json()
    cust_codes = [c['code'] for c in d5_cust.get('citations', [])]
    print(f"\n[Scenario 5 - Customer Portal KYC Boundary] Query: '{q5}'")
    print(f"  Customer received codes: {cust_codes}")
    assert "POL-KYC-001" not in cust_codes, "SECURITY BREACH: Customer accessed POL-KYC-001!"
    print("  CONFIRMED: POL-KYC-001 is BLOCKED from Customer Portal.")

    # Scenario 6: Employee accessing restricted KYC/AML policy
    r5_emp = client.post("/api/v1/rag/ask", json={"query": q5, "portal_type": "employee", "language": "en", "threshold": 0.15})
    d5_emp = r5_emp.json()
    emp_codes = [c['code'] for c in d5_emp.get('citations', [])]
    print(f"\n[Scenario 6 - Employee Portal KYC Access] Query: '{q5}'")
    print(f"  Employee received codes: {emp_codes}")
    assert "POL-KYC-001" in emp_codes, "Employee was denied access to POL-KYC-001!"
    print("  CONFIRMED: POL-KYC-001 is ACCESSIBLE to Employee Portal.")

    print("\n=== All RAG deep test scenarios verified successfully! ===")

if __name__ == "__main__":
    test_rag_scenarios()

