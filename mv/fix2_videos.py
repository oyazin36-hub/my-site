# カットシーン集の指示（10/3）で直した 1 枚目（frames/fix2/cNN.jpg）から動画を作る。出力は clips/cutfNN.mp4（NN はシートのカット番号）
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY

D = "frames/fix2"
STYLE = ("Japanese hand-drawn anime film style, soft painterly backgrounds, warm natural light, muted colors, gentle film grain, cinematic 16:9. "
         "Keep the art style, colors, faces, genders and composition of the first frame. Nobody appears who is not in the first frame "
         "and nobody disappears. One single continuous shot. No on-screen text, no letters or numbers, no logos, no sparks.")
MOTION = {
 "02": "Sepia old-film look. The white-haired, slightly stern craftsman in his 70s carefully wipes and tends the old lathe with a cloth, calm and focused; the camera slowly pushes in. He stays the same old man throughout.",
 "03": "The woman walks a few steps forward through the factory and the camera moves closer; she picks up an old photograph and looks at it with a gentle, nostalgic smile. Up close she looks youthful, around 60, smooth skin, bright face, dark brown bob hair.",
 "09": "The man with glasses slowly slides his fingertips along the plain steel straightedge that lies flat on the machined surface, checking the flatness carefully; the straightedge stays flat on the metal. Slow push-in.",
 "12": "Early morning: soft golden sunlight gradually grows brighter through the high windows and spreads across the floor, the workers start their machines; the camera slowly pushes forward. There is no shutter or door on the back wall; nothing floats in the air.",
 "16": "The three men lean over the white paper drawing on the table, point at it and laugh together warmly; the camera stays still. The paper stays plain white with grey pencil lines.",
 "17": "The two men pull the light-grey cover cloth off the machine; the cloth slides down and drops to the floor and they smile proudly. The machine stays exactly the same shape the whole time; no parts grow, move or appear on it.",
 "30": "The camera rises straight up from the city through the clouds, higher and higher into the dark blue sky and out into space, finally showing the whole planet Earth floating in space. There is only ever one Earth; no second planet appears.",
 "33": "The petite woman slowly turns her head toward her colleagues working at the desks and computers and watches over them with a warm, gentle smile. The camera slowly moves a little closer.",
 "41": "The white-haired man presses the buttons on the yellow pendant control box and the overhead crane slowly lifts the huge steel plate a little higher; both men stay where they are, clear of the load, watching it. Nobody goes under or touches the load.",
 "45": "Everyone looks up toward the bright light with determined smiles, a gentle breeze moves their hair; the camera very slowly pushes in. Every person, including the man in the center, stays in the shot the whole time with the same face and gender.",
 "47": "Still-life: a slow gentle push-in on the two calipers on the wooden workbench, warm evening light, floating dust. The calipers and the blank display never show any letters or numbers.",
 "48": "The president in the navy uniform and the customer in a dark suit shake hands firmly and smile, then both look at the large finished steel plate beside them; the camera slowly moves around them a little.",
 "49": "In front of the factory shutter, the delivery man in grey and the machinist with glasses bow to each other with smiles beside the truck with steel bars; the camera stays steady.",
 "50": "The elderly driver smiles and waves his hand from the truck window as the white 3-ton truck slowly pulls away from the factory front; the workers bow to see it off.",
}
MODELS = ["veo-3.1-fast-generate-preview", "veo-3.1-generate-preview", "veo-3.1-lite-generate-preview"]

def make(no):
    out = f"clips/cutf{no}.mp4"
    if os.path.exists(out):
        return f"skip {no}"
    first = f"{D}/c30_first.jpg" if no == "30" else f"{D}/c{no}.jpg"
    last = None
    for model in MODELS:
        inst = {"prompt": MOTION[no] + " " + STYLE,
                "image": {"bytesBase64Encoded": b64(first), "mimeType": "image/jpeg"}}
        if no == "30" and "lite" not in model:  # 終わりのコマも指定して、地球が二重にならないようにする
            inst["lastFrame"] = {"bytesBase64Encoded": b64(f"{D}/c30_last.jpg"), "mimeType": "image/jpeg"}
        try:
            op = call("POST", f"models/{model}:predictLongRunning", {
                "instances": [inst], "parameters": {"aspectRatio": "16:9", "durationSeconds": 8}})
            while not op.get("done"):
                time.sleep(15); op = call("GET", op["name"])
            s = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples")
            if not s:
                last = str(op.get("error") or op.get("response"))[:120]
                continue
            req = urllib.request.Request(s[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
            with urllib.request.urlopen(req) as r, open(out, "wb") as f:
                f.write(r.read())
            return f"ok {no} {model}"
        except Exception as e:
            last = str(e)[:160]
    return f"FAIL {no} {last}"

if __name__ == "__main__":
    nos = sys.argv[1:] or list(MOTION)
    with ThreadPoolExecutor(3) as ex:
        for m in ex.map(make, nos):
            print(m, flush=True)
