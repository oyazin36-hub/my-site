# カットシーン集 第2版の指示（10/4）の 1 枚目を描く。出力は frames/fix3/cNN.jpg
import base64, os, sys
from concurrent.futures import ThreadPoolExecutor
from common import call, b64
from fix2_frames import KEEP, STYLE

D = "frames/fix3"
F2 = "frames/fix2"
R = "refs/illust"

# (出力, [画像（1 枚目が元画像または画風の見本）], 指示)
JOBS = {
    "c03b": ([f"{F2}/c12.jpg", f"{F2}/c02.jpg", f"{R}/vp.jpg"],
             "Using image 1 for the art style, the place (today's factory) and the light, draw a new scene: the white-haired, "
             "slightly stern craftsman in his 70s from image 2 (same face and hair, now in the navy work uniform) hands an old, "
             "well-worn steel caliper with both hands to the petite woman in her 50s from image 3 (the vice president, same face "
             "and hair, navy uniform), who receives it with both hands. They look at each other with warm smiles. Medium shot, "
             "realistic human scale. " + STYLE),
    "c04a": ([f"{F2}/base_c02.jpg"],
             "Edit this image. Remove the young craftsman completely so the old 1948 workshop is empty, showing the old lathe "
             "clearly in the same place, the same sepia tone and the same composition. " + KEEP.replace(" Do not add or remove anyone.", "")),
    "c04b": ([f"{F2}/c12.jpg", "frames/fix3/c04a.jpg"],
             "Using image 1 for the art style and the place (today's bright factory, in color), draw the very same old lathe from "
             "image 2 (same shape and same position in the frame, same camera angle), now carefully kept and polished, standing "
             "in a clean corner of today's factory among modern machines, soft morning light. Nobody in the shot. " + STYLE),
    "c24": ([f"frames/fix2/r2base_c24.jpg", f"{R}/cmm_device.jpg"],
             "Edit image 1. The man kneeling by the steel part now holds the handheld touch probe from image 2 in his right hand "
             "and touches the machined surface with its tip, measuring it himself. The tripod camera stays exactly where it is. " + KEEP),
    "c27": ([f"frames/fix2/r2base_c27.jpg"],
             "Edit this image. Replace the small machine in the middle with a huge brand-new double-column gantry machining "
             "center about 10 meters long and 5 meters tall, light grey and white, filling the background; the workers stand in "
             "front of it and look small next to it (realistic scale). Keep the same workers, faces, uniforms, factory and art "
             "style. No text, letters, numbers or logos anywhere."),
    "c31": ([f"{R}/office.jpg", f"{R}/president.jpg"],
             "Using image 1 for the art style and the place (the company office with desks, windows and a cork board), draw the "
             "morning meeting held in this office: the president from image 2 (a man around 40, navy uniform) stands at the front "
             "and speaks, and about twelve employees in navy work uniforms stand in two rows between the desks listening, men of "
             "various ages (some white-haired elders) and three women (a petite woman in her 50s, a woman around 40 with short "
             "hair, a woman in her 50s with a ponytail). Morning light. " + STYLE),
    "c37": ([f"frames/fix2/r2base_c37.jpg"],
             "Edit this image. Remove every person in the background (inside the shutter opening and behind the truck); keep "
             "only the four people in the foreground exactly as they are. " + KEEP.replace(" Do not add or remove anyone.", "")),
    "c50": ([f"{F2}/c50.jpg"],
             "Edit this image. Nobody is on or at the truck's loading bed: remove anyone standing on, in or right behind the "
             "truck bed. The driver in the cab and the people standing on the ground stay exactly as they are. "
             + KEEP.replace(" Do not add or remove anyone.", "")),
    "c51": ([f"{F2}/c12.jpg"],
             "Using image 1 for the art style and the place (inside the factory), draw a new scene: at the end of the work day, "
             "about twelve employees in navy work uniforms stand together among the big machines, smiling and waving to the "
             "camera, warm orange evening light through the high windows. Men of various ages (some white-haired elders, one "
             "with a ponytail) and three women (a petite woman in her 50s, a woman around 40 with short hair, a woman in her 50s "
             "with a ponytail). Medium-wide shot. Not in front of the building and not outdoors. " + STYLE),
}

def draw(name):
    imgs, text = JOBS[name]
    out = f"{D}/{name}.jpg"
    if os.path.exists(out):
        return f"skip {name}"
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64(p)}} for p in imgs]
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
    os.makedirs(D, exist_ok=True)
    names = sys.argv[1:] or [n for n in JOBS if n != "c04b"]
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(draw, names):
            print(line, flush=True)
