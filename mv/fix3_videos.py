# カットシーン集 第2版の指示（10/4）の動画を作る。出力は clips/cutgNN.mp4。既定は Fast 版
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
# 第3版の指示（10/4 夕）
JOBS.update({
 "04b": (f"{F3}/c04p1.jpg", f"{F3}/c04p2.jpg",
         "A slow, smooth transition across time: the three young craftsmen of 1948 working together at the old lathe in sepia "
         "gradually become today's three employees in the same places and poses in today's bright factory in full color, with the "
         "same earnest, proud expressions; their hands keep working calmly. The camera stays still."),
 "41": (f"{F3}/c41b.jpg", None,
        "The white-haired man presses the buttons on the yellow pendant control box and the overhead crane slowly lifts the huge "
        "steel plate a little higher; both men stay where they are, clear of the load, watching it. Nobody else appears; nobody "
        "goes under or touches the load."),
})

# 10/5 本物の工場で描き直した 12・27
JOBS.update({
 "12r": (f"{F3}/c12r.jpg", None,
         "Early morning in the quiet factory hall: the golden sunlight through the high windows slowly grows brighter and "
         "spreads across the flat green floor, dust glitters in the light beams, the ceiling lights come on one after another; "
         "the camera slowly moves forward from the mezzanine. No people appear. Nothing floats in the air."),
 "27r": (f"{F3}/c27r.jpg", None,
         "The huge new white gantry machine starts up: its lights come on and the spindle head moves slowly along the beam; "
         "the employees in front of it look up in awe and applaud with smiles. The camera slowly tilts up to show how tall "
         "the machine is. Everyone keeps the same face."),
})

# 10/5 カットシーン集 第3版への追記（写真付き）。最初のコマは frames/fix4
F4 = "frames/fix4"
JOBS.update({
 "07": (f"{F4}/base_c07.jpg", None,
        "The milling cutter on the spindle spins fast and steadily the whole time and cuts slowly straight along the steel; "
        "fine metal chips curl away from the spinning cutter. The cutter visibly rotates in every frame. No sparks."),
 "08": (f"{F4}/c08.jpg", None,
        "The man with glasses measures the machined top plate of the large steel frame with a caliper and explains; the younger "
        "man nods and watches carefully, learning. The frame stays still and keeps its shape."),
 "09r": (f"{F4}/c09.jpg", None,
         "The man with glasses slides his fingertips along the plain steel straightedge lying flat on the machined top plate, "
         "checking the flatness. His face is alive: he blinks naturally, his eyes follow his fingers, then he gives a small "
         "satisfied nod. Slow push-in."),
 "10": (f"{F4}/c10.jpg", None,
        "The white-haired advisor finishes drawing with the pencil, rolls up the drawing and hands it with a warm smile to the "
        "younger designer, who receives it happily. His thick white hair stays the same throughout."),
 "11": (f"{F4}/c11.jpg", None,
        "The white-haired designer points at the hand-drawn drawing and the smiling designer compares it with the tablet; they "
        "nod and smile at each other. The factory behind them stays calm; the camera slowly pushes in."),
 "24r": (f"{F4}/c24.jpg", None,
         "The quality manager touches the probe in his hand to several points on the machined top plate of the steel frame, "
         "slowly and carefully. The tripod camera stays completely still and nothing moves by itself."),
 "31r": (f"{F4}/c31.jpg", None,
         "Morning meeting in the office: the president speaks with calm, confident gestures; the employees listen, nod and "
         "smile. Everyone stays in place; the camera slowly pans across the group."),
 "37r": (f"{F4}/c37.jpg", None,
         "The worker on the forklift slowly lifts the bundle of steel bars off the truck bed with the forks and backs away "
         "carefully toward the shutter; the other people stand clear, watch and bow to the delivery man. Nobody carries "
         "anything by hand."),
})

# 10/5 事務所の写真で描き直した 14・33
JOBS.update({
 "14": (f"{F4}/c14.jpg", None,
        "The smiling designer with glasses works on the CAD drawing on his monitors, moves the mouse, then leans back slightly "
        "and smiles with satisfaction. The colleagues behind him keep working quietly. Slow push-in."),
 "33r": (f"{F4}/c33.jpg", None,
         "The petite vice president sits at her desk on the right below the hanging signboards, turned toward the automatic "
         "entrance door on the left; she watches over the office and her colleagues with a warm, gentle smile. The camera "
         "slowly moves a little closer to her. Nobody else moves position."),
})

# 10/5 会社で作っているガラス切断装置（約 9 m）の除幕
JOBS.update({
 "17g": (f"{F4}/c17g.jpg", None,
         "The two men pull the light-grey cover cloth off the big glass-cutting machine; the cloth slides down slowly and stays "
         "low, never lifting into the air. Then the carriage with the round saw blade glides smoothly along the long horizontal "
         "beam from right to left while the blade spins, just like a test run, and the two men smile proudly. The machine's frame "
         "never changes shape; no parts appear or grow."),
})

