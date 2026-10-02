import base64, json, os, time, urllib.request, urllib.error

API = "https://generativelanguage.googleapis.com/v1beta"
KEY = os.environ["GeminiAPIKey"]

def call(method, path, body=None, timeout=600):
    req = urllib.request.Request(
        f"{API}/{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-goog-api-key": KEY, "Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            msg = e.read().decode()
            if e.code in (429, 500, 502, 503) and attempt < 1:
                time.sleep(20 * (attempt + 1)); continue
            raise RuntimeError(f"{e.code}: {msg}")

def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()
