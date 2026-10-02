# カット表の未生成カットを Veo 3.1 Fast でまとめて生成する: python3 make_all.py [カット番号...]
import base64, os, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY
from cuts import CUTS
from make_clip import STYLE, NEGATIVE, MODEL
MODEL = os.environ.get("VEO_MODEL", MODEL)

def generate(cut):
    no = cut["no"]
    out = f"clips/cut{no}.mp4"
    if os.path.exists(out):
        return f"skip {no}"
    inst = {"prompt": f"{cut['prompt']} {STYLE}"}
    if cut.get("frame"):
        prev = f"clips/cut{cut['frame']}.mp4"
        while not os.path.exists(prev):
            time.sleep(15)
        last = f"frames/cut{cut['frame']}_last.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-sseof", "-0.1", "-i", prev, "-frames:v", "1", last], check=True)
        inst["image"] = {"bytesBase64Encoded": b64(last), "mimeType": "image/jpeg"}
    first_frame = f"frames/cut{no}_first.jpg"
    if os.environ.get("FROM_STILLS") and os.path.exists(first_frame):
        # 見ていただいた 1 枚絵（見本の画風）を最初のコマにして動かす。画風と構図が 1 枚絵とそろう
        inst["image"] = {"bytesBase64Encoded": b64(first_frame), "mimeType": "image/jpeg"}
    elif cut.get("refs") and "lite" in MODEL:
        # Lite は参照画像を受け付けないので、参照画像から最初のコマを絵にして、それを動かす
        first = f"frames/cut{no}_first.jpg"
        if not os.path.exists(first):
            parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64(f"refs/{r}.jpg")}} for r in cut["refs"]]
            parts.append({"text": "Using the attached character and location references (keep faces, hair, clothing and "
                          "places exactly the same), draw the first frame of this shot as a single 16:9 film still: "
                          f"{cut['prompt']} {STYLE}"})
            r = call("POST", "models/gemini-3.1-flash-image:generateContent", {
                "contents": [{"parts": parts}],
                "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}},
            })
            img = next(p["inlineData"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
            open(first, "wb").write(base64.b64decode(img["data"]))
        inst["image"] = {"bytesBase64Encoded": b64(first), "mimeType": "image/jpeg"}
    elif cut.get("refs"):
        inst["referenceImages"] = [{"image": {"bytesBase64Encoded": b64(f"refs/{r}.jpg"), "mimeType": "image/jpeg"},
                                    "referenceType": "asset"} for r in cut["refs"]]
    params = {"aspectRatio": "16:9", "durationSeconds": 8}
    if (os.environ.get("FROM_STILLS") or not cut.get("refs")) and "lite" not in MODEL:  # 参照画像を使うときと Lite は negativePrompt を受け付けない
        params["negativePrompt"] = NEGATIVE
    op = call("POST", f"models/{MODEL}:predictLongRunning", {"instances": [inst], "parameters": params})
    while not op.get("done"):
        time.sleep(15)
        op = call("GET", op["name"])
    if "error" in op:
        return f"FAIL {no}: {op['error']}"
    samples = op["response"]["generateVideoResponse"].get("generatedSamples")
    if not samples:
        return f"FAIL {no}: {op['response']}"
    req = urllib.request.Request(samples[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
    with urllib.request.urlopen(req) as r, open(out + ".part", "wb") as f:
        f.write(r.read())
    os.rename(out + ".part", out)
    return f"ok {no}"

def safe(cut):
    try:
        return generate(cut)
    except Exception as e:
        return f"FAIL {cut['no']}: {str(e)[:300]}"

from cuts import TIMELINE
used = {n for n, _, _ in TIMELINE}
if os.environ.get("FROM_STILLS"):  # 見本の画風で作り直すときは、曲で使う全カットが対象（作成済みの 06 も含む）
    todo = [c for c in CUTS if c["no"] in used and (len(sys.argv) == 1 or c["no"] in sys.argv[1:])]
else:
    todo = [c for c in CUTS if not c.get("done") and (len(sys.argv) == 1 or c["no"] in sys.argv[1:])]
with ThreadPoolExecutor(4) as ex:
    for msg in ex.map(safe, todo):
        print(msg, flush=True)
