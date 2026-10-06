# 10/6 夜 B 案の第 1 弾：カット 26 の絵柄（柔らかい光・やさしい陰影・表情豊かなテレビアニメ調）で 1 枚目を描き直す。出力は frames/fix11
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3

D = "frames/fix11"
S26 = f"{D}/style26.jpg"
f3.D = D
TXT = ("Redraw image 1 in exactly the art style of image 2: a polished TV-anime look with soft, warm natural light, gentle "
       "cel shading with soft gradients, thin delicate outlines (no heavy black outlines, no sketchy hatching), clean "
       "expressive faces with warm skin tones and slightly rosy cheeks, softly blurred background with depth. Keep "
       "EVERYTHING else of image 1 exactly: the same composition and camera, the same people in the same places and poses "
       "(same faces, hair, age, glasses, navy uniforms), the same machines, objects, drawings and their orientation, the "
       "same place. Do not add or remove anyone or anything. No text, letters, numbers or logos anywhere.")
JOBS = {}
for n in ("08", "09", "13", "14", "23", "27", "28", "31"):
    JOBS[f"c{n}"] = ([f"{D}/base_c{n}.jpg", S26], TXT)
# 先に描いて確認待ちの 1 枚目も同じ絵柄に
for k, src in (("c03w", "frames/fix10/c03w.jpg"), ("c03h", "frames/fix10/c03h.jpg"), ("c22", "frames/fix10/c22.jpg"),
               ("c45", "frames/fix10/c45.jpg"), ("c10s", "frames/fix10/c10s.jpg"), ("c10e", "frames/fix10/c10e.jpg"),
               ("c04_now", "frames/fix3/c04p2.jpg")):
    JOBS[k] = ([src, S26], TXT)
f3.JOBS = JOBS

if __name__ == "__main__":
    names = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line[:150], flush=True)
