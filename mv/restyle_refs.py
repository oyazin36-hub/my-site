# 人物と場所の参照画像を、画風の見本（refs/style.jpg）に合わせて描き直す
import base64
from concurrent.futures import ThreadPoolExecutor
from common import call, b64
from staff import STAFF
from make_clip import STYLE

NOTE = "Image 1 shows ONLY the art style to copy (ignore the woman in it; do not copy her glasses, hair or clothes). Draw in exactly that art style. "
SHEET = "A character reference sheet: full-body front view and a head-and-shoulders close-up side by side on a plain softly lit background. 16:9. No text. Character: "
JOBS = {k: ([], SHEET + en) for k, (_, en) in STAFF.items()}
JOBS["c1948"] = ([], SHEET + "a Japanese man in his twenties with short black hair, wearing a navy work jacket, 1940s clothing")
P = "A 16:9 establishing shot with no people, drawn from the attached photo(s), keeping the real layout, objects and colors faithfully. No text, no logos, no maker names. "
JOBS["exterior"] = (["photo_exterior"], P.replace(" No text, no logos, no maker names.", "") + "Redraw THIS EXACT building from the same camera angle as the photo (it is the fixed official look of the company): long two-story white factory building with a blue band and red stripe along the top, the round company emblem and the yellow company name lettering on the blue band, a canopy over the light-yellow roll-up shutter, a white two-story office wing on the right with an entrance canopy, a stone lantern left of the shutter, round trimmed shrubs along the front, a long natural stone retaining wall, an asphalt driveway in front, a wooded green hill behind, clear blue sky. Keep everything in the same place as the photo.")
JOBS["factory_real"] = (["photo_interior_a", "photo_interior_b"], P + "The factory interior: very high ceiling with orange-brown steel roof beams on yellow columns, high clerestory windows, beige corrugated walls, grey concrete floor, large green radial drills and green machines, big cream-white machining centers, a yellow crane hook reel, welded steel frames and machined plates on the floor.")
JOBS["big_part"] = (["photo_interior"], P + "Close-up hero shot of a huge flat precision-machined steel plate several meters long with a mirror-like milled surface, machined pockets, T-slots and bolt holes, resting on a grey concrete factory floor, machines blurred behind.")
JOBS["cmm_device"] = (["photo_cmm"], "Draw ONLY the equipment on a plain light background, 16:9: a white and silver cylindrical tracking camera head on a black tripod, a black handheld touch probe with green marker LEDs and a red ruby stylus tip, and a handheld laser scan probe with green marker LEDs emitting blue laser light. No text, numbers, brand names or logos. ")
JOBS["okazaki"] = ([], "A 16:9 establishing shot with no people: the city of Okazaki in Aichi seen from a hill, with the Yahagi River flowing through it. No text.")
JOBS["old_shop"] = ([], "A 16:9 establishing shot with no people: a small 1940s Japanese machine workshop with wooden beams and old machines, slanted window light, sepia tones. No text.")
JOBS["office"] = ([], "A 16:9 establishing shot with no people: a calm design office by the window with CAD monitors and machine drawings pinned on the wall. No text.")

def go(item):
    k, (photos, text) = item
    parts = [{"inlineData": {"mimeType": "image/jpeg", "data": b64("refs/style.jpg")}}]
    parts += [{"inlineData": {"mimeType": "image/jpeg", "data": b64(f"refs/{p}.jpg")}} for p in photos]
    parts.append({"text": NOTE + text + " " + STYLE})
    for _ in range(2):
        try:
            r = call("POST", "models/gemini-3.1-flash-image:generateContent", {"contents": [{"parts": parts}],
                     "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}})
            img = next(p["inlineData"] for p in r["candidates"][0]["content"]["parts"] if "inlineData" in p)
            open(f"refs/{k}.jpg", "wb").write(base64.b64decode(img["data"]))
            return "ok " + k
        except Exception as e:
            err = str(e)[:80]
    return "FAIL " + k + " " + err

if __name__ == "__main__":
    import sys
    keys = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(5) as ex:
        print(" ".join(ex.map(go, [(k, JOBS[k]) for k in keys])))
