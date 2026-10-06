# 10/6 図面の装置の向きをそろえる：参考 CAD と同じ正面図（左右の柱が縦、上に梁、中央に丸い刃）を、見る人から正しい向きで
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP

D = "frames/fix7"
CAD = "refs/photo_glass_cutter_cad.png"
LINE = f"{D}/line_ref.jpg"
KEEP_TEXT = KEEP.replace(" Do not add or remove anyone.", "")
UPRIGHT = ("The drawing is exactly the front view of image 2 and is seen upright from the camera: the two tall side frames "
           "with three round holes stand vertically on the left and right, the long beam runs horizontally across the top, "
           "the large round saw blade hangs in the middle below it. Not rotated, not upside down, not mirrored, not in "
           "perspective or 3D; a flat 2D line drawing on the flat paper. ")

f3.D = D
f3.JOBS = {
    "line_ref": ([CAD],
                 "Redraw this CAD front view as a clean hand-drafted engineering drawing: grey pencil lines on plain white "
                 "paper, the whole machine centred and upright exactly as in the image (two tall side frames with three round "
                 "holes each on the left and right, the long beam across the top, the rail below it and the cutting unit with "
                 "the large round saw blade in the middle). Flat 2D front view, no colour, no perspective. Only the drawing on "
                 "white paper fills the image. No text, letters, numbers or logos anywhere."),
}
for no, base, what in (("c03", "frames/fix6/c03.jpg", "the white paper drawing the two people hold between them"),
                       ("c10s", "frames/fix6/c10s.jpg", "the flat drawing the advisor is drawing on the desk (partly finished)"),
                       ("c11", "frames/fix6/c11.jpg", "the hand-drawn drawing on the workbench and the screen of the tablet"),
                       ("c16", "frames/fix6/c16.jpg", "the large white paper drawing on the table"),
                       ("c40", "frames/fix6/c40.jpg", "the hand-drawn drawing and the drawing on the CAD screen")):
    f3.JOBS[no] = ([base, LINE], f"Edit image 1: {what} now shows the drawing of image 2. " + UPRIGHT + KEEP_TEXT)

# 2 回目：絵全体に図面が透けて重なる・紙の上で横倒しになる失敗をなくす
UPRIGHT2 = ("Only the lines printed on the paper change; nothing is overlaid on the rest of the picture (no ghost, no "
            "transparent double exposure over the people or the room). On the paper, the machine is drawn upright as seen "
            "from the camera: its top beam is at the far edge of the paper / top of the sheet, its two side frames point "
            "toward the camera / bottom of the sheet, the paper is landscape. Not rotated 90 degrees, not mirrored, not 3D. ")
for no, base, what in (("c03", "frames/fix6/c03.jpg", "the white paper drawing the two people hold between them (now held "
                        "unrolled as a flat landscape sheet facing the camera)"),
                       ("c10s", "frames/fix6/c10s.jpg", "the flat drawing the advisor is drawing on the desk (partly finished)"),
                       ("c11", "frames/fix6/c11.jpg", "the hand-drawn drawing on the workbench and the screen of the tablet"),
                       ("c16", "frames/fix6/c16.jpg", "the large white paper drawing on the table")):
    f3.JOBS[no] = ([base, LINE], f"Edit image 1: {what} now shows the drawing of image 2. " + UPRIGHT2 + KEEP_TEXT)

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    print(f3.draw("line_ref"))
    names = [n for n in sys.argv[1:] if n in f3.JOBS] or [n for n in f3.JOBS if n != "line_ref"]
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line, flush=True)
    if os.path.exists(f"{D}/c10s.jpg") and (not sys.argv[1:] or "c10e" in sys.argv[1:]):
        f3.JOBS = {"c10e": ([f"{D}/c10s.jpg", LINE],
                            "Draw the moment a few seconds later in exactly the same room, camera, people and style: the advisor "
                            "has lifted the same single flat drawing sheet off the desk with both hands and hands it, still flat, "
                            "to the smiling designer, who takes it by the other corners; the desk is now empty. The sheet faces "
                            "the camera and shows the drawing of image 2 upright, exactly the same front view. Only one drawing "
                            "sheet. No text, letters, numbers or logos anywhere.")}
        print(f3.draw("c10e"))
