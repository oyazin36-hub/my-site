# 完成版の 6 場面を、直した最初のコマ（frames/fix/cutNN.jpg）から動画にし直す。構図は完成版のまま
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY

STYLE = ("Japanese hand-drawn anime film style, soft painterly backgrounds, warm natural light, muted colors, gentle film grain, cinematic 16:9. "
         "Keep the art style, colors, faces and composition of the first frame. No on-screen text, no logos, no sparks.")
MOTION = {
 "40": "Still-life: a slow gentle push-in on the two calipers on the wooden workbench, warm evening light, floating dust. The calipers and the blank display never show any letters or numbers.",
 "35": "The employees standing in front of the factory smile; the camera slowly pulls back and rises a little. No standing signboards appear anywhere; the company sign on the building stays exactly as it is.",
 "38": "The employees look up toward the bright light with determined smiles, a gentle breeze, the camera slowly pushes in. Every person keeps exactly the same face and gender as in the first frame.",
 "43": "The two men pull the light-grey cover cloth fully off the machine; the cloth slides off and drops to the floor, revealing the machine, and they smile proudly.",
 "10": "The large roll-up shutter at the far end slowly rises and golden morning light floods across the floor; the camera slowly pushes forward. Everyone keeps the navy blue uniform; no large objects float in the air.",
 "34": "The overhead crane slowly lifts the huge steel plate a little higher; the two men standing to the left guide it with long ropes from a safe distance, watching it. Nobody goes under the load.",
}
MODELS = ["veo-3.1-generate-preview", "veo-3.1-fast-generate-preview", "veo-3.1-lite-generate-preview"]

def make(no):
    out = f"clips/cut{no}.mp4"
    for model in MODELS:
        try:
            op = call("POST", f"models/{model}:predictLongRunning", {
                "instances": [{"prompt": MOTION[no] + " " + STYLE,
                               "image": {"bytesBase64Encoded": b64(f"frames/fix/cut{no}.jpg"), "mimeType": "image/jpeg"}}],
                "parameters": {"aspectRatio": "16:9", "durationSeconds": 8}})
            while not op.get("done"):
                time.sleep(15); op = call("GET", op["name"])
            s = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples")
            if not s:
                continue
            req = urllib.request.Request(s[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
            with urllib.request.urlopen(req) as r, open(out, "wb") as f:
                f.write(r.read())
            return f"ok {no} {model}"
        except Exception as e:
            last = str(e)[:60]
    return f"FAIL {no} {last}"

if __name__ == "__main__":
    nos = sys.argv[1:] or list(MOTION)
    os.makedirs("clips/before_fix", exist_ok=True)
    for n in nos:
        if os.path.exists(f"clips/cut{n}.mp4") and not os.path.exists(f"clips/before_fix/cut{n}.mp4"):
            os.rename(f"clips/cut{n}.mp4", f"clips/before_fix/cut{n}.mp4")
    with ThreadPoolExecutor(3) as ex:
        for m in ex.map(make, nos):
            print(m, flush=True)
