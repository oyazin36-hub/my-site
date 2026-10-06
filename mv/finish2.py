# 社名の出し方（カット 52）を作り直して、edit.py の出力 out/mv.mp4 に重ねる
#   python3 finish2.py          → out/mv_final.mp4 と preview_final.mp4
#   python3 finish2.py test     → 社名部分だけの試し（out/logo_test.mp4）
import subprocess, sys

# 10/6 夜：全体の雰囲気をカット 26 に寄せる色合わせ（柔らかい光のにじみ・少し明るく温かく・線を少し締める）。
# 白黒のカット 2 とセピアから始まるカット 4 の前半には暖色をかけない
GRADE = ("format=gbrp,split[o][g];[g]gblur=sigma=8[gb];[o][gb]blend=all_mode=screen:all_opacity=0.14,format=yuv420p,"
         "eq=saturation=1.06:gamma=1.03:contrast=0.97,"
         "colorbalance=rm=0.03:gm=0.005:bm=-0.03:enable='not(between(t,1.8,7.4))',unsharp=5:5:0.3")

AT = 272.0  # 社名が出始める時刻。エンディング最後の全員集合（270.9〜）でカメラが空へ上がり始めるところ

def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

def logo_ass(t0, end):
    a, b = ts(t0), ts(end)
    s = lambda d: ts(t0 + d)
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,IPAGothic,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,1,0,0,0,100,100,12,0,1,0,3,5,0,0,0,1
Style: Sub,DejaVu Sans,22,&H00F2F2F2,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,10,0,1,0,0,5,0,0,0,1
Style: Gold,DejaVu Sans,18,&H0060C8E8,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,8,0,1,0,0,5,0,0,0,1
Style: Shape,DejaVu Sans,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = [
        # 文字の後ろを少し暗くして読みやすくする帯
        f"Dialogue: 0,{a},{b},Shape,,0,0,0,,{{\\pos(0,250)\\1c&H000000&\\1a&HFF&\\blur30\\t(0,800,\\1a&H78&)\\p1}}m 0 0 l 1280 0 1280 230 0 230{{\\p0}}",
        # 上下の金の細い線が中央から伸びる
        f"Dialogue: 1,{a},{b},Shape,,0,0,0,,{{\\an5\\pos(640,292)\\1c&H60C8E8&\\fscx0\\t(0,700,0.5,\\fscx100)\\p1}}m 0 0 l 560 0 560 2 0 2{{\\p0}}",
        f"Dialogue: 1,{s(0.2)},{b},Shape,,0,0,0,,{{\\an5\\pos(640,462)\\1c&H60C8E8&\\fscx0\\t(0,700,0.5,\\fscx100)\\p1}}m 0 0 l 560 0 560 2 0 2{{\\p0}}",
        # 社名：広い字間・ぼかしから、締まってくっきり現れる
        f"Dialogue: 2,{s(0.4)},{b},Main,,0,0,0,,{{\\pos(640,362)\\alpha&HFF&\\fsp46\\blur10\\t(0,1100,0.4,\\alpha&H00&\\fsp12\\blur0)}}原マシナリー",
        # 光が文字の上を一度だけ横切る
        f"Dialogue: 3,{s(1.7)},{s(2.6)},Shape,,0,0,0,,{{\\clip(330,305,950,420)\\move(250,300,1030,300)\\1c&HFFFFFF&\\1a&H50&\\blur14\\frz-20\\p1}}m 0 0 l 50 0 50 140 0 140{{\\p0}}",
        f"Dialogue: 2,{s(1.2)},{b},Sub,,0,0,0,,{{\\pos(640,428)\\alpha&HFF&\\fsp24\\t(0,900,\\alpha&H00&\\fsp10)}}HARA MACHINERY CO., LTD.",
        f"Dialogue: 2,{s(1.6)},{b},Gold,,0,0,0,,{{\\pos(640,266)\\alpha&HFF&\\t(0,800,\\alpha&H00&)}}SINCE 1948",
    ]
    return head + "\n".join(ev) + "\n"

def run(cmd):
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        # 全員集合カット（8.9 秒）の上で試す。社名は 4.1 秒目から
        open("out/logo_test.ass", "w").write(logo_ass(4.1, 8.9))
        run(["ffmpeg", "-v", "error", "-y", "-i", "clips/cut50.mp4", "-an", "-vf",
             "setpts=PTS*1.1125,ass=out/logo_test.ass", "-t", "8.9", "-c:v", "libx264", "-crf", "20", "out/logo_test.mp4"])
    else:
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    "out/mv.mp4"], capture_output=True, text=True).stdout)
        open("out/logo.ass", "w").write(logo_ass(AT, dur))
        # 曲はここで必ず入れ直す（out/mv.mp4 に音が無くても音楽付きになる）
        run(["ffmpeg", "-v", "error", "-y", "-i", "out/mv.mp4", "-i", "song.mp3", "-map", "0:v", "-map", "1:a",
             "-vf", GRADE + ",ass=out/logo.ass", "-af", f"afade=t=out:st={dur - 1.5:.2f}:d=1.5",
             "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-t", f"{dur}",
             "out/mv_final.mp4"])
        run(["ffmpeg", "-v", "error", "-y", "-i", "out/mv_final.mp4", "-c:v", "libx264", "-b:v", "620k",
             "-maxrate", "800k", "-bufsize", "1600k", "-vf", "scale=960:-2", "-c:a", "aac", "-b:a", "96k", "preview_final.mp4"])
