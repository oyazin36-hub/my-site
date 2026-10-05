# カットシーン集 第3版への追記（10/5、写真付き）の 1 枚目を描く。出力は frames/fix4/cNN.jpg
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP, STYLE

D = "frames/fix4"
F2, F3, R = "frames/fix2", "frames/fix3", "refs/illust"
PRODUCT = ("the real product from the product photo: a large welded steel machine base frame, a box-shaped frame of square "
           "steel tubes with a thick, flat, finely machined dark-steel top plate with a few round holes")
NO_COPY = "Do not copy any real person from the photos; use the photos only for the place and objects."
KEEP_ALL = KEEP.replace(" Do not add or remove anyone.", "")

f3.D = D
f3.JOBS = {
    "c08": ([f"{D}/base_c08.jpg", "refs/photo_product.jpg"],
            f"Edit image 1. Replace only the metal workpiece on the bench with {PRODUCT} (image 2), at a realistic size; "
            "the two men keep exactly the same faces, uniforms and poses, the man with glasses measuring the machined top "
            "plate and the younger man watching and learning. " + NO_COPY + " " + KEEP_ALL),
    "c09": ([f"{F2}/c09.jpg", "refs/photo_product.jpg"],
            f"Edit image 1. Replace only the long machined bed with the machined top plate of {PRODUCT} (image 2); the man "
            "with glasses lays the plain steel straightedge flat on that top plate and checks the flatness with his "
            "fingertips. Same man, same face and pose. " + NO_COPY + " " + KEEP_ALL),
    "c10": ([f"{D}/base_c10.jpg"],
            "Edit this image. Give only the elderly white-haired man with glasses a fuller head of hair: thick, neatly "
            "combed white hair, no bald or thin spots. Same face, glasses, uniform and pose. " + KEEP),
    "c11": ([f"{D}/base_c11.jpg", f"{R}/interior_top.jpg"],
            "Using image 1 for the two men (the white-haired designer and the smiling designer with glasses, same faces, "
            "hair and navy uniforms) and the action (comparing a hand-drawn drawing with a tablet on a workbench), draw the "
            "same moment inside the real factory of image 2 at floor level: the workbench stands on the flat green floor, "
            "with the yellow columns, high windows, steel frames and the big white gantry machines behind them. " + STYLE),
    "c24": ([f"{F3}/c24.jpg", "refs/photo_product.jpg"],
            f"Edit image 1. Replace only the steel part on the floor with {PRODUCT} (image 2), at a realistic size; the "
            "quality manager kneels beside it and touches the machined top plate with the handheld probe; the tripod "
            "camera stays where it is. " + NO_COPY + " " + KEEP_ALL),
    "c31": ([f"{F3}/c31.jpg", "refs/photo_office.jpg"],
            "Redraw image 1 (the morning meeting: the president speaking and the employees in navy uniforms standing and "
            "listening, same people) in the real office of image 2: a bright office with a white ceiling and long "
            "fluorescent lights, long rows of white desks with computers, grey filing cabinets and a corridor by the "
            "windows. " + NO_COPY + " " + STYLE),
    "c37": ([f"{F3}/c37.jpg"],
            "Edit this image. The steel bars are unloaded from the truck with a forklift: a compact forklift driven by a "
            "worker in the navy uniform lifts the bundle of steel bars off the truck bed with its forks; nobody carries "
            "anything by hand; the other people stand clear and watch. " + KEEP_ALL),
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(f3.JOBS)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line, flush=True)
