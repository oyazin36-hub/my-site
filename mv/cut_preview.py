# 1 カットだけの確認用動画（通しの MV は作らない）。edit.py と同じ切り出し位置・finish2.py と同じ色合わせ、曲はその区間
#   python3 cut_preview.py 4   → out/cut04_preview.mp4
import subprocess, sys
from cuts import TIMELINE
from finish2 import GRADE

n = int(sys.argv[1])
no, a, b = TIMELINE[n - 1]
d = b - a
off = min((8 - d) / 2, 1.5) if d < 8 else 0
vf = f"trim={off}:{off + d},setpts=PTS-STARTPTS" if d <= 8 else f"setpts=PTS*{d / 8}"
grade = GRADE.replace("enable='not(between(t,1.8,17.4))'", f"enable='not(between(t+{a},1.8,17.4))'")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"clips/cut{no}.mp4", "-ss", f"{a}", "-t", f"{d:.3f}", "-i", "song.mp3",
                "-map", "0:v", "-map", "1:a", "-vf", vf + "," + grade, "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", f"out/cut{n:02d}_preview.mp4"], check=True)
print(f"out/cut{n:02d}_preview.mp4", no, a, b)
