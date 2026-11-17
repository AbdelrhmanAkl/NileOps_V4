import os
import json

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "rag_eval"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

PARAPHRASE_QUESTIONS_20 = [
    # --- 15 In-Domain Paraphrased Questions (Arabic Egyptian Colloquial + English) ---
    {
        "id": "P01",
        "language": "ar",
        "portal": "customer",
        "question": "عايز افتح حساب عادي بالمصري بس مش عارف محتاج فلوس كام في الاول؟",
        "category": "paraphrase_current_min",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P02",
        "language": "ar",
        "portal": "customer",
        "question": "لو الفلوس اللي في حسابي قلت عن الرصيد المطلوب البنك بيخصم كام كل شهر مصاريف؟",
        "category": "paraphrase_fee",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P03",
        "language": "ar",
        "portal": "customer",
        "question": "لو عاوز اعمل حساب توفير يديني عائد شهري محترم، احط فيه كام كبداية؟",
        "category": "paraphrase_savings_min",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P04",
        "language": "ar",
        "portal": "customer",
        "question": "ممكن افتح حساب جاري بالجنيه ولا لازم عملة صعبة؟",
        "category": "paraphrase_currency",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P05",
        "language": "ar",
        "portal": "employee",
        "question": "هو الموظف في الفرع بيعرف منين المحافظة اللي اتولد فيها العميل من أرقام البطاقة؟",
        "category": "paraphrase_kyc_gov",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P06",
        "language": "ar",
        "portal": "employee",
        "question": "يعني ايه اول رقم في البطاقة ده اتنين ولا تلاتة؟ بيحدد ايه بالضبط في فحص الهوية؟",
        "category": "paraphrase_kyc_century",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P07",
        "language": "ar",
        "portal": "employee",
        "question": "هو في خانات في الرقم القومي بتعرف الموظف سنة وشهر ويوم ميلاد صاحب البطاقة؟",
        "category": "paraphrase_kyc_bdate",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P08",
        "language": "ar",
        "portal": "employee",
        "question": "ايه المطلوب للتاكد من عدم استخدام بطاقات حقيقية في تجارب واختبارات فحص الجودة؟",
        "category": "paraphrase_kyc_qa",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P09",
        "language": "en",
        "portal": "customer",
        "question": "How much cash do I need to put down up front to get a standard personal checking account running?",
        "category": "paraphrase_current_min",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P10",
        "language": "en",
        "portal": "customer",
        "question": "What penalty does the bank charge to my balance every month if I dip below the required minimum deposit?",
        "category": "paraphrase_fee",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P11",
        "language": "en",
        "portal": "customer",
        "question": "What is the initial deposit requirement for the top-tier monthly interest savings option?",
        "category": "paraphrase_savings_min",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P12",
        "language": "en",
        "portal": "customer",
        "question": "Can personal deposit accounts be denominated in local currency?",
        "category": "paraphrase_currency",
        "expected_policy": "POL-RETAIL-001",
        "should_abstain": False,
    },
    {
        "id": "P13",
        "language": "en",
        "portal": "employee",
        "question": "Which digits on an Egyptian identity card tell the branch teller where the person was born?",
        "category": "paraphrase_kyc_gov",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P14",
        "language": "en",
        "portal": "employee",
        "question": "How does the system distinguish people born in the 1900s from people born in the 2000s on their civil ID?",
        "category": "paraphrase_kyc_century",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },
    {
        "id": "P15",
        "language": "en",
        "portal": "employee",
        "question": "Where on the 14-digit Egyptian card sequence can staff identify the birth date information?",
        "category": "paraphrase_kyc_bdate",
        "expected_policy": "POL-KYC-001",
        "should_abstain": False,
    },

    # --- 5 Out-of-Domain Questions (Colloquial Arabic + English) ---
    {
        "id": "P16",
        "language": "ar",
        "portal": "customer",
        "question": "ازاي اعمل ملوخية بالفراخ على الطريقة المصرية المظبوطة؟",
        "category": "out_of_domain",
        "expected_policy": None,
        "should_abstain": True,
    },
    {
        "id": "P17",
        "language": "ar",
        "portal": "customer",
        "question": "عايز اعرف احسن ورشة لتصليح عفشة العربيات في شارع فيصل",
        "category": "out_of_domain",
        "expected_policy": None,
        "should_abstain": True,
    },
    {
        "id": "P18",
        "language": "ar",
        "portal": "employee",
        "question": "سعر الدولار كام في السوق الموازي النهاردة في القاهرة؟",
        "category": "out_of_domain",
        "expected_policy": None,
        "should_abstain": True,
    },
    {
        "id": "P19",
        "language": "en",
        "portal": "customer",
        "question": "What are the standard rules for playing squash in Egyptian sporting clubs?",
        "category": "out_of_domain",
        "expected_policy": None,
        "should_abstain": True,
    },
    {
        "id": "P20",
        "language": "en",
        "portal": "employee",
        "question": "How do I fix a leaking water pipe under my kitchen sink with teflon tape?",
        "category": "out_of_domain",
        "expected_policy": None,
        "should_abstain": True,
    },
]

def main():
    filepath = os.path.join(OUTPUT_DIR, "rag_paraphrase_set_20.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(PARAPHRASE_QUESTIONS_20, f, ensure_ascii=False, indent=2)
    print(f"Generated {len(PARAPHRASE_QUESTIONS_20)} paraphrased RAG evaluation questions at {filepath}")

if __name__ == "__main__":
    main()

