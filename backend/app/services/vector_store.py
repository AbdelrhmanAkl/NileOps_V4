"""NileOps Qdrant Vector Store Integration Service.

Manages vector collection lifecycle, dynamic dimension configuration,
chunk ingestion with 4-eyes governance validation, portal filtering,
and PostgreSQL-Qdrant consistency reconciliation.
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.policy import PolicyDocument
from app.services.embedding import embedding_service

COLLECTION_NAME = "nileops_kb"


class QdrantVectorService:
    def __init__(self, host_url: str = settings.QDRANT_URL):
        self.url = host_url
        self.client = QdrantClient(url=self.url, check_compatibility=False)
        self.collection_name = COLLECTION_NAME
        self.initialized = False

    async def init_collection(self) -> bool:
        """Dynamically discover embedding dimension and create collection if missing."""
        try:
            dim = await embedding_service.probe_dimension()

            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=dim,
                        distance=models.Distance.COSINE,
                    ),
                )
                # Create payload indexes for high-speed filtered retrieval
                for field in ["portal_access", "is_active", "code", "domain", "language"]:
                    self.client.create_payload_index(
                        collection_name=self.collection_name,
                        field_name=field,
                        field_schema=models.PayloadSchemaType.KEYWORD,
                    )

            self.initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize Qdrant collection: {e}")
            return False

    def check_health(self) -> Dict[str, Any]:
        """Perform health check on Qdrant service."""
        try:
            collections = self.client.get_collections().collections
            info = None
            if any(c.name == self.collection_name for c in collections):
                info = self.client.get_collection(self.collection_name)
            return {
                "status": "healthy",
                "connected": True,
                "url": self.url,
                "collection": self.collection_name,
                "points_count": info.points_count if info else 0,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
            }

    def _determine_portal_access(self, doc: PolicyDocument) -> str:
        """Classify policy accessibility: customer (public) vs employee (restricted)."""
        domain_upper = (doc.domain or "").upper()
        if domain_upper in ("RETAIL_BANKING", "DIGITAL_CHANNELS", "CUSTOMER_SERVICE", "CARDS"):
            return "customer"
        return "employee"

    def _chunk_text(self, text: str, max_chars: int = 500, overlap: int = 50) -> List[str]:
        """Split document text into structured overlapping chunks."""
        if not text:
            return []
        # Split by paragraphs or sentences
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        chunks = []
        current_chunk = ""

        for p in paragraphs:
            if len(current_chunk) + len(p) <= max_chars:
                current_chunk += ("\n" + p if current_chunk else p)
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = p

        if current_chunk:
            chunks.append(current_chunk)

        # Fallback if text has no newlines and is long
        if not chunks and len(text) > 0:
            step = max_chars - overlap
            for i in range(0, len(text), step):
                chunks.append(text[i : i + max_chars])

        return chunks

    async def index_document(self, doc: PolicyDocument) -> Tuple[bool, str]:
        """Ingest policy document chunks into Qdrant enforcing strict 4-eyes approval."""
        if not self.initialized:
            await self.init_collection()

        # Strict 4-Eyes Governance Rule:
        # Document must be APPROVED or INDEXED, have a designated approver, and approver != creator
        if doc.status not in ("APPROVED", "INDEXED"):
            return False, f"Document {doc.code} rejected from vector index: status is {doc.status}"

        if not doc.approved_by_id:
            return False, f"Document {doc.code} rejected: missing approved_by_id"

        if doc.approved_by_id == doc.created_by_id:
            return False, f"Document {doc.code} rejected: creator cannot approve own document (separation of duties violation)"

        # Delete any existing chunks for this document to ensure clean idempotency
        await self.delete_document_chunks(str(doc.id))

        portal_access = self._determine_portal_access(doc)
        points: List[models.PointStruct] = []

        # Process English content
        en_chunks = self._chunk_text(doc.content_en)
        for idx, chunk in enumerate(en_chunks):
            embedding = await embedding_service.get_embedding(chunk)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.id}_en_{idx}"))
            payload = {
                "document_id": str(doc.id),
                "code": doc.code,
                "title_en": doc.title_en,
                "title_ar": doc.title_ar,
                "domain": doc.domain,
                "language": "en",
                "chunk_index": idx,
                "version": doc.version,
                "portal_access": portal_access,
                "is_active": True,
                "status": doc.status,
                "approved_by_id": str(doc.approved_by_id),
                "content": chunk,
            }
            points.append(models.PointStruct(id=point_id, vector=embedding, payload=payload))

        # Process Arabic content
        ar_chunks = self._chunk_text(doc.content_ar)
        for idx, chunk in enumerate(ar_chunks):
            embedding = await embedding_service.get_embedding(chunk)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc.id}_ar_{idx}"))
            payload = {
                "document_id": str(doc.id),
                "code": doc.code,
                "title_en": doc.title_en,
                "title_ar": doc.title_ar,
                "domain": doc.domain,
                "language": "ar",
                "chunk_index": idx,
                "version": doc.version,
                "portal_access": portal_access,
                "is_active": True,
                "status": doc.status,
                "approved_by_id": str(doc.approved_by_id),
                "content": chunk,
            }
            points.append(models.PointStruct(id=point_id, vector=embedding, payload=payload))

        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)

        return True, f"Indexed {len(points)} chunks for {doc.code}"

    async def delete_document_chunks(self, document_id: str) -> None:
        """Purge all chunks associated with a document ID."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    async def search(
        self,
        query: str,
        portal_type: str = "customer",
        limit: int = 4,
        score_threshold: float = 0.15,
    ) -> List[Dict[str, Any]]:
        """Perform semantic retrieval with strict portal isolation and threshold enforcement."""
        if not self.initialized:
            await self.init_collection()

        query_vector = await embedding_service.get_embedding(query)

        filter_conditions: List[models.Condition] = [
            models.FieldCondition(key="is_active", match=models.MatchValue(value=True))
        ]

        # Strict Portal Isolation:
        # Customer portal CANNOT view internal employee documents
        if portal_type == "customer":
            filter_conditions.append(
                models.FieldCondition(key="portal_access", match=models.MatchValue(value="customer"))
            )

        query_filter = models.Filter(must=filter_conditions)

        res = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        results = []
        for hit in res.points:
            payload = hit.payload or {}
            results.append(
                {
                    "score": round(float(hit.score), 4),
                    "document_id": payload.get("document_id"),
                    "code": payload.get("code"),
                    "title": payload.get("title_ar") if payload.get("language") == "ar" else payload.get("title_en"),
                    "title_en": payload.get("title_en"),
                    "title_ar": payload.get("title_ar"),
                    "domain": payload.get("domain"),
                    "version": payload.get("version"),
                    "portal_access": payload.get("portal_access"),
                    "language": payload.get("language"),
                    "content": payload.get("content"),
                }
            )

        return results

    async def reconcile_with_postgres(self, session: AsyncSession) -> Dict[str, Any]:
        """Synchronize Qdrant vector index with authoritative PostgreSQL policy records."""
        if not self.initialized:
            await self.init_collection()

        result = await session.execute(select(PolicyDocument))
        policies = result.scalars().all()

        indexed_count = 0
        skipped_count = 0
        errors = []

        for p in policies:
            if p.status in ("APPROVED", "INDEXED") and p.approved_by_id and p.approved_by_id != p.created_by_id:
                success, msg = await self.index_document(p)
                if success:
                    indexed_count += 1
                else:
                    errors.append(msg)
            else:
                # Remove unapproved or rejected documents from index
                await self.delete_document_chunks(str(p.id))
                skipped_count += 1

        stats = self.check_health()
        return {
            "total_policies_scanned": len(policies),
            "indexed_policies": indexed_count,
            "skipped_or_purged": skipped_count,
            "total_qdrant_points": stats.get("points_count", 0),
            "errors": errors,
        }


qdrant_service = QdrantVectorService()
