# カット表の未生成カットを Veo 3.1 Fast でまとめて生成する: python3 make_all.py [カット番号...]
import os, subprocess, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY
from cuts import CUTS
from make_clip import STYLE, NEGATIVE, MODEL

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
    if cut.get("refs"):
        inst["referenceImages"] = [{"image": {"bytesBase64Encoded": b64(f"refs/{r}.jpg"), "mimeType": "image/jpeg"},
                                    "referenceType": "asset"} for r in cut["refs"]]
    params = {"aspectRatio": "16:9", "durationSeconds": 8}
    if not cut.get("refs"):  # 参照画像を使うときは negativePrompt を受け付けない
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

todo = [c for c in CUTS if not c.get("done") and (len(sys.argv) == 1 or c["no"] in sys.argv[1:])]
with ThreadPoolExecutor(4) as ex:
    for msg in ex.map(safe, todo):
        print(msg, flush=True)
