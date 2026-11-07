import asyncio
import httpx

async def test_ollama():
    url = "http://127.0.0.1:11434"
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try /api/embed (Ollama >= 0.1.34)
        try:
            resp = await client.post(f"{url}/api/embed", json={"model": "qwen3:8b", "input": "Hello NileOps"})
            if resp.status_code == 200:
                data = resp.json()
                embeddings = data.get("embeddings", [])
                dim = len(embeddings[0]) if embeddings else 0
                print(f"Success /api/embed: dimension={dim}")
                return dim
        except Exception as e:
            print(f"/api/embed error: {e}")

        # Try /api/embeddings (classic)
        try:
            resp = await client.post(f"{url}/api/embeddings", json={"model": "qwen3:8b", "prompt": "Hello NileOps"})
            if resp.status_code == 200:
                data = resp.json()
                embedding = data.get("embedding", [])
                dim = len(embedding)
                print(f"Success /api/embeddings: dimension={dim}")
                return dim
        except Exception as e:
            print(f"/api/embeddings error: {e}")

    print("Ollama test failed")
    return None

if __name__ == "__main__":
    asyncio.run(test_ollama())

