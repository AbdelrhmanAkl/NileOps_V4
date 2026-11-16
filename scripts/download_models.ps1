# NileOps — Model Pre-caching & Offline Preparation Script
# Downloads intfloat/multilingual-e5-small into the local HuggingFace cache for offline execution.

$env:HF_HUB_ENABLE_HF_TRANSFER = "0"
Write-Host "--- Pre-caching intfloat/multilingual-e5-small for Offline Execution ---"

backend\.venv\Scripts\python.exe -c @"
import sys, re, os
sys.modules['regex'] = re
from sentence_transformers import SentenceTransformer

model_name = 'intfloat/multilingual-e5-small'
print(f'Downloading / verifying {model_name} in HuggingFace cache...')
model = SentenceTransformer(model_name)
v = model.encode('query: اختبار التنزيل والترميز', normalize_embeddings=True)
print(f'Model cached successfully. Embedding dimension: {len(v)}')
"@

Write-Host "Offline verification complete. Set HF_HUB_OFFLINE=1 for strict air-gapped runtime."
