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
             "slightly stern craftsman in his 70s from image 2 (same face and hair, now in the navy work uniform) hands a rolled-out "
             "white paper drawing (plain grey pencil lines of a machine, no text) with both hands to the petite woman in her 50s from image 3 (the vice president, same face "
             "and hair, navy uniform), who receives it with both hands, both holding the drawing between them. They look at each other with warm smiles. Medium shot, "
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

# 第3版の指示（10/4 夕）
JOBS.update({
    "c04p1": ([f"{F2}/base_c02.jpg"],
              "Using image 1 for the sepia art style and the place (the old 1948 workshop), draw a new scene: three young "
              "craftsmen in old work clothes work together around the old lathe, one guiding the work, one measuring, one "
              "watching closely, all with the same earnest, proud expression. Medium shot, sepia old-film look. "
              "One single continuous shot. No text, letters, numbers or logos anywhere."),
    "c04p2": ([f"{F2}/c12.jpg", "frames/fix3/c04p1.jpg", f"{R}/machinist.jpg", f"{R}/new_viet.jpg", f"{R}/insp_woman.jpg"],
              "Using image 1 for the art style, colors and the place (today's bright factory), draw today's version of image 2: "
              "three of today's employees in navy work uniforms in exactly the same composition, positions and poses as the three "
              "craftsmen in image 2, working together around a modern machine with the same earnest, proud expression. The three "
              "are the man with glasses from image 3, the Vietnamese man from image 4 and the woman with short hair from image 5 "
              "(same faces and hair). " + STYLE),
    "c41b": ([f"{F2}/c41.jpg"],
             "Edit this image. Remove all the small distant people in the background (the tiny figures between and behind the "
             "machines), so only the two men in front remain. " + KEEP.replace(" Do not add or remove anyone.", "")),
})

# 10/5 本物の工場（中二階からの写真）を元に描き直す
JOBS.update({
    "c12r": ([f"{R}/interior_top.jpg"],
             "Edit this image only in its lighting and time of day: it is early morning before work starts; warm golden "
             "morning sunlight streams in through the high windows on the right in soft beams across the flat green floor, "
             "the hall is still quiet and slightly dim. Keep exactly the same view, layout, machines, steel frames and flat "
             "floor. No people. No text, letters, numbers or logos anywhere."),
    "c27r": ([f"{R}/interior_top.jpg", f"{F2}/c12.jpg", f"{R}/president.jpg"],
             "Using image 1 for the place (this real factory hall with the flat green floor, yellow columns and the big white "
             "double-column gantry machining center with black bellows covers on the right) and image 2 for the art style, draw "
             "a new shot from floor level: the huge white gantry machining center, about 10 meters long and 5 meters tall, "
             "towers in the middle of the frame; about ten employees in navy work uniforms stand on the green floor in front of "
             "it, realistic human scale (people reach about a third of the machine's height), looking up at it and applauding "
             "with smiles; the president from image 3 stands among them. " + STYLE),
})

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
