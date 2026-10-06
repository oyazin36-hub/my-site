# 10/6 夕のカットシーン集の指示：21 ガラス切断装置の支柱のボルトを締めて組み立てる／10 図面の大きさを変えない手渡し
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP, STYLE

D = "frames/fix9"
f3.D = D
f3.JOBS = {
    "c21": ([f"{D}/base_c21.jpg", "frames/fix6/c17_end.jpg", "refs/photo_glass_cutter_cad.png", "refs/illust/interior_top.jpg"],
            "Using image 1 for the man (the same skilled assembler with glasses, short black hair and a short beard, same face, "
            "navy uniform) and the art style, draw a new scene in the real factory of image 4 (flat green floor, yellow "
            "columns, high windows): he is assembling the company's glass-cutting machine from images 2 and 3. One of its tall "
            "white side columns (a tall white steel frame with three large round holes) stands upright on the floor beside him "
            "on its base, and he tightens the large silver bolts at the foot of that column with a long torque wrench, "
            "concentrating. The long top beam is not mounted yet. The machine is white except for its silver metal parts. "
            "Medium shot, realistic human scale (the column is about 4 meters tall, much taller than him). Nobody else nearby. "
            + STYLE),
    "c10e2": (["frames/fix7/c10s.jpg", "frames/fix7/line_ref.jpg"],
              "Draw the moment a few seconds later in exactly the same room, camera angle, people and art style as image 1: "
              "the advisor has lifted the very same large sheet off the desk and hands it to the smiling designer; each holds "
              "two corners and they hold it flat and level just above the desk, so the sheet keeps EXACTLY the same size and "
              "shape as it had lying on the desk in image 1 and still shows the same drawing (image 2) the same way up. "
              "Both smile. Only one sheet. No other people added. No text, letters, numbers or logos anywhere."),
}

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    if not os.path.exists(f"{D}/base_c21.jpg"):
        os.system(f"ffmpeg -v error -y -i clips/cut18.mp4 -frames:v 1 -q:v 2 {D}/base_c21.jpg")
    with ThreadPoolExecutor(2) as ex:
        for line in ex.map(f3.draw, sys.argv[1:] or list(f3.JOBS)):
            print(line, flush=True)
