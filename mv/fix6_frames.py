# 10/6 図面をガラス切断装置の設計図にそろえる＋25 の荷物。出力は frames/fix6/cNN.jpg（クレジット追加後に実行）
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP

D = "frames/fix6"
CAD = "refs/photo_glass_cutter_cad.png"
DRAW = ("the design drawing of the company's glass-cutting machine from the CAD image: two tall side frames with three round "
        "holes each at both ends, a long horizontal beam across the top, a long rail below it, and the cutting unit with a "
        "large round saw blade in the middle, drawn in clean lines")
KEEP_TEXT = KEEP.replace(" Do not add or remove anyone.", "")

f3.D = D
f3.JOBS = {
    "c25": (["frames/fix5/c25_v6.jpg", "frames/fix5/c50.jpg"],
            "Edit image 1: make the load on the truck bed exactly like the load in image 2: lower, a level box frame of dark "
            "steel tubes with a thick dark top plate, top edge perfectly horizontal and the same height at front and rear, under "
            "a thin clear plastic sheet. Keep the truck, its lettering, the driver, the people and everything else exactly the "
            "same."),
    "c03": (["frames/fix3/c03b.jpg", CAD],
            f"Edit image 1: the white paper drawing being handed over now shows {DRAW} (image 2), as grey pencil lines on white "
            "paper. " + KEEP_TEXT),
    "c10s": (["frames/fix5/c10s.jpg", CAD],
             f"Edit image 1: the flat drawing the advisor is drawing on the desk now shows {DRAW} (image 2), as pencil lines on "
             "white paper, partly finished. " + KEEP_TEXT),
    "c11": (["frames/fix4/c11.jpg", CAD],
            f"Edit image 1: the hand-drawn drawing on the workbench and the screen of the tablet both show {DRAW} (image 2). "
            + KEEP_TEXT),
    "c14": (["frames/fix4/c14.jpg", CAD],
            f"Edit image 1: both computer monitors show the CAD screen of image 2: {DRAW}, in colour on a dark background, like "
            "image 2. " + KEEP_TEXT),
    "c16": (["frames/fix2/c16.jpg", CAD],
            f"Edit image 1: the large white paper drawing on the table now shows {DRAW} (image 2), as grey pencil lines. "
            + KEEP_TEXT),
    "c28": ([f"{D}/base_c28.jpg", CAD],
            f"Edit image 1: the drawing on the whiteboard becomes a hand-drawn marker sketch of {DRAW} (image 2). " + KEEP_TEXT),
    "c40": ([f"{D}/base_c40.jpg", CAD],
            f"Edit image 1: both the hand-drawn drawing and the CAD screen show {DRAW} (image 2). " + KEEP_TEXT),
}

# 10/6 装置（カット 17・47）は銀色の部分以外を白に
WHITE = ("Repaint only the glass-cutting machine: every coloured part (the light-blue top beam, the green rail, the orange and "
         "yellow cutting unit, any other coloured covers) becomes clean white; the silver/metal parts (the saw blade, bare metal "
         "rails, bolts) stay silver. The machine's shape stays exactly the same. ")
f3.JOBS.update({
    "c17_end": (["frames/fix5/c17b_end.jpg"], "Edit this image. " + WHITE + KEEP_TEXT),
    "c47": (["frames/fix5/c47.jpg"], "Edit this image. " + WHITE + KEEP_TEXT),
})

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    for no, src in (("28", "24"), ("40", "33")):
        b = f"{D}/base_c{no}.jpg"
        if not os.path.exists(b):
            os.system(f"ffmpeg -v error -y -i clips/cut{src}.mp4 -frames:v 1 -q:v 2 {b}")
    names = sys.argv[1:] or list(f3.JOBS)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line, flush=True)
    # 10 の終わりのコマは、描き直した始まりのコマから作る
    if os.path.exists(f"{D}/c10s.jpg") and (not sys.argv[1:] or "c10e" in sys.argv[1:]):
        f3.JOBS = {"c10e": ([f"{D}/c10s.jpg"],
                            "Draw the moment a few seconds later in exactly the same room, camera, people and style: the advisor "
                            "has lifted the same single flat drawing sheet off the desk with both hands and hands it, still flat "
                            "and showing the same drawing, to the smiling designer, who takes it by the other corners; the desk "
                            "is now empty. Only one drawing sheet. No text, letters, numbers or logos anywhere.")}
        print(f3.draw("c10e"))
