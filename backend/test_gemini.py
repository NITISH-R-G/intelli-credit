import urllib.request
import json

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": "AIzaSyDeRuR_U2W9EC5aagOvkKBXHNK3cNiZL_M"
}
data = {
    "contents": [{"parts": [{"text": "Explain how AI works in a few words"}]}]
}
req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        print("SUCCESS! Gemini API tested successfully.")
        print("Response:", text.strip())
except Exception as e:
    print(f"Error testing Gemini: {e}")
