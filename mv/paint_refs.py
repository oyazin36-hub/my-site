# 人物の参照画像を、人物が出ない場面と同じ絵画調（refs/style_paint_in.jpg）で描き直す → refs/paint/
import base64, sys
from concurrent.futures import ThreadPoolExecutor
from common import call, b64
from staff import STAFF

PAINT = ("Cinematic Japanese anime film art in the exact look of image 1: richly painted, finely detailed rendering with soft cinematic lighting, "
         "warm sunlight and gentle haze, smooth painterly shading and subtle gradients, realistic proportions, thin soft line art "
         "(no thick black outlines, no flat manga coloring), film-like color grading.")
SHEET = ("Draw a character reference sheet of the person below in that exact art style: full-body front view and a head-and-shoulders close-up "
         "side by side, standing in a softly lit factory-hall background like image 1. 16:9. No text. Character: ")
JOBS = {k: en for k, (_, en) in STAFF.items()}
JOBS["c1948"] = "a Japanese man in his twenties with short black hair, wearing a navy work jacket, 1940s clothing"

def go(k):
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64("refs/style_paint_in.jpg")}},
             {"inlineData": {"mimeType": "image/jpeg", "data": b64(f"refs/illust/{k}.jpg")}},
             {"text": "Image 1 shows the ART STYLE to copy. Image 2 shows WHO the person is (keep the same face, age, hair style and color, glasses, beard, body type and navy uniform) "
                      "but do NOT copy image 2's drawing style. " + PAINT + " " + SHEET + JOBS[k]}]
    for _ in range(2):
        try:
            r = call("POST", "models/gemini-3.1-flash-image:generateContent", {"contents": [{"parts": parts}],
                     "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}})
            img = next(p["inlineData"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
            open(f"refs/paint/{k}.jpg", "wb").write(base64.b64decode(img["data"]))
            return "ok " + k
        except Exception as e:
            err = str(e)[:80]
    return "FAIL " + k + " " + err

if __name__ == "__main__":
    keys = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(5) as ex:
        print(" ".join(ex.map(go, keys)))
