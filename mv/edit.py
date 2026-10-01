# 生成したカットを曲の時刻どおりにつなぎ、歌詞テロップと年号・地名を入れて書き出す
# python3 edit.py [曲ファイル]   → out/mv.mp4
import os, subprocess, sys
from cuts import CUTS

os.makedirs("out/trim", exist_ok=True)
FONT = "WenQuanYi Zen Hei"

def ts(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

# 1. 各カットを使う長さに切り、720p・24fps に揃える（カット表の長さの合計＝曲の長さ）
parts = []
for c in CUTS:
    src, dst = f"clips/cut{c['no']}.mp4", f"out/trim/{c['no']}.mp4"
    if not os.path.exists(src):
        sys.exit(f"missing {src}")
    fade = "" if c is CUTS[0] else ",fade=t=in:d=0.25"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", str(c["dur"]), "-an",
                    "-vf", f"scale=1280:720,fps=24,setsar=1{fade}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", dst], check=True)
    parts.append(dst)
open("out/list.txt", "w").write("".join(f"file 'trim/{os.path.basename(p)}'\n" for p in parts))

# 2. 歌詞（下）と年号・地名（左上）、最後にロゴ代わりの社名（中央）を字幕で重ねる
ass = [
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, BorderStyle, Outline, Shadow",
    f"Style: Lyric,{FONT},40,&H00FFFFFF,&H50000000,&H00000000,0,2,40,40,48,1,2.5,0",
    f"Style: Tag,{FONT},34,&H00FFFFFF,&H60000000,&H00000000,1,7,48,48,40,1,2,0",
    f"Style: Logo,{FONT},84,&H00FFFFFF,&H60000000,&H00000000,1,5,40,40,40,1,3,0",
    "", "[Events]", "Format: Layer, Start, End, Style, Text",
]
for c in CUTS:
    s, e = c["start"], c["start"] + c["dur"]
    lines = [l for l in c["lyric"].split("／") if l]
    for i, l in enumerate(lines):  # 1 カットに複数行あるときは均等に割り振る
        a = s + c["dur"] * i / len(lines)
        b = s + c["dur"] * (i + 1) / len(lines)
        ass.append(f"Dialogue: 0,{ts(a)},{ts(b - 0.05)},Lyric,{{\\fad(150,150)}}{l}")
    if c["tc"] == "原マシナリー":
        ass.append(f"Dialogue: 0,{ts(s + 0.8)},{ts(e)},Logo,{{\\fad(800,0)}}原マシナリー\\N{{\\fs34}}since 1948")
    elif c["tc"]:
        ass.append(f"Dialogue: 0,{ts(s + 0.3)},{ts(e - 0.3)},Tag,{{\\fad(300,300)}}{c['tc']}")
open("out/mv.ass", "w").write("\n".join(ass) + "\n")

# 3. つないで字幕を焼き込み、曲があれば重ねる
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "out/list.txt"]
if len(sys.argv) > 1:
    cmd += ["-i", sys.argv[1], "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
cmd += ["-vf", "ass=out/mv.ass,fade=t=out:st=274:d=2", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "out/mv.mp4"]
subprocess.run(cmd, check=True, cwd=".")
print("wrote out/mv.mp4")
