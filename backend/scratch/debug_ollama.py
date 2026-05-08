import httpx

base_url = "http://localhost:11434"
try:
    r = httpx.get(f"{base_url}/api/tags")
    print(f"Tags Status: {r.status_code}")
    print(f"Tags Response: {r.text[:200]}")
    
    # Try a dummy generate call
    r = httpx.post(f"{base_url}/api/generate", json={"model": "llama3", "prompt": "hi", "stream": False})
    print(f"Generate Status: {r.status_code}")
    print(f"Generate Response: {r.text[:200]}")
    
    # Try a dummy chat call
    r = httpx.post(f"{base_url}/api/chat", json={"model": "llama3", "messages": [{"role": "user", "content": "hi"}], "stream": False})
    print(f"Chat Status: {r.status_code}")
    print(f"Chat Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
