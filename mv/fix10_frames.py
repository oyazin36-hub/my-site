# 10/6 夜のカットシーン集の指示（第5版への書き込み）の 1 枚目。出力は frames/fix10
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP, STYLE

D = "frames/fix10"
R = "refs/illust"
KEEP_ALL = KEEP.replace(" Do not add or remove anyone.", "")
PHOTO = "refs/upload/2d22f062eac8cf42b1d974bfb05f4c1c.jpg"
f3.D = D
JOBS1 = {
    # 社長の顔（いただいた写真の顔立ちを、今までの社長と同じ絵柄・紺の作業着で）
    "president_v2": ([f"{R}/president.jpg", PHOTO],
                     "Redraw the character sheet of image 1 in exactly the same anime art style, layout and navy work uniform, "
                     "but give the man the face and hair of the man in image 2: a slightly round face, short neat black hair, "
                     "calm gentle eyes and a kind, composed expression, around 40. Full body on the left, close-up of the face "
                     "on the right. No suit, no tie: the navy work uniform. No text, letters, numbers or logos anywhere."),
    # 3：50 歳くらいの職人が溶接 → 副社長へ図面を手渡す
    "c03w": ([f"{D}/base_c03young.jpg", "frames/fix2/c12.jpg", f"{R}/interior_top.jpg"],
             "Using image 1 for the man (the same craftsman, now about 50 years old: same face, a few grey hairs and fine "
             "lines, navy work uniform, leather welding gloves) and image 2 for the art style, draw him in today's real factory "
             "of image 3 (flat green floor, yellow columns): he is arc welding a joint of a steel frame on a welding table, "
             "holding the welding torch with a dark welding face shield lowered, bright blue-white arc light and a few sparks. "
             "Medium shot, realistic. " + STYLE),
    "c03h": (["frames/fix3/c03b.jpg", f"{D}/base_c03young.jpg", "frames/fix7/line_ref.jpg"],
             "Edit image 1: the white-haired craftsman becomes the same craftsman as image 2 but about 50 years old (a few "
             "grey hairs, fine lines, same face). He hands a single A3 drawing sheet (about 42 x 30 cm) to the vice president, "
             "each holding it with both hands; on the sheet is the drawing of image 3, small. Everything else stays the same. "
             + KEEP_ALL),
    # 4：1948 → 1990 年代 → 今（同じ構図の 3 人）
    "c04_1990": (["frames/fix3/c04p1.jpg", "frames/fix3/c04p2.jpg"],
                 "Draw the in-between era of images 1 (1948, sepia) and 2 (today, full color): the same three positions, poses "
                 "and composition, in a 1990s factory with slightly faded film colors: three craftsmen of the 1990s in navy "
                 "work uniforms of that time (one man with glasses, one younger man, one woman with short hair) working "
                 "together around a 1990s NC lathe with a boxy beige control panel and a small CRT screen, the same earnest, "
                 "proud expressions. " + STYLE),
    # 10：図面は A3
    "c10s": (["frames/fix9/c10s.jpg"],
             "Edit this image: the drawing sheet on the desk becomes an A3 sheet (42 x 30 cm), noticeably smaller: about as "
             "wide as the advisor's forearm is long, with lots of bare desk around it. The drawing on it is the same, scaled "
             "down, turned the same way (the right way up for the advisor). He still draws on it with the pencil. " + KEEP_ALL),
    # 22：ベトナム人の新人が溶接
    "c22": ([f"{R}/new_viet.jpg", "frames/fix2/c12.jpg", f"{R}/interior_top.jpg"],
            "Using image 1 for the young Vietnamese newcomer (same face and hair, navy work uniform, leather welding gloves) "
            "and image 2 for the art style, draw him in today's real factory of image 3 (flat green floor, yellow columns): he "
            "is welding a joint of a steel frame on a welding table, holding the torch carefully with a welding face shield "
            "lowered, bright arc light and a few sparks; an experienced senior welder (navy uniform) stands beside him "
            "watching with arms folded. Medium shot, realistic. " + STYLE),
}
JOBS2 = {
    "c45": ([f"{D}/base_c45.jpg", f"{D}/president_v2.jpg"],
            "Edit image 1: the man in the centre front (the president) gets the face and hair of the man in image 2 (same "
            "art style); same pose, uniform and upward gaze. Everyone else stays exactly the same. " + KEEP_ALL),
}

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    f3.JOBS = JOBS1
    names = [n for n in sys.argv[1:] if n in JOBS1] or list(JOBS1)
    with ThreadPoolExecutor(4) as ex:
        for line in ex.map(f3.draw, names):
            print(line[:150], flush=True)
    f3.JOBS = JOBS2
    if not sys.argv[1:] or "c45" in sys.argv[1:]:
        print(f3.draw("c45")[:150])
    # 10 の手渡しは A3 にした描いているコマから
    if os.path.exists(f"{D}/c10s.jpg") and (not sys.argv[1:] or "c10e" in sys.argv[1:]):
        f3.JOBS = {"c10e": ([f"{D}/c10s.jpg"],
                            "Draw the moment a few seconds later in exactly the same room, camera angle, people and art style: "
                            "the advisor lifts the same A3 sheet off the desk with both hands and hands it to the smiling "
                            "designer, who takes it by the other two corners; they hold it flat just above the desk. The sheet "
                            "is exactly the same size as in image 1 and the drawing on it is turned the same way. Both smile. "
                            "Only one sheet. No other people added. No text, letters, numbers or logos anywhere.")}
        print(f3.draw("c10e")[:150])
