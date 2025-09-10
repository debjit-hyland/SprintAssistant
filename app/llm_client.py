import os, requests
HF_API_TOKEN=os.getenv("HF_API_TOKEN")
MODEL="meta-llama/Meta-Llama-3-8B-Instruct"
def summarize_text_markdown(raw:str)->str:
   if not HF_API_TOKEN: return raw  # fallback
   headers={"Authorization":f"Bearer {HF_API_TOKEN}"}
   resp=requests.post(
       f"https://api-inference.huggingface.co/models/{MODEL}",
       headers=headers,json={"inputs":f"Summarize:\n{raw}"},timeout=60
   )
   resp.raise_for_status(); out=resp.json()
   if isinstance(out,list): return out[0]["generated_text"].strip()
   return out.get("generated_text","").strip()