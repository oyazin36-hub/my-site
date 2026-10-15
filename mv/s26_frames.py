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

# 第 2 弾：大勢の場面。人物は元の絵の人をそのまま（人数・並び・顔を変えない）、絵柄だけカット 26 に合わせる
KEEP = (" Keep EXACTLY the same people as image 2 - the same number of people, the same positions, poses, faces, hair and ages; nobody added or removed. ")
J.update({
 17: (["des_white", "assembler"], KEEP + "the moment just before the unveiling: the white glass cutting machine is still completely covered by the large cloth exactly as in image 2, and the two staff hold the cloth edges ready to pull it off. Same composition as image 2."),
 18: ([], KEEP + "employees seen from behind walk toward the bright light at the factory entrance."),
 25: (["driver"], KEEP + "shipping: the company truck carries the product level on its bed (same truck, same lettering, same load as image 2); the staff see it off."),
 27: (["president", "vp"], KEEP + "the large new gantry machine starts and everyone claps; the machine keeps exactly the same shape as image 2."),
 31: (["president"], KEEP + "morning meeting in the real office: the president speaks and the staff listen."),
 32: ([], KEEP + "lunch break in the rest room: the staff eat bento and laugh together."),
 33: (["vp"], KEEP + "the vice-president sits at her desk by the right wall and watches over everyone warmly."),
 37: (["president", "driver"], KEEP + "beside the forklift with a bundle of steel on its forks, the president and the delivery man bow to each other."),
 42: (["president", "vp"], KEEP + "everyone gathers in front of the factory."),
 45: (["president"], KEEP + "the employees look up toward the warm light; the president stands in front with a confident look."),
 48: (["president"], KEEP + "the president (from the character sheet, navy work uniform) shakes hands with the CLIENT, an older gentleman with grey hair in a dark business SUIT and tie exactly as in image 2, beside the steel frame product. Keep the same wide composition as image 2 (full bodies visible) and the product exactly as in image 2: a welded square-tube steel frame with a machined dark top plate. No tools or other objects added."),
 49: ([], KEEP + "at the end of the work day everyone in the factory waves and smiles."),
 50: ([], KEEP + "everyone gathered; warm evening light."),
})

# 細かく直したカット（場面が 2 つあるカットは a/b に分ける）。キーは文字列
J.update({
 "02": ([], "1948: ONLY the hands of a craftsman carving a stone block with a chisel and hammer in an old workshop; no face visible. Keep it black and white like image 2."),
 "03w": ([], KEEP + "the same welder as in image 2 (short hair, about fifty) is the ONLY person in the foreground; do not add anyone new; he welds a steel frame in the present-day factory, welding mask down, a bright arc; same place and composition as image 2."),
 "03h": (["vp"], KEEP + "the craftsman (exactly the same man as image 2: about fifty, short dark hair with some grey - NOT white hair) hands an A3 drawing (flat line drawing) to the vice-president in the factory; same composition as image 2."),
 "04o": ([], KEEP + "a modest 1990s town workshop: three young workers in caps work at an old lathe together. Keep the sepia tone of image 2."),
 "04f": ([], KEEP + "in the real office three people look at a drawing on the table and discuss it."),
 "22": (["new_viet", "machinist"], KEEP + "in the welding corner against the wall, the Vietnamese newcomer crouches on the floor and welds the steel frame product standing on the large steel plate, a bright arc; the senior machinist with glasses stands beside the plate with arms crossed, watching. Same room layout as image 2."),
 "38": ([], "close-up of the hand of a craftsman turning the handle of an old lathe in an old workshop (1990s); face not shown; same composition as image 2."),
 "40": ([], "two hands: an older hand drawing a machine with a pencil on paper and a younger hand at a computer whose screen shows the SAME machine as a flat 2D front-view line drawing (not 3D); same composition as image 2."),
 "41": (["adv_big", "new_pony_m"], KEEP + "keep EXACTLY the same wide straight side-view composition and framing as image 2 (whole product and both men fully visible, same sizes and distances): the steel frame product hangs perfectly level from four equal chains; the white-haired advisor holds the yellow pendant switch and the man with a ponytail stands beside him with EMPTY hands at his sides, both clear of the load. The product keeps exactly the same shape and stays level."),
 "47": (["president", "vp"], KEEP + "21 employees clap around the steel frame product and the white glass cutting machine; the president and vice-president in the middle. Keep every person exactly as in image 2 (same count, same faces)."),
})

if __name__ == "__main__":
    ns = [int(a) if a.isdigit() and int(a) in J else a for a in sys.argv[1:]] or list(J)
    f3.JOBS = {f"c{n:02d}a" if isinstance(n, int) else f"c{n}a": (["frames/s26/src26.jpg", f"frames/s26/src{n:02d}.jpg" if isinstance(n, int) else f"frames/s26/src{n}.jpg"] + [R + r + ".jpg" for r in J[n][0]], STYLE + J[n][1]) for n in ns}
    for r in ThreadPoolExecutor(5).map(f3.draw, list(f3.JOBS)):
        print(r[:120], flush=True)
