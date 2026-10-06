# 10/6 カット 37：フォークリフトが鉄の束をすり抜けないよう、束はフォークの上・後ろの通り道は空にした 1 枚目
import os, sys
from concurrent.futures import ThreadPoolExecutor
import fix3_frames as f3
from fix2_frames import KEEP

D = "frames/fix8"
KEEP_TEXT = KEEP.replace(" Do not add or remove anyone.", "")
f3.D = D
T = ("Edit this image. The single bundle of long steel bars now rests flat and securely ON the two forks of the forklift, "
     "raised about 30 cm above the ground, held in front of the forklift between it and the truck; nothing else touches "
     "the bundle. Remove the hand pallet jack, the stacked steel plates and the wooden pallets on the ground, so the "
     "ground between the forklift and the open shutter is completely empty and clear. There is only this one bundle of "
     "bars in the scene. Same people, same places, same camera. " + KEEP_TEXT)
f3.JOBS = {f"c37_{k}": (["frames/fix4/c37.jpg"], T) for k in "ab"}

if __name__ == "__main__":
    os.makedirs(D, exist_ok=True)
    with ThreadPoolExecutor(2) as ex:
        for line in ex.map(f3.draw, sys.argv[1:] or list(f3.JOBS)):
            print(line, flush=True)
