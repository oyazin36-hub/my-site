# カットシーン集 第2版の指示（10/4）の動画を作る。出力は clips/cutgNN.mp4。費用を抑えるため Fast 版だけで作る
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY
from fix2_videos import STYLE

F2, F3 = "frames/fix2", "frames/fix3"
# 番号: (最初のコマ, 終わりのコマ または None, 動き)
JOBS = {
 "03a": (f"{F2}/base_c02.jpg", f"{F2}/c02.jpg",
         "Sepia old-film look. The craftsman keeps tending the old lathe in the same place while the years pass: his black hair "
         "slowly turns white and his face gently ages into a slightly stern man in his 70s. Same man, same pose, same workshop; "
         "the camera stays still. Only he is in the shot."),
 "03b": (f"{F3}/c03b.jpg", None,
         "The white-haired craftsman hands the white paper drawing to the vice president; she takes it carefully with both hands, "
         "they look at each other and smile warmly, and she nods. The drawing stays plain with grey pencil lines. The camera slowly pushes in."),
 "04": (f"{F3}/c04a.jpg", f"{F3}/c04b.jpg",
        "A slow, smooth time-lapse transition: the empty sepia 1948 workshop with the old lathe gradually turns into today's bright "
        "factory in full color, while the very same old lathe stays in the shot the whole time. Nobody appears."),
 "09": (f"{F2}/c09.jpg", None,
        "The man with glasses slides his fingertips along the plain steel straightedge lying flat on the machined surface, checking "
        "the flatness. His face is alive: he blinks naturally, his eyes follow his fingers, he narrows his eyes in concentration and "
        "then gives a small satisfied nod. Slow push-in."),
 "17": (f"{F2}/c17.jpg", None,
        "The two men gently pull the light-grey cover cloth toward them; the cloth slides slowly down the side of the machine, stays low "
        "and never lifts into the air, and settles in a heap on the floor; then they smile proudly. The machine never changes shape."),
 "24": (f"{F3}/c24.jpg", None,
        "The quality manager touches the probe in his hand to several points on the machined steel part, moving it slowly and carefully "
        "and checking the result. The tripod camera stays completely still and nothing moves by itself."),
 "27": (f"{F3}/c27.jpg", None,
        "The huge new gantry machine starts up: its lights come on and the head moves slowly along the beam; the workers watch in awe "
        "and then applaud with smiles. The camera slowly tilts up to show how tall the machine is."),
 "31": (f"{F3}/c31.jpg", None,
        "Morning meeting in the office: the president speaks to the staff with calm, confident gestures; the employees listen, nod and "
        "smile. Everyone stays in place; the camera slowly pans across the group."),
 "37": (f"{F3}/c37.jpg", None,
        "In front of the factory shutter, the supplier's delivery man and the workers bow to each other and start unloading the steel "
        "bars together carefully. Only the people already in the shot; nobody else appears in the background."),
 "50": (f"{F3}/c50.jpg", None,
        "The elderly driver smiles and waves from the cab window as the white 3-ton truck slowly pulls away; the workers on the ground "
        "bow to see it off. Nobody is on the truck's loading bed at any time; nobody climbs onto it."),
 "51": (f"{F3}/c51.jpg", None,
        "At the end of the work day, the employees standing together among the machines smile and wave to the camera, warm evening "
        "light; the camera slowly pulls back a little. Everyone keeps the same face."),
}
MODEL = "veo-3.1-fast-generate-preview"

def make(no):
    out = f"clips/cutg{no}.mp4"
    if os.path.exists(out):
        return f"skip {no}"
    first, last, motion = JOBS[no]
    inst = {"prompt": motion + " " + STYLE, "image": {"bytesBase64Encoded": b64(first), "mimeType": "image/jpeg"}}
    if last:
        inst["lastFrame"] = {"bytesBase64Encoded": b64(last), "mimeType": "image/jpeg"}
    try:
        op = call("POST", f"models/{MODEL}:predictLongRunning", {
            "instances": [inst], "parameters": {"aspectRatio": "16:9", "durationSeconds": 8}})
        while not op.get("done"):
            time.sleep(15); op = call("GET", op["name"])
        s = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples")
        if not s:
            return f"FAIL {no} {str(op.get('error') or op.get('response'))[:160]}"
        req = urllib.request.Request(s[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
        with urllib.request.urlopen(req) as r, open(out, "wb") as f:
            f.write(r.read())
        return f"ok {no}"
    except Exception as e:
        return f"FAIL {no} {str(e)[:160]}"

def join03():
    # カット 3 = 年を重ねる前半（8 秒を約 2 倍速で 4.1 秒）＋ 図面を手渡す後半（4.2 秒）。edit.py は 8 秒のクリップを前提に中ほどを使うので、合わせて 8 秒にする
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "clips/cutg03a.mp4", "-i", "clips/cutg03b.mp4", "-filter_complex",
                    "[0]setpts=PTS/1.95,scale=1280:720,fps=24,format=yuv420p[a];"
                    "[1]trim=1.5:5.7,setpts=PTS-STARTPTS,scale=1280:720,fps=24,format=yuv420p[b];"
                    "[a][b]xfade=transition=fade:duration=0.3:offset=3.8[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", "clips/cutg03.mp4"], check=True)

if __name__ == "__main__":
    nos = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(3) as ex:
        for m in ex.map(make, nos):
            print(m, flush=True)
    if os.path.exists("clips/cutg03a.mp4") and os.path.exists("clips/cutg03b.mp4"):
        join03(); print("joined 03")
