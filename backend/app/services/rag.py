"""NileOps Production RAG Service.

Combines Qdrant semantic retrieval with grounded response generation,
multilingual Arabic/English support, strict thresholding/abstention,
and verifiable policy citations.
"""

from typing import Any, Dict, List, Optional
import time
import httpx

from app.core.config import settings
from app.services.lexical_support import compute_lexical_containment
from app.services.query_normalizer import normalize_colloquial_query
from app.services.vector_store import qdrant_service

def map_similarity_threshold(threshold: Optional[float] = None) -> float:
    backend = getattr(settings, "EMBEDDING_BACKEND", "e5").lower()
    if threshold is None:
        return settings.RAG_SIMILARITY_THRESHOLD if backend == "e5" else 0.15
    if backend == "e5" and threshold < 0.5:
        # Rescale legacy hash threshold (0.0 - 0.30) to E5 cosine threshold range (0.70 - 0.85)
        return 0.70 + threshold * 0.5
    return threshold


def get_default_similarity_threshold() -> float:
    return map_similarity_threshold(None)

DEFAULT_SIMILARITY_THRESHOLD = settings.RAG_SIMILARITY_THRESHOLD

ABSTENTION_MESSAGES = {
    "ar": "لم يتم العثور على سياسة مطابقة. يرجى محاولة إعادة صياغة سؤالك.",
    "en": "No matching policy found. Try rephrasing your question.",
}


