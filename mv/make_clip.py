# カット表の 1 カットを Veo 3.1 で生成する: python3 make_clip.py 06
import sys, time, urllib.request
from common import call, KEY

STYLE = ("Japanese hand-drawn anime film style, soft painterly backgrounds, warm natural light, "
         "muted colors, gentle film grain, cinematic 16:9. No on-screen text, no logos, no sparks.")
NEGATIVE = "flying metal chips, piles of shavings, debris scattering, stone, concrete, rock, cracks, cracked surface, sparks, flying sparks, sparkles, embers, fire, text, letters, logos, watermark, photorealistic"
MODEL = "veo-3.1-fast-generate-preview"

CUTS = {
    "06": "Low-angle wide shot. A large gantry-type machining center smoothly and quietly mills a huge solid block of "
          "smooth, polished silver steel with clean flat faces; the freshly machined metal surface gleams like a mirror. "
          "Clean, calm cutting with only a few tiny metal shavings falling gently near the tool.",
}

no = sys.argv[1]
op = call("POST", f"models/{MODEL}:predictLongRunning", {
    "instances": [{"prompt": f"{CUTS[no]} {STYLE}"}],
    "parameters": {"aspectRatio": "16:9", "durationSeconds": 8, "negativePrompt": NEGATIVE},
})
print("started", op["name"], flush=True)
while not op.get("done"):
    time.sleep(15)
    op = call("GET", op["name"])
if "error" in op:
    sys.exit(f"error: {op['error']}")
resp = op["response"]["generateVideoResponse"]
if not resp.get("generatedSamples"):
    sys.exit(f"no video: {resp}")
uri = resp["generatedSamples"][0]["video"]["uri"]
req = urllib.request.Request(uri, headers={"x-goog-api-key": KEY})
with urllib.request.urlopen(req) as r, open(f"clips/cut{no}.mp4", "wb") as f:
    f.write(r.read())
print("saved", f"clips/cut{no}.mp4", flush=True)
