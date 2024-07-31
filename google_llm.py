import requests

class GoogleLLM:
    def __init__(self, api_key):
        self.api_key = api_key
        self.api_url = "https://api.genai.dev/v1/models/YOUR_MODEL_ID:predict"  # Update with the actual endpoint

    def generate_text(self, prompt, max_tokens=512, temperature=0.7):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        response = requests.post(self.api_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["choices"][0]["text"]
