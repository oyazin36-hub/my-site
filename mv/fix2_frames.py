# カットシーン集で受けた指示（10/3）の画像を描く。動画にする前に見てもらうための 1 枚目
import base64, os, sys
from concurrent.futures import ThreadPoolExecutor
from common import call, b64

D = "frames/fix2"
KEEP = ("Keep EVERYTHING else exactly the same as the input image: the same composition, camera angle, framing, "
        "background, machines, colors, lighting, art style, and every other person with the same face, hair, gender, "
        "pose and position. Do not add or remove anyone. No text, letters, numbers or logos anywhere.")
STYLE = ("Draw it in exactly the same Japanese hand-drawn anime film style, painterly backgrounds, warm natural light and "
         "colors as the first image. Everyone wears the same navy blue work uniform as in the first image. "
         "One single continuous shot, no panels. No text, letters, numbers or logos anywhere.")

# (出力, 元画像, 参照画像, 指示)。元画像があれば部分修正、無ければ新しい場面
JOBS = {
    "c02": ("base_c02", [], "Edit this image. Replace ONLY the craftsman: he becomes a man in his 70s with white hair, "
            "a slightly stern, strong-featured face with a few wrinkles, the same pose, the same clothes and the same hands "
            "on the lathe. Keep the sepia tone. " + KEEP),
    "c03": ("base_c03", [], "Edit this image. Make ONLY the woman look younger and more youthful: a woman around 60 "
            "with smoother skin, fewer wrinkles, a bright gentle face, same dark brown bob hair, same navy uniform, same pose. " + KEEP),
    "c09": ("base_c09", [], "Edit this image. Fix ONLY the ruler: the man lays a plain straight steel straightedge flat "
            "on the machined surface along its length and checks the flatness with his fingertips, the straightedge fully "
            "resting on the metal with a realistic shape and size, without any markings. " + KEEP),
    "c12": ("base_c12", [], "Edit this image. Remove ONLY the roll-up shutter on the far back wall: replace it with the "
            "same plain light-beige factory wall panels and windows as the rest of that wall, so there is no shutter or "
            "door anywhere. Soft early-morning sunlight comes in through the high windows. " + KEEP),
    "c16": ("base_c16", [], "Edit this image. Change ONLY the large drawing on the table: it becomes plain white paper "
            "with thin grey pencil line drawings of machine parts (no blue). " + KEEP),
    "c33": ("base_c33", [], "Edit this image. Change ONLY the woman in the center: she turns her face slightly to the "
            "left toward her colleagues working at the desks and computers, watching over them with a warm, gentle smile. "
            "Same woman, same hair, same uniform, same place. " + KEEP),
    "c41": ("base_c41", [], "Edit this image for safety. The two men on the left step back and stand clear of the hanging "
            "steel plate, at a safe distance, with nobody under or touching the load. The white-haired man holds a yellow "
            "pendant crane control box, hanging on a cable from the crane above, in both hands and operates its buttons, "
            "watching the load. Same two men, same faces and uniforms. " + KEEP),
    "c45": ("base_c45", ["vp", "insp_woman"], "Edit image 1. The young woman left of the center man becomes the "
            "petite woman in her 50s from image 2 (same face and hair as image 2). The young woman right of the center "
            "man becomes the woman around 40 with short hair from image 3. They stay women, in the same places, poses and "
            "navy uniforms, looking up with smiles. The center man and all the men stay exactly the same. " + KEEP),
    "c48": ("base_c23", ["president"], "Using image 1 only for the art style, the factory interior and the lighting, "
            "draw a new scene inside the same factory: the company president from image 2 (a man around 40 in the navy "
            "uniform) shakes hands warmly with a customer, a Japanese businessman in a dark suit, both smiling, in front of "
            "a large finished machined steel part on the floor. Medium shot, realistic human scale. " + STYLE),
    "c49": ("base_c37", ["machinist"], "Using image 1 for the art style and the place (the yellow roll-up shutter "
            "entrance in front of the factory), draw a new scene there: a supplier's delivery man in a grey company jacket "
            "and the skilled machinist from image 2 (glasses, short hair, slim, navy uniform) check the delivered steel "
            "bars together on the truck bed and bow to each other with smiles. Medium shot, realistic scale. " + STYLE),
    "c50": ("base_c25", ["driver"], "Using image 1 for the art style and the place (the front of the factory by the "
            "yellow roll-up shutter), draw a new scene: the small elderly driver from image 2 sits in the cab of a white "
            "3-ton flatbed truck loaded with a covered finished product, leaning out of the driver's window, smiling and "
            "waving a hand as the truck starts to pull away. " + STYLE),
}

def draw(name):
    base, refs, text = JOBS[name]
    out = f"{D}/{name}.jpg"
    if os.path.exists(out):
        return f"skip {name}"
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64(f"{D}/{base}.jpg")}}]
    parts += [{"inlineData": {"mimeType": "image/jpeg", "data": b64(f"refs/illust/{r}.jpg")}} for r in refs]
    parts.append({"text": text})
    try:
        r = call("POST", "models/gemini-3.1-flash-image:generateContent", {
            "contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}},
        })
        img = next(p["inlineData"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
        open(out, "wb").write(base64.b64decode(img["data"]))
        return f"ok {name}"
    except Exception as e:
        return f"FAIL {name}: {str(e)[:200]}"

if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(draw, names):
            print(line, flush=True)
