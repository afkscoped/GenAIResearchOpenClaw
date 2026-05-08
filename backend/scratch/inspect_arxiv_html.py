import httpx

url = 'https://arxiv.org/search/?query=diffusion+models&searchtype=all&source=header'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
try:
    r = httpx.get(url, headers=headers, timeout=20.0)
    text = r.text
    start = text.find('<li class="arxiv-result">')
    if start != -1:
        print(text[start:start+5000])
    else:
        print("Not found")
        print(text[:1000])
except Exception as e:
    print(f"Error: {e}")