# 10/5 夕：加工品の統一・10 の設計者・17 のお披露目・47 ものづくりの未来（最初のコマは frames/fix5）
F5 = "frames/fix5"
JOBS.update({
 "10b": (f"{F5}/c10.jpg", None,
         "The white-haired advisor hands the rolled drawing to the slim smiling designer with glasses, who receives it happily; "
         "they nod and smile at each other. Both men keep exactly the same faces, hair and glasses. The camera stays still."),
 "17b": (f"{F5}/c17a.jpg", f"{F5}/c17b_end.jpg",
         "The unveiling: the two men pull the huge cover cloth off together in one big sweep; it slides down and away to the "
         "floor, revealing the whole glass-cutting machine. The camera stays still; the machine's shape never changes."),
 "47b": (f"{F5}/c47.jpg", None,
         "Morning light grows brighter through the high windows; everyone looks toward the light with hopeful, determined "
         "faces; the camera slowly pulls back and rises a little. Nobody moves position; the machines and the product never "
         "change shape."),
 "07b": (f"{F5}/c07.jpg", None,
         "The milling cutter spins fast and steadily the whole time and slowly mills the flat machined top plate of the steel "
         "frame; fine chips curl away. The frame never changes shape. No sparks. The camera stays almost still."),
 "25b": (f"{F5}/c25.jpg", None,
         "The workers bow to see off the truck; the driver waves; the truck with the steel frame product under the clear sheet "
         "slowly starts to move. Nobody is on the truck bed. The camera stays still."),
 "41b": (f"{F5}/c41.jpg", None,
         "The white-haired man presses the buttons on the yellow pendant control box and the crane slowly lifts the steel frame "
         "product a little higher; both men stay clear of the load and watch. The load never moves over anyone. The camera "
         "stays still."),
 "43b": (f"{F5}/c43.jpg", None,
         "The advisor and the young newcomer look at the finished steel frame product together; the advisor points at the "
         "machined top plate and the newcomer nods with a proud smile. The camera slowly moves a little closer."),
 "48b": (f"{F5}/c48.jpg", None,
         "The president and the customer shake hands firmly and smile, then both look at the finished steel frame product "
         "beside them. The camera stays almost still."),
 "50b": (f"{F5}/c50.jpg", None,
         "The elderly driver smiles and waves from the cab as the white truck with the steel frame product under the clear "
         "sheet slowly pulls away; the workers bow. Nobody is on the truck bed at any time. The camera stays still."),
})

# 10/5 夕：カット 10 は平らな図面をそのまま手渡す（始まりと終わりのコマを指定）
JOBS.update({
 "10f": (f"{F5}/c10s.jpg", f"{F5}/c10e.jpg",
         "The white-haired advisor finishes the last line with the pencil, puts the pencil down, lifts the same large flat drawing "
         "sheet off the desk with both hands and hands it, still flat, to the smiling designer with glasses, who takes it by the "
         "other corners; they smile at each other. There is only one drawing sheet, it stays flat and keeps the same size the whole "
         "time; it is never rolled. The camera stays still."),
})

# 10/6 トラックを会社のトラック（銀色の平ボディ）に統一
JOBS.update({
 "25t": (f"{F5}/c25.jpg", None, JOBS["25b"][2] + " The truck is a silver flatbed truck and stays exactly the same."),
 "50t": (f"{F5}/c50.jpg", None, JOBS["50b"][2] + " The truck is a silver flatbed truck and stays exactly the same."),
})

MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")  # 急ぐ日は標準版を指定する

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
    # カット 3 = 年を重ねる前半（1〜7 秒目を 1.25 倍速で 4.8 秒。速すぎると手の動きが不自然）＋ 図面を手渡す後半（3.5 秒）。edit.py は 8 秒のクリップを前提に中ほどを使うので、合わせて 8 秒にする
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "clips/cutg03a.mp4", "-i", "clips/cutg03b.mp4", "-filter_complex",
                    "[0]trim=1:7,setpts=(PTS-STARTPTS)/1.25,scale=1280:720,fps=24,format=yuv420p[a];"
                    "[1]trim=1.5:5.0,setpts=PTS-STARTPTS,scale=1280:720,fps=24,format=yuv420p[b];"
                    "[a][b]xfade=transition=fade:duration=0.3:offset=4.5[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", "clips/cutg03.mp4"], check=True)

if __name__ == "__main__":
    nos = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(3) as ex:
        for m in ex.map(make, nos):
            print(m, flush=True)
    if os.path.exists("clips/cutg03a.mp4") and os.path.exists("clips/cutg03b.mp4"):
        join03(); print("joined 03")
