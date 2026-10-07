# 1 カットを差し替えたあと、保存用の動画・静止画、印刷用とカットシーン集のコマ、カットシーン集の保存用動画（曲付き）を作り直す
#   python3 refresh_cut.py 3
import subprocess, sys
from cuts import TIMELINE
from finish2 import GRADE

n = int(sys.argv[1]); no, a, b = TIMELINE[n - 1]; d = b - a
off = min((8 - d) / 2, 1.5) if d < 8 else 0
vf = f"trim={off}:{off + d},setpts=PTS-STARTPTS" if d <= 8 else f"setpts=PTS*{d / 8}"
grade = GRADE.replace("enable='not(between(t,1.8,7.4))'", f"enable='not(between(t+{a},1.8,7.4))'")
run = lambda *c: subprocess.run(["ffmpeg", "-v", "error", "-y", *c], check=True)
mp4 = f"out/cuts_save/動画/カット{n:02d}.mp4"
run("-i", f"clips/cut{no}.mp4", "-an", "-vf", f"{vf},scale=1280:720,fps=24,setsar=1," + grade, "-t", f"{d:.3f}",
    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4)
run("-ss", f"{d / 2:.3f}", "-i", mp4, "-frames:v", "1", "-q:v", "2", f"out/cuts_save/静止画/カット{n:02d}.jpg")
for k, f in enumerate((0.15, 0.5, 0.85)):
    run("-ss", f"{d * f:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=480:270", "-q:v", "3", f"out/print/img/c{n:02d}_{k}.jpg")
    subprocess.run(["cp", f"out/print/img/c{n:02d}_{k}.jpg", f"cutsheet/thumbs4/c{n:02d}_{k}.jpg"], check=True)
run("-i", mp4, "-ss", f"{a}", "-t", f"{d:.3f}", "-i", "song.mp3", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "21",
    "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", f"cutsheet/cuts5/c{n:02d}.mp4")
print("ok", n, no)
