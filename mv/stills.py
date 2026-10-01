# Veo の上限中のつなぎ: 未生成カットを、参照画像から描いた 1 枚絵＋ゆっくりしたカメラの動きで 8 秒の動画にする
# 出力 clips/still/cutNN.mp4（Veo で本物ができたら edit.py はそちらを優先する）
import base64, os, subprocess
from concurrent.futures import ThreadPoolExecutor
from common import call, b64
from cuts import CUTS, TIMELINE
from make_clip import STYLE

os.makedirs("clips/still", exist_ok=True)
MOVES = ["0.0009", "0.0007"]  # ゆっくり寄る

def frame(cut):
    no = cut["no"]
    path = f"frames/cut{no}_first.jpg"
    if os.path.exists(path):
        return path
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64(f"refs/{r}.jpg")}} for r in cut.get("refs", [])]
    lead = ("Using the attached character and location references (keep faces, hair, clothing and places exactly the same), "
            if parts else "")
    parts.append({"text": f"{lead}draw this shot as a single 16:9 film still: {cut['prompt']} {STYLE}"})
    r = call("POST", "models/gemini-3.1-flash-image:generateContent", {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}},
    })
    img = next(p["inlineData"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
    open(path, "wb").write(base64.b64decode(img["data"]))
    return path

def make(cut):
    no = cut["no"]
    out = f"clips/still/cut{no}.mp4"
    if os.path.exists(out):
        return f"skip {no}"
    try:
        img = frame(cut)
        z = MOVES[int(no) % 2]
        # 2 倍に拡大してから zoompan で寄ると、動きがなめらかになる
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", img,
                        "-vf", f"scale=2560:1440,zoompan=z='1+{z}*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=192:s=1280x720:fps=24",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
        return f"ok {no}"
    except Exception as e:
        return f"FAIL {no}: {str(e)[:200]}"

need = {n for n, _, _ in TIMELINE if not os.path.exists(f"clips/cut{n}.mp4")}
todo = [c for c in CUTS if c["no"] in need]
with ThreadPoolExecutor(4) as ex:
    for m in ex.map(make, todo):
        print(m, flush=True)
