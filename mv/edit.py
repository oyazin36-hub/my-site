# 生成したカットを実際の曲に合わせてつなぎ、歌詞テロップと年号・地名・社名を入れて書き出す
# python3 edit.py [曲ファイル]   → out/mv.mp4
import os, subprocess, sys
from cuts import TIMELINE, LYRICS, TAGS, LOGO_AT

# まだ生成できていないカットは、似た場面の生成済みカットで仮に埋める（右上に「仮」と出す）
STANDIN = {"19": "18", "22": "07", "23": "14", "24": "12", "25": "02", "26": "01", "27": "15", "28": "14",
           "29": "12", "30": "16", "31": "03", "32": "11", "33": "09", "34": "13", "35": "15", "36": "09",
           "37": "10", "38": "15", "39": "16", "40": "17", "41": "49", "42": "06", "43": "18", "44": "05",
           "45": "21", "46": "02", "47": "03", "48": "10"}

os.makedirs("out/trim", exist_ok=True)
FONT = "WenQuanYi Zen Hei"
CLIP = 8.0

def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

# 1. 各カットを尺に合わせて切る。短い尺は動きの中ほどを使い、8 秒を超える尺は少しだけゆっくり再生する
parts, STANDINS = [], []
for i, (no, s, e) in enumerate(TIMELINE):
    src, dst, dur = f"clips/cut{no}.mp4", f"out/trim/{i:02d}_{no}.mp4", e - s
    if not os.path.exists(src):
        src = f"clips/cut{STANDIN[no]}.mp4"
        STANDINS.append((s, e, no))
    off = min((CLIP - dur) / 2, 1.5) if dur < CLIP else 0
    speed = f"setpts=PTS*{dur / CLIP:.4f}," if dur > CLIP else ""
    fade = ",fade=t=in:d=0.2" if i else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.2f}", "-i", src, "-an",
                    "-vf", f"{speed}scale=1280:720,fps=24,setsar=1{fade}", "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", dst], check=True)
    parts.append(dst)
open("out/list.txt", "w").write("".join(f"file 'trim/{os.path.basename(p)}'\n" for p in parts))

# 2. 歌詞（下）、年号・地名（左上）、最後の社名（中央）を字幕にする
ass = [
    "[Script Info]", "ScriptType: v4.00+", "PlayResX: 1280", "PlayResY: 720", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Alignment, MarginL, MarginR, MarginV, BorderStyle, Outline, Shadow",
    f"Style: Lyric,{FONT},40,&H00FFFFFF,&H50000000,&H00000000,0,2,40,40,48,1,2.5,0",
    f"Style: Tag,{FONT},34,&H00FFFFFF,&H60000000,&H00000000,1,7,48,48,40,1,2,0",
    f"Style: Temp,{FONT},20,&H00FFFFFF,&H80000000,&H00000000,0,9,24,24,20,1,1.5,0",
    f"Style: Logo,{FONT},84,&H00FFFFFF,&H60000000,&H00000000,1,5,40,40,40,1,3,0",
    "", "[Events]", "Format: Layer, Start, End, Style, Text",
]
ass += [f"Dialogue: 0,{ts(a)},{ts(b - 0.05)},Lyric,{{\\fad(120,120)}}{t}" for a, b, t in LYRICS]
ass += [f"Dialogue: 0,{ts(a)},{ts(b)},Tag,{{\\fad(300,300)}}{t}" for a, b, t in TAGS]
ass += [f"Dialogue: 0,{ts(a)},{ts(b)},Temp,仮（カット{n} 未生成）" for a, b, n in STANDINS]
end = TIMELINE[-1][2]
ass.append(f"Dialogue: 0,{ts(LOGO_AT)},{ts(end)},Logo,{{\\fad(800,1200)}}原マシナリー\\N{{\\fs34}}since 1948")
open("out/mv.ass", "w").write("\n".join(ass) + "\n")

# 3. つないで字幕を焼き込み、曲を重ねる
cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "out/list.txt"]
if len(sys.argv) > 1:
    cmd += ["-i", sys.argv[1], "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k"]
cmd += ["-vf", f"ass=out/mv.ass,fade=t=out:st={end - 1.5}:d=1.5", "-t", f"{end}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "out/mv.mp4"]
subprocess.run(cmd, check=True)
print("wrote out/mv.mp4")
