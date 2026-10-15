# カット 26 の絵柄に合わせて各カットの絵を描き直す（見本＝カット26、元の絵＝そのカットの今の絵、人物は設定集）
#   PYTHONPATH=. python3 s26_frames.py 9 10 ...   → frames/s26/cNNa.jpg
import sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
f3.D = "frames/s26"
STYLE = ("Image 1 is ONLY a style sample: copy its soft, slightly realistic Japanese anime look, gentle line work, warm soft glowing light, color palette, "
         "shallow depth of field with a softly blurred background, expressive natural faces and a fairly close camera - but do NOT copy any person from image 1. "
         "Redraw the scene of image 2 in that style, keeping its content: the same people doing the same thing, the same machines, objects and place, "
         "roughly the same composition (bring the camera a little closer if it helps). Every machine and object keeps exactly the same shape and design as in image 2. "
         "The people must match the character sheets given after image 2 (same face, hair, age, glasses), all in the company navy work uniform unless stated. "
         "Realistic sizes. No text, no letters, no logos. Scene: ")
R = "refs/illust/"
J = {
 9: (["insp_mid"], "the inspector with glasses lays a straightedge on the machined top plate of the steel frame product and checks its flatness closely, calm and focused."),
 10: (["adv_slim", "des_smile"], "closer view from the side at table height: the slim elderly advisor draws on an A3 machine drawing on a wooden table (the drawing faces him), and the smiling designer with glasses watches beside him; their faces are clearly visible. The drawing is flat paper with line drawings only."),
 11: (["des_white", "des_smile"], "the white-haired senior designer and the smiling designer with glasses stand in the factory comparing a printed drawing with a tablet, talking. The factory floor stays GREEN exactly like image 2."),
 13: (["machinist"], "the senior machinist with glasses presses a button on the machine control panel, focused."),
 14: (["des_smile"], "in the office, the smiling designer with glasses designs a glass cutting machine in CAD on two monitors (simple line drawings on screen, no text); he looks at the screen, not at the camera, and uses the mouse."),
 21: (["assembler"], "the bearded master assembler stands on the floor and tightens an M20 nut with a normal-sized wrench (about 30 cm long, one hand) at a joint low on a column of the white glass cutting machine under assembly; the machine keeps exactly the same shape as in image 2."),
 23: (["concept", "des_smile"], "a client in a dark suit explains his request at a table; the cheerful, slightly plump elderly concept designer from the first character sheet (seventies, NO glasses, clean-shaven, round friendly face) sketches ideas on paper, and the slim smiling designer with glasses from the second character sheet listens beside him. Exactly these two employees and the client."),
 24: (["qc_chief", "cmm_device"], "closer view: the quality-control chief is actively measuring - he holds the black handheld touch probe with green lights (exactly like the left device in the last reference image) firmly in his hand and presses its small red-tipped stylus against the edge of a hole in the machined top plate of the steel frame product, his eyes on the contact point, concentrating. Behind him the white tracker camera on its black tripod (like the right device in the last reference image) faces the probe. He is clearly working, not posing."),
 39: (["machinist"], "the senior machinist with glasses operates the control panel of a modern machine, focused."),
 43: (["adv_big", "new_shy"], "the strong elderly advisor (short white hair) and the shy young newcomer look at the finished steel frame product together; the advisor points at the machined top plate and the newcomer smiles proudly."),
}
if __name__ == "__main__":
    ns = [int(a) for a in sys.argv[1:]] or list(J)
    f3.JOBS = {f"c{n:02d}a": (["frames/s26/src26.jpg", f"frames/s26/src{n:02d}.jpg"] + [R + r + ".jpg" for r in J[n][0]], STYLE + J[n][1]) for n in ns}
    for r in ThreadPoolExecutor(5).map(f3.draw, list(f3.JOBS)):
        print(r[:120], flush=True)
