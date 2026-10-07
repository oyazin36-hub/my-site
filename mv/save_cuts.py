# 保存用：カットごとの動画（音なし）と静止画（中ほどの 1 コマ）。cut_preview.py と同じ切り出し位置・色合わせ
#   python3 save_cuts.py → out/cuts_save/動画/カットNN.mp4, out/cuts_save/静止画/カットNN.jpg
import os, subprocess
from cuts import TIMELINE
from finish2 import GRADE

V, S = "out/cuts_save/動画", "out/cuts_save/静止画"
os.makedirs(V, exist_ok=True); os.makedirs(S, exist_ok=True)
for n, (no, a, b) in enumerate(TIMELINE, 1):
    d = b - a
    off = min((8 - d) / 2, 1.5) if d < 8 else 0
    vf = f"trim={off}:{off + d},setpts=PTS-STARTPTS" if d <= 8 else f"setpts=PTS*{d / 8}"
    grade = GRADE.replace("enable='not(between(t,1.8,7.4))'", f"enable='not(between(t+{a},1.8,7.4))'")
    mp4 = f"{V}/カット{n:02d}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"clips/cut{no}.mp4", "-an", "-vf", f"{vf},scale=1280:720,fps=24,setsar=1," + grade,
                    "-t", f"{d:.3f}", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d / 2:.3f}", "-i", mp4, "-frames:v", "1", "-q:v", "2", f"{S}/カット{n:02d}.jpg"], check=True)
    print(n, no, a, b, flush=True)
