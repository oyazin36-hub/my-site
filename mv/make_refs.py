# 登場人物と場所の参照画像を作る（カット表「登場人物」「場所」の英語説明から）
import base64, sys
from common import call

STYLE = ("Japanese hand-drawn anime film style, soft painterly backgrounds, warm natural light, "
         "muted colors, gentle film grain. No text, no logos.")
CHAR = ("Character reference sheet: full-body front view and a head-and-shoulders close-up side by side "
        "on a plain light background, of {d}. Fictional person. ")
PLACE = "Establishing wide shot, 16:9, no people: {d}. "

REFS = {
    "c1948":    CHAR.format(d="a Japanese man in his twenties with short black hair, wearing a navy work jacket, 1940s clothing"),
    "veteran":  CHAR.format(d="an elderly Japanese craftsman in his seventies with swept-back grey hair, wearing a navy work jacket"),
    "mid":      CHAR.format(d="a Japanese man in his forties with short dark hair, white shirt with rolled-up sleeves"),
    "designer": CHAR.format(d="a young Japanese woman in her twenties with a brown bob haircut and round glasses, wearing a white shirt"),
    "operator": CHAR.format(d="a young Japanese man in his twenties with short hair, navy work uniform and safety glasses"),
    "old_shop": PLACE.format(d="a small 1940s Japanese machine workshop with wooden beams and old machines, slanted window light, sepia tones"),
    "factory":  PLACE.format(d="a bright, high-ceilinged modern Japanese factory with a large gantry-type five-face machining center, clean floor"),
    "office":   PLACE.format(d="a calm design office by the window with CAD monitors and drawings pinned on the wall"),
    "okazaki":  PLACE.format(d="the city of Okazaki in Aichi seen from a hill, with the Yahagi River flowing through it"),
}

for name, prompt in REFS.items():
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    r = call("POST", "models/gemini-3.1-flash-image:generateContent", {
        "contents": [{"parts": [{"text": prompt + STYLE}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}},
    })
    parts = r["candidates"][0]["content"]["parts"]
    img = next(p["inlineData"] for p in parts if "inlineData" in p)
    ext = "png" if "png" in img["mimeType"] else "jpg"
    open(f"refs/{name}.{ext}", "wb").write(base64.b64decode(img["data"]))
    print("ok", name, img["mimeType"], flush=True)
