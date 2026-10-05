# 10/5 夕の指示で描き直す 1 枚目（クレジット追加後に実行）。出力は frames/fix5/cNN.jpg
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP, STYLE

D, F2, F3, F4, R = "frames/fix5", "frames/fix2", "frames/fix3", "frames/fix4", "refs/illust"
PRODUCT = ("the company's machined product from the product photo: a large welded steel machine base frame of square steel "
           "tubes with a thick, flat, finely machined dark-steel top plate with several round holes")
KEEP_ALL = KEEP.replace(" Do not add or remove anyone.", "")

f3.D = D
f3.JOBS = {
    # 10：元の設計者（メガネ・細身・笑顔）のまま、顧問の髪だけ fix4/c10 の量に
    "c10": ([f"{F4}/orig_c10_handover.jpg", f"{F4}/c10.jpg"],
            "Edit image 1 with the smallest possible change: only the elderly man on the left gets the hair of the elderly man "
            "in image 2 (the same amount of neat short white hair). The designer on the right stays exactly as he is: the same "
            "slim smiling man with glasses and black hair receiving the rolled drawing. " + KEEP),
    # 17：装置全体が布ですっぽり覆われた始まりのコマ（終わりのコマは今の動画から）
    "c17a": ([f"{F4}/c17g.jpg"],
             "Redraw this image so that the whole machine is completely hidden under one huge light-grey cover cloth that drapes "
             "over it to the floor on every side; only its large boxy silhouette (about 9 meters wide and 4 meters tall) can be "
             "seen, nothing of the machine shows. The same two men stand at both ends holding the edges of the cloth, ready to "
             "pull it off. Same factory, same camera framing, same art style. No text, letters, numbers or logos anywhere."),
    # 47：ものづくりの未来（会社全体）
    "c47": ([f"{R}/interior_top.jpg", f"{F4}/c17g.jpg", "refs/photo_product2.jpg", f"{R}/new_shy.jpg", f"{R}/new_viet.jpg",
             f"{R}/new_pony_m.jpg", f"{R}/new_glasses.jpg", f"{R}/des_smile.jpg", f"{R}/des_white.jpg", f"{R}/assembler.jpg"],
            "Draw one wide film still in the real factory of image 1 (flat green floor, yellow columns, high windows) in "
            "morning light: in the foreground stand the four newcomers of the large metal machining department (images 4 to "
            "7) beside " + PRODUCT + " (image 3); in the background stands the company's glass-cutting machine from image 2 "
            "with the device department in front of it: the two designers (images 8 and 9) and the skilled assembler (image "
            "10). Young and veteran, both departments, all in navy work uniforms, all face the same direction toward the "
            "bright light with hopeful, determined expressions. Realistic scale. " + STYLE),
    # 加工品をこの製品にそろえる
    "c07": ([f"{F4}/base_c07.jpg", "refs/photo_product2.jpg"],
            f"Edit image 1: the steel block being cut becomes the machined top plate of {PRODUCT} (image 2), with the "
            "spinning cutter of the gantry machine milling its flat top surface. Same camera, light and style. " + KEEP_ALL),
}

def add(no, base, what):
    f3.JOBS[no] = ([base, "refs/photo_product2.jpg"],
                   f"Edit image 1: replace only {what} with {PRODUCT} (image 2), at a realistic size; nothing else changes. "
                   + KEEP_ALL)

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    for no, src in (("25", "21"), ("43", "36")):
        b = f"{D}/base_c{no}.jpg"
        if not os.path.exists(b):
            os.system(f"ffmpeg -v error -y -i clips/cut{src}.mp4 -frames:v 1 -q:v 2 {b}")
    add("c25", f"{D}/base_c25.jpg", "the covered load on the truck bed (keep a clear plastic cover over it)")
    add("c41", f"{F3}/c41b.jpg", "the hanging steel plate (the frame hangs from the crane chains)")
    add("c43", f"{D}/base_c43.jpg", "the large machined plate on the floor")
    add("c48", f"{F3}/c48.jpg" if os.path.exists(f"{F3}/c48.jpg") else f"{F2}/c48.jpg", "the steel plate beside the two men")
    add("c50", f"{F3}/c50.jpg", "the covered load on the truck bed (keep a clear plastic cover over it)")
    names = sys.argv[1:] or list(f3.JOBS)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line, flush=True)
