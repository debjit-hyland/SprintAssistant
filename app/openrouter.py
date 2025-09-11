from typing import Optional
import requests
import json
from typing import Optional
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def ai_response(command: str, data: str) -> Optional[dict]:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "meta-llama/llama-4-maverick:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": command
                        },
                        {
                            "type": "text",
                            "text": data
                        }
                    ]
                }
            ],
        })
    )
    return response.json() if response.status_code == 200 else None