import httpx
import sys

query = "diffusion models"
url = f"https://arxiv.org/search/?query={query}&searchtype=all&source=header"
try:
    response = httpx.get(url, timeout=10.0)
    print(f"Status: {response.status_code}")
    print(f"Content-type: {response.headers.get('content-type')}")
    print(f"Sample content: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