class RAGService:
    def __init__(self, ollama_url: str = settings.OLLAMA_URL, model: str = settings.OLLAMA_MODEL):
        self.ollama_url = ollama_url
        self.model = model
        self._ollama_available: Optional[bool] = None
        self._last_ollama_check: float = 0.0

    async def _query_llm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """Query local Ollama LLM with fallback on timeout and circuit-breaker."""
        now = time.time()
        if self._ollama_available is False and (now - self._last_ollama_check) < 60.0:
            return None

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(connect=0.2, read=2.0, write=1.0, pool=1.0)) as client:
                res = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                    },
                )
                if res.status_code == 200:
                    self._ollama_available = True
                    self._last_ollama_check = now
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return response_text
                else:
                    self._ollama_available = False
                    self._last_ollama_check = now
        except Exception:
            self._ollama_available = False
            self._last_ollama_check = now
        return None

    def _synthesize_fallback_answer(self, chunks: List[Dict[str, Any]], language: str) -> str:
        """Deterministically synthesize answer directly from retrieved policy chunks."""
        if not chunks:
            return ABSTENTION_MESSAGES.get(language, ABSTENTION_MESSAGES["en"])

        top_chunk = chunks[0]
        title = top_chunk.get("title_ar") if language == "ar" else top_chunk.get("title_en")
        code = top_chunk.get("code")
        content = top_chunk.get("content", "").strip()

        if language == "ar":
            return (
                f"بناءً على السياسة البنكية المعتمدة ({title} - رمز {code}):\n\n"
                f"{content}\n\n"
                f"يرجى الالتزام بالتعليمات المذكورة أعلاه ومراجعة الفرع في حال الحاجة لأي مستندات إضافية."
            )
        else:
            return (
                f"Based on the approved banking policy ({title} - Code {code}):\n\n"
                f"{content}\n\n"
                f"Please comply with the instructions above and consult a representative if additional assistance is needed."
            )

    async def retrieve_and_generate(
        self,
        query: str,
        portal_type: str = "customer",
        language: str = "ar",
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute end-to-end RAG with multi-signal gating, thresholding, portal isolation, and citations."""
        # 1. Colloquial query normalization & semantic candidate retrieval from Qdrant
        normalized_query = normalize_colloquial_query(query)
        hits = await qdrant_service.search(
            query=normalized_query,
            portal_type=portal_type,
            limit=10,
            score_threshold=0.0,
        )

        # 2. Check for empty retrieval
        if not hits:
            return {
                "query": query,
                "portal_type": portal_type,
                "language": language,
                "answer": ABSTENTION_MESSAGES.get(language, ABSTENTION_MESSAGES["en"]),
                "confidence_score": 0.0,
                "abstained": True,
                "fallback_used": False,
                "citations": [],
            }

        top_score = hits[0]["score"]
        top2_score = hits[1]["score"] if len(hits) > 1 else 0.0
        margin1_2 = top_score - top2_score
        scores = [h["score"] for h in hits]
        mean_score = sum(scores) / len(scores) if scores else 0.0
        margin1_mean10 = top_score - mean_score

        # Compute lexical containment against top candidate policy content
        top1_code = hits[0].get("code")
        top_doc_content = " ".join([h.get("content", "") for h in hits if h.get("code") == top1_code])
        lex_support = compute_lexical_containment(query, top_doc_content)

        # Multi-signal abstention gating
        # Calibrated via 5-fold CV on DEV pool: answer if high confidence with clear margin OR modest confidence with strong lexical containment
        t_high = getattr(settings, "RAG_ABSTENTION_T_HIGH", 0.80)
        m12_min = getattr(settings, "RAG_ABSTENTION_M12_MIN", 0.010)
        m10_min = getattr(settings, "RAG_ABSTENTION_M10_MIN", 0.015)
        t_low = getattr(settings, "RAG_ABSTENTION_T_LOW", 0.76)
        l_min = getattr(settings, "RAG_ABSTENTION_L_MIN", 0.06)

        is_supported = (top_score >= t_high and margin1_2 >= m12_min and margin1_mean10 >= m10_min) or (
            top_score >= t_low and lex_support >= l_min
        )

        # If caller passed explicit custom threshold, enforce it in addition
        if threshold is not None:
            effective_threshold = map_similarity_threshold(threshold)
            if top_score < effective_threshold:
                is_supported = False

        if not is_supported:
            return {
                "query": query,
                "portal_type": portal_type,
                "language": language,
                "answer": ABSTENTION_MESSAGES.get(language, ABSTENTION_MESSAGES["en"]),
                "confidence_score": 0.0,
                "abstained": True,
                "fallback_used": False,
                "citations": [],
            }

        # 3. Construct structured citations from top candidate hits
        selected_hits = hits[:3]
        seen_codes = set()
        citations = []
        context_snippets = []

        for h in selected_hits:
            code = h["code"]
            if code not in seen_codes:
                seen_codes.add(code)
                citations.append(
                    {
                        "code": code,
                        "title": h["title"],
                        "domain": h["domain"],
                        "version": h["version"],
                        "portal_access": h["portal_access"],
                        "score": h["score"],
                        "passage": h.get("content", ""),
                    }
                )
            context_snippets.append(f"[{code}] {h['title']}:\n{h['content']}")

        combined_context = "\n\n---\n\n".join(context_snippets)

        # 4. Prompt Construction
        if language == "ar":
            system_prompt = (
                "أنت المساعد الذكي لبنك النيل (NileOps). أجب بدقة واحترافية باللغة العربية بناءً فقط على السياسات البنكية المعتمدة التالية. "
                "لا تخترع أي معلومات من خارج السياق. اذكر رمز السياسة دائماً."
            )
            prompt = f"السياسات البنكية المعتمدة:\n{combined_context}\n\nالسؤال: {query}\n\nالإجابة:"
        else:
            system_prompt = (
                "You are the NileOps AI Banking Assistant. Answer professionally and accurately based ONLY on the following approved banking policies. "
                "Do not invent information outside the context. Always cite the policy code."
            )
            prompt = f"Approved Banking Policies:\n{combined_context}\n\nQuestion: {query}\n\nAnswer:"

        # 5. LLM Query with Fallback
        fallback_used = False
        llm_answer = await self._query_llm(prompt, system_prompt)
        if not llm_answer:
            llm_answer = self._synthesize_fallback_answer(selected_hits, language)
            fallback_used = True

        return {
            "query": query,
            "portal_type": portal_type,
            "language": language,
            "answer": llm_answer,
            "confidence_score": top_score,
            "abstained": False,
            "fallback_used": fallback_used,
            "citations": citations,
        }


rag_service = RAGService()
