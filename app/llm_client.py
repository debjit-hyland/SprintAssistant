import os, requests

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")

OLLAMA_BASE = os.getenv("OLLAMA_BASE")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

SYSTEM = "You are a helpful scrum assistant. Extract decisions, action items (owner, item, due), blockers. Return clean Markdown."

def summarize_text_markdown(raw: str) -> str:
    prompt = f"{SYSTEM}\n\nSummarize the following meeting/chat notes:\n\n{raw}"
    # Prefer Ollama if available (no internet, fully free)
    if OLLAMA_BASE:
        resp = requests.post(f"{OLLAMA_BASE}/v1/chat/completions", json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    # Fallback: Hugging Face Inference (free)
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}
    resp = requests.post(
        f"https://api-inference.huggingface.co/models/{HF_MODEL}",
        headers=headers,
        json={"inputs": prompt, "parameters": {"max_new_tokens": 400, "temperature": 0.2}},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    # Some endpoints return list; others dict → normalize:
    if isinstance(data, list):
        return data[0]["generated_text"].replace(prompt, "").strip()
    return data.get("generated_text", "").strip()
