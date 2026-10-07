# カットシーン集 第2版の指示（10/4）の動画を作る。出力は clips/cutgNN.mp4。既定は Fast 版
import os, sys, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from common import call, b64, KEY
from fix2_videos import STYLE

F2, F3 = "frames/fix2", "frames/fix3"
# 番号: (最初のコマ, 終わりのコマ または None, 動き)
JOBS = {
 "03a": (f"{F2}/base_c02.jpg", f"{F2}/c02.jpg",
         "Sepia old-film look. The craftsman keeps tending the old lathe in the same place while the years pass: his black hair "
         "slowly turns white and his face gently ages into a slightly stern man in his 70s. Same man, same pose, same workshop; "
         "the camera stays still. Only he is in the shot."),
 "03b": (f"{F3}/c03b.jpg", None,
         "The white-haired craftsman hands the white paper drawing to the vice president; she takes it carefully with both hands, "
         "they look at each other and smile warmly, and she nods. The drawing stays plain with grey pencil lines. The camera slowly pushes in."),
 "04": (f"{F3}/c04a.jpg", f"{F3}/c04b.jpg",
        "A slow, smooth time-lapse transition: the empty sepia 1948 workshop with the old lathe gradually turns into today's bright "
        "factory in full color, while the very same old lathe stays in the shot the whole time. Nobody appears."),
 "09": (f"{F2}/c09.jpg", None,
        "The man with glasses slides his fingertips along the plain steel straightedge lying flat on the machined surface, checking "
        "the flatness. His face is alive: he blinks naturally, his eyes follow his fingers, he narrows his eyes in concentration and "
        "then gives a small satisfied nod. Slow push-in."),
 "17": (f"{F2}/c17.jpg", None,
        "The two men gently pull the light-grey cover cloth toward them; the cloth slides slowly down the side of the machine, stays low "
        "and never lifts into the air, and settles in a heap on the floor; then they smile proudly. The machine never changes shape."),
 "24": (f"{F3}/c24.jpg", None,
        "The quality manager touches the probe in his hand to several points on the machined steel part, moving it slowly and carefully "
        "and checking the result. The tripod camera stays completely still and nothing moves by itself."),
 "27": (f"{F3}/c27.jpg", None,
        "The huge new gantry machine starts up: its lights come on and the head moves slowly along the beam; the workers watch in awe "
        "and then applaud with smiles. The camera slowly tilts up to show how tall the machine is."),
 "31": (f"{F3}/c31.jpg", None,
        "Morning meeting in the office: the president speaks to the staff with calm, confident gestures; the employees listen, nod and "
        "smile. Everyone stays in place; the camera slowly pans across the group."),
 "37": (f"{F3}/c37.jpg", None,
        "In front of the factory shutter, the supplier's delivery man and the workers bow to each other and start unloading the steel "
        "bars together carefully. Only the people already in the shot; nobody else appears in the background."),
 "50": (f"{F3}/c50.jpg", None,
        "The elderly driver smiles and waves from the cab window as the white 3-ton truck slowly pulls away; the workers on the ground "
        "bow to see it off. Nobody is on the truck's loading bed at any time; nobody climbs onto it."),
 "51": (f"{F3}/c51.jpg", None,
        "At the end of the work day, the employees standing together among the machines smile and wave to the camera, warm evening "
        "light; the camera slowly pulls back a little. Everyone keeps the same face."),
}
# 第3版の指示（10/4 夕）
JOBS.update({
 "04b": (f"{F3}/c04p1.jpg", f"{F3}/c04p2.jpg",
         "A slow, smooth transition across time: the three young craftsmen of 1948 working together at the old lathe in sepia "
         "gradually become today's three employees in the same places and poses in today's bright factory in full color, with the "
         "same earnest, proud expressions; their hands keep working calmly. The camera stays still."),
 "41": (f"{F3}/c41b.jpg", None,
        "The white-haired man presses the buttons on the yellow pendant control box and the overhead crane slowly lifts the huge "
        "steel plate a little higher; both men stay where they are, clear of the load, watching it. Nobody else appears; nobody "
        "goes under or touches the load."),
})

# 10/5 本物の工場で描き直した 12・27
JOBS.update({
 "12r": (f"{F3}/c12r.jpg", None,
         "Early morning in the quiet factory hall: the golden sunlight through the high windows slowly grows brighter and "
         "spreads across the flat green floor, dust glitters in the light beams, the ceiling lights come on one after another; "
         "the camera slowly moves forward from the mezzanine. No people appear. Nothing floats in the air."),
 "27r": (f"{F3}/c27r.jpg", None,
         "The huge new white gantry machine starts up: its lights come on and the spindle head moves slowly along the beam; "
         "the employees in front of it look up in awe and applaud with smiles. The camera slowly tilts up to show how tall "
         "the machine is. Everyone keeps the same face."),
})

# 10/5 カットシーン集 第3版への追記（写真付き）。最初のコマは frames/fix4
F4 = "frames/fix4"
JOBS.update({
 "07": (f"{F4}/base_c07.jpg", None,
        "The milling cutter on the spindle spins fast and steadily the whole time and cuts slowly straight along the steel; "
        "fine metal chips curl away from the spinning cutter. The cutter visibly rotates in every frame. No sparks."),
 "08": (f"{F4}/c08.jpg", None,
        "The man with glasses measures the machined top plate of the large steel frame with a caliper and explains; the younger "
        "man nods and watches carefully, learning. The frame stays still and keeps its shape."),
 "09r": (f"{F4}/c09.jpg", None,
         "The man with glasses slides his fingertips along the plain steel straightedge lying flat on the machined top plate, "
         "checking the flatness. His face is alive: he blinks naturally, his eyes follow his fingers, then he gives a small "
         "satisfied nod. Slow push-in."),
 "10": (f"{F4}/c10.jpg", None,
        "The white-haired advisor finishes drawing with the pencil, rolls up the drawing and hands it with a warm smile to the "
        "younger designer, who receives it happily. His thick white hair stays the same throughout."),
 "11": (f"{F4}/c11.jpg", None,
        "The white-haired designer points at the hand-drawn drawing and the smiling designer compares it with the tablet; they "
        "nod and smile at each other. The factory behind them stays calm; the camera slowly pushes in."),
 "24r": (f"{F4}/c24.jpg", None,
         "The quality manager touches the probe in his hand to several points on the machined top plate of the steel frame, "
         "slowly and carefully. The tripod camera stays completely still and nothing moves by itself."),
 "31r": (f"{F4}/c31.jpg", None,
         "Morning meeting in the office: the president speaks with calm, confident gestures; the employees listen, nod and "
         "smile. Everyone stays in place; the camera slowly pans across the group."),
 "37r": (f"{F4}/c37.jpg", None,
         "The worker on the forklift slowly lifts the bundle of steel bars off the truck bed with the forks and backs away "
         "carefully toward the shutter; the other people stand clear, watch and bow to the delivery man. Nobody carries "
         "anything by hand."),
})

# 10/5 事務所の写真で描き直した 14・33
JOBS.update({
 "14": (f"{F4}/c14.jpg", None,
        "The smiling designer with glasses works on the CAD drawing on his monitors, moves the mouse, then leans back slightly "
        "and smiles with satisfaction. The colleagues behind him keep working quietly. Slow push-in."),
 "33r": (f"{F4}/c33.jpg", None,
         "The petite vice president sits at her desk on the right below the hanging signboards, turned toward the automatic "
         "entrance door on the left; she watches over the office and her colleagues with a warm, gentle smile. The camera "
         "slowly moves a little closer to her. Nobody else moves position."),
})

# 10/5 会社で作っているガラス切断装置（約 9 m）の除幕
JOBS.update({
 "17g": (f"{F4}/c17g.jpg", None,
         "The two men pull the light-grey cover cloth off the big glass-cutting machine; the cloth slides down slowly and stays "
         "low, never lifting into the air. Then the carriage with the round saw blade glides smoothly along the long horizontal "
         "beam from right to left while the blade spins, just like a test run, and the two men smile proudly. The machine's frame "
         "never changes shape; no parts appear or grow."),
})

# 10/5 夕：加工品の統一・10 の設計者・17 のお披露目・47 ものづくりの未来（最初のコマは frames/fix5）
F5 = "frames/fix5"
JOBS.update({
 "10b": (f"{F5}/c10.jpg", None,
         "The white-haired advisor hands the rolled drawing to the slim smiling designer with glasses, who receives it happily; "
         "they nod and smile at each other. Both men keep exactly the same faces, hair and glasses. The camera stays still."),
 "17b": (f"{F5}/c17a.jpg", f"{F5}/c17b_end.jpg",
         "The unveiling: the two men pull the huge cover cloth off together in one big sweep; it slides down and away to the "
         "floor, revealing the whole glass-cutting machine. The camera stays still; the machine's shape never changes."),
 "47b": (f"{F5}/c47.jpg", None,
         "Morning light grows brighter through the high windows; everyone looks toward the light with hopeful, determined "
         "faces; the camera slowly pulls back and rises a little. Nobody moves position; the machines and the product never "
         "change shape."),
 "07b": (f"{F5}/c07.jpg", None,
         "The milling cutter spins fast and steadily the whole time and slowly mills the flat machined top plate of the steel "
         "frame; fine chips curl away. The frame never changes shape. No sparks. The camera stays almost still."),
 "25b": (f"{F5}/c25.jpg", None,
         "The workers bow to see off the truck; the driver waves; the truck with the steel frame product under the clear sheet "
         "slowly starts to move. Nobody is on the truck bed. The camera stays still."),
 "41b": (f"{F5}/c41.jpg", None,
         "The white-haired man presses the buttons on the yellow pendant control box and the crane slowly lifts the steel frame "
         "product a little higher; both men stay clear of the load and watch. The load never moves over anyone. The camera "
         "stays still."),
 "43b": (f"{F5}/c43.jpg", None,
         "The advisor and the young newcomer look at the finished steel frame product together; the advisor points at the "
         "machined top plate and the newcomer nods with a proud smile. The camera slowly moves a little closer."),
 "48b": (f"{F5}/c48.jpg", None,
         "The president and the customer shake hands firmly and smile, then both look at the finished steel frame product "
         "beside them. The camera stays almost still."),
 "50b": (f"{F5}/c50.jpg", None,
         "The elderly driver smiles and waves from the cab as the white truck with the steel frame product under the clear "
         "sheet slowly pulls away; the workers bow. Nobody is on the truck bed at any time. The camera stays still."),
})

# 10/5 夕：カット 10 は平らな図面をそのまま手渡す（始まりと終わりのコマを指定）
JOBS.update({
 "10f": (f"{F5}/c10s.jpg", f"{F5}/c10e.jpg",
         "The white-haired advisor finishes the last line with the pencil, puts the pencil down, lifts the same large flat drawing "
         "sheet off the desk with both hands and hands it, still flat, to the smiling designer with glasses, who takes it by the "
         "other corners; they smile at each other. There is only one drawing sheet, it stays flat and keeps the same size the whole "
         "time; it is never rolled. The camera stays still."),
})

# 10/6 トラックを会社のトラック（銀色の平ボディ）に統一
JOBS.update({
 "25t": (f"{F5}/c25.jpg", None, JOBS["25b"][2] + " The truck is a silver flatbed truck and stays exactly the same."),
 "50t": (f"{F5}/c50.jpg", None, JOBS["50b"][2] + " The truck is a silver flatbed truck and stays exactly the same."),
})

# 10/6 図面をガラス切断装置の設計図に・装置を白に・トラック（最初のコマは frames/fix6）
F6 = "frames/fix6"
STILL = " The drawing stays flat and keeps exactly the same lines; the camera stays almost still."
JOBS.update({
 "25u": (f"{F6}/c25.jpg", None, JOBS["25b"][2] + " The truck, its lettering and the level load stay exactly the same."),
 "50u": (f"{F6}/c50.jpg", None, JOBS["50b"][2] + " The truck, its lettering and the level load stay exactly the same."),
 "03d": (f"{F6}/c03.jpg", None,
         "The white-haired craftsman hands the drawing of the machine to the vice president; she takes it carefully with both "
         "hands, they look at each other and smile warmly, and she nods." + STILL),
 "10d": (f"{F6}/c10s.jpg", f"{F6}/c10e.jpg",
         "The white-haired advisor finishes the last line with the pencil, puts the pencil down, lifts the single flat drawing "
         "sheet off the desk with both hands and hands it, still flat, to the smiling designer with glasses, who takes it by the "
         "other corners; they smile at each other. Only one sheet; it is never rolled." + STILL),
 "11d": (f"{F6}/c11.jpg", None,
         "The white-haired designer points at the machine drawing on the bench and the smiling designer compares it with the same "
         "drawing on his tablet; they nod and smile at each other." + STILL),
 "14d": (f"{F6}/c14.jpg", None,
         "The smiling designer with glasses works on the CAD model of the machine on his two monitors, moves the mouse, then "
         "leans back slightly and smiles. The colleagues behind him keep working quietly. The screens keep showing the same "
         "machine." + STILL),
 "16d": (f"{F6}/c16.jpg", None,
         "The three men lean over the machine drawing on the table, point at it and laugh together warmly." + STILL),
 "28d": (f"{F6}/c28.jpg", None,
         "The planner explains the machine sketch on the whiteboard with lively gestures; the two colleagues listen, nod and "
         "smile. The sketch on the whiteboard stays exactly the same." + STILL),
 "40d": (f"{F6}/c40.jpg", None,
         "The hand-drawn machine drawing slowly blends into the CAD model of the same machine on the screen; the older and the "
         "younger hands rest on the desk. The machine's shape stays exactly the same." + STILL),
 "17d": ("frames/fix5/c17a.jpg", f"{F6}/c17_end.jpg",
         "The unveiling: the two men pull the huge cover cloth off together in one big sweep; it slides down to the floor, "
         "revealing the whole white glass-cutting machine. The camera stays still; the machine's shape and white colour never "
         "change."),
 "47d": (f"{F6}/c47.jpg", None, JOBS["47b"][2] + " The machine stays white."),
})

MODEL = os.environ.get("VEO_MODEL", "veo-3.1-fast-generate-preview")  # 急ぐ日は標準版を指定する

# 10/6 図面の向きを基準の正面図にそろえた 1 枚目（frames/fix7）と、カット 37（すり抜けない・フォークに載せたまま）
F7 = "frames/fix7"
JOBS.update({
 "03e": (f"{F7}/c03.jpg", None, JOBS["03d"][2] + " The drawing on the sheet stays exactly the same and the same way up."),
 "10e": (f"{F7}/c10s.jpg", f"{F7}/c10e.jpg", JOBS["10d"][2] + " The drawing on the sheet stays exactly the same and the same way up."),
 "11e": (f"{F7}/c11.jpg", None, JOBS["11d"][2] + " The drawings stay exactly the same and the same way up."),
 "16e": (f"{F7}/c16.jpg", None, JOBS["16d"][2] + " The drawing on the paper stays exactly the same and the same way up."),
 "40e": (f"{F7}/c40.jpg", None, JOBS["40d"][2] + " The drawing stays exactly the same and the same way up."),
 "37e": ("frames/fix8/c37_a.jpg", None,
         "The forklift slowly rolls a short way forward, carrying the one bundle of steel bars that rests on its forks; the "
         "bundle stays on the forks the whole time and never touches or passes through anything. The white-haired man and the "
         "delivery man bow to each other; the others stand clear and watch. The camera stays still."),
})

# 10/6 カット 37 やり直し：フォークリフトは動かさず（最初と最後のコマを同じに）、人だけ動く
JOBS["37f"] = ("frames/fix8/c37_a.jpg", "frames/fix8/c37_a.jpg",
               "The forklift and the bundle of steel bars on its forks stay completely still in place the whole time; the "
               "driver keeps her hands on the wheel. Only the people move a little: the white-haired man and the delivery "
               "man bow to each other politely and straighten up again. Nobody new appears. The camera stays still.")

# 10/6 カット 21：ガラス切断装置の梁と支柱のつなぎ目のボルトを締める（組み立て途中）
JOBS["21a"] = ("frames/fix9/c21_A3.jpg", None,
               "The skilled assembler on the small work platform fits the long wrench onto a large bolt at the joint between "
               "the top beam and the white column and tightens it firmly with several strong pulls, then checks the joint "
               "with his hand and nods. The half-assembled machine, the parts on the pallets and the platform stay exactly "
               "the same shape and in place. Nobody else appears. The camera stays still.")

# 10/6 夜 カット 21：床に立ち、腰の高さで支柱のつなぎ目の M20 ナットを締める（frames/fix9/c21_p.jpg）
JOBS["21b"] = ("frames/fix9/c21_p.jpg", None,
               "The skilled assembler stands on the floor and tightens the hex nut on the white column with the spanner: "
               "several firm short pulls, re-seating the spanner on the same nut each time, then he moves the spanner to "
               "the next nut in the row below and gives it a pull. The spanner and the nuts keep the same size; the machine, "
               "the parts on the pallets and everything else stay exactly the same shape and in place. Nobody else "
               "appears. The camera stays still.")

# 10/6 夜：3（約 50 歳の職人が溶接 → 副社長へ A3 の図面）、4（1990 年代）、22（ベトナム人の新人が溶接）、45（社長の顔）
SAME = " Every person keeps exactly the same face, hair, age and clothes the whole time; nobody new appears. The camera stays still."
F10 = "frames/fix10"
JOBS.update({
 "03w": (f"{F10}/c03w.jpg", None,
         "The craftsman welds the joint of the steel frame steadily, moving the torch slowly along the seam with a bright "
         "blue-white arc and a few small sparks; the steel frame and the table stay exactly the same shape." + SAME),
 "03h": (f"{F10}/c03h.jpg", None,
         "The craftsman hands the A3 drawing sheet to the vice president; she takes it carefully with both hands, they "
         "look at each other and smile warmly, and she nods. The sheet stays the same size and flat." + SAME),
 "04n": (f"{F10}/c04_1990.jpg", None,
         "The three 1990s craftsmen work calmly together at the NC lathe: one measures the part, one adjusts the handle, "
         "one watches closely; small, natural movements. The lathe stays exactly the same shape." + SAME),
 "22v": (f"{F10}/c22.jpg", f"{F10}/c22_end.jpg",
         "The young welder finishes the weld with a steady hand, the arc goes out, he flips his welding face shield up "
         "and smiles with relief at the senior beside him, who nods with approval. The steel frame stays the same shape."
         + SAME),
 "45v": (f"{F10}/c45.jpg", None,
         "The employees stand together and look ahead into the bright warm light with hopeful, determined faces; the "
         "president in front lifts his chin slightly with a confident look; hair and clothes move gently in a soft breeze."
         + SAME),
})

# 10/6 夜：社長の顔をそろえた 31・48
JOBS.update({
 "31p": ("frames/fix10/p31.jpg", None,
         "Morning meeting in the office: the president speaks with calm, confident gestures; the employees listen, nod and "
         "smile. Everyone stays in place." + SAME),
 "48p": ("frames/fix10/p48.jpg", None,
         "The president and the customer shake hands firmly and smile, then both look at the finished steel frame product "
         "beside them; the product stays exactly the same shape." + SAME),
})

# 10/7 カット 2：1948 年の町工場、職人の手元だけ（顔は出さない）。ノミとハンマーで石を削る（編集で白黒に）
JOBS["02s"] = ("frames/fix12/c02_b.jpg", None,
               "The craftsman's hands strike the steel chisel with the hammer several times in a steady rhythm, small stone "
               "chips fly off and a little dust rises; between strikes he shifts the chisel slightly along the stone. Only "
               "the hands and sleeves are visible, never a face; nobody else appears. The stone block, the workbench and the "
               "old lathe in the background keep exactly the same shape. The camera stays still.")

# 10/7 カット 4 の 1990 年代：こぢんまりしたトタン張りの町工場（frames/fix10/c04_1990_e.jpg）
JOBS["04e"] = ("frames/fix10/c04_1990_e.jpg", None,
               "The three 1990s craftsmen work calmly together at the lathe: one measures the part with the micrometer, one "
               "adjusts the handle, the woman watches closely; small, natural movements. The lathe and the workshop stay "
               "exactly the same shape." + SAME)

# 10/7 カット 4 をカット 3 に合わせた描き方で、2 場面とも自然に作業し続ける動画に
NATURAL = (" Natural, continuous, unhurried real working movements like a documentary shot: hands keep working the whole "
           "time, small head turns and glances, breathing; nobody stops to pose, stands up straight or looks at the camera.")
JOBS.update({
 "04r": ("frames/fix10/c04_90r.jpg", None,
         "The three 1990s craftsmen keep working at the lathe: the man with glasses carefully adjusts the tool post with "
         "a small wrench, the young man in the middle measures the part with the micrometer and reads it, the woman leans "
         "in and watches, then points at the part." + NATURAL + " The lathe and the workshop stay exactly the same shape." + SAME),
 "04t": ("frames/fix10/c04_nowr.jpg", None,
         "The three employees keep working at the lathe: the man with glasses checks the part with the digital gauge, the "
         "young man in the middle measures with the micrometer, the woman turns the handle of the lathe slowly and "
         "glances at the reading." + NATURAL + " The lathe and the factory stay exactly the same shape." + SAME),
})

# 10/7 カット 4：参考動画の動き（小さくゆっくりした自然な動き、カメラはゆっくり寄るだけ）に合わせる
GENTLE = (" Very calm and gentle like a quiet anime film: small, slow, natural movements only, no sudden or big motions, "
          "nobody stands up, poses or looks at the camera; the camera very slowly pushes in a little.")
JOBS.update({
 "04s": ("frames/fix10/c04_90r.jpg", None,
         "The three 1990s craftsmen keep working at the lathe: the man with glasses slowly turns the small wrench on the "
         "tool post, the young man in the middle carefully reads the micrometer, the woman leans in and watches quietly."
         + GENTLE + " The lathe and the workshop stay exactly the same shape." + SAME.replace(" The camera stays still.", "")),
 "04o": ("frames/fix10/c04_now_p.jpg", None,
         "In the office the three employees quietly discuss the drawing on the table: the man with glasses slowly traces a "
         "line on the drawing with his pen while explaining, the man in the middle thinks with his hand on his chin and "
         "nods slowly, the woman tilts her head and smiles a little." + GENTLE +
         " The table, the drawing sheet and the office stay exactly the same shape and size." + SAME.replace(" The camera stays still.", "")),
})

# 10/7 カット 4 再挑戦：参考動画と同じ作り方（カメラ完全固定・動きは手元と表情だけ）。1 場面 2 本ずつ作って数値で選ぶ
LOCKED = (" Locked-off static camera on a tripod: no zoom, no pan, no push-in, the frame never moves. Only tiny, slow, "
          "natural movements of hands and faces (a hand moving a little, a blink, a small nod, breathing); bodies stay in "
          "place; nobody stands up, poses or looks at the camera. Calm, quiet anime film.")
for k in ("a", "b"):
    JOBS[f"04x{k}"] = ("frames/fix10/c04_90r.jpg", None,
        "The three 1990s craftsmen work quietly at the lathe: the man with glasses slowly turns the small wrench on the tool "
        "post, the young man carefully reads the micrometer, the woman watches." + LOCKED +
        " The lathe and the workshop keep exactly the same shape. Every person keeps the same face, hair, cap and clothes; nobody new appears.")
    JOBS[f"04y{k}"] = ("frames/fix10/c04_now_p.jpg", None,
        "The three employees quietly discuss the drawing on the table: the man with glasses slowly moves his pen along a "
        "line of the drawing, the man in the middle keeps his hand on his chin and nods slightly, the woman listens and "
        "smiles a little." + LOCKED +
        " The table, the drawing sheet and the office keep exactly the same shape and size. Every person keeps the same face, hair and navy uniform; nobody new appears.")

# 10/7 新しい設定表の顔（社長・品質課の課長・先代社長の奥さん）にそろえた 23・24・27・32・49。カメラ固定・小さな動き
F13 = "frames/fix13"
KEEPF = " The machines, tables and room keep exactly the same shape. Every person keeps the same face, hair and clothes; nobody new appears."
JOBS.update({
 "23n": (f"{F13}/c23.jpg", None, "In the meeting the client in the suit explains with a gentle open-hand gesture, the president "
         "behind the table nods slowly, the smiling concept designer adds a few lines to the drawing with his pen." + LOCKED + KEEPF),
 "24n": (f"{F13}/c24.jpg", None, "The quality control section chief kneels and slowly touches the probe to a few points on the "
         "machined top plate, carefully checking; the tripod stays still." + LOCKED + KEEPF),
 "27n": (f"{F13}/c27.jpg", None, "The employees in front of the big white gantry machine applaud warmly with smiles; the "
         "president in the middle claps and smiles; the machine stays still." + LOCKED + KEEPF),
 "32n": (f"{F13}/c32.jpg", None, "Lunch break: the employees eat their bento and laugh together; the young man in front tells "
         "a story with a small hand gesture, the founder's wife laughs, the woman on the right smiles and listens." + LOCKED + KEEPF),
 "49n": (f"{F13}/c49.jpg", None, "At the end of the work day the employees stand together and wave gently at the camera with "
         "warm smiles." + LOCKED.replace("looks at the camera", "moves from their place") + KEEPF),
})

# 10/7 カット 47：社長・副社長を真ん中に（frames/fix13/c47.jpg）
JOBS["47n"] = ("frames/fix13/c47.jpg", None,
               "Everyone applauds warmly with smiles around the finished product and the white glass-cutting machine; the "
               "president and the vice president in the center clap and smile at each other." + LOCKED + KEEPF)

# 10/7 カット 7：実際の加工動画を元にした絵（frames/fix14/c07.jpg）。カメラ固定、主軸が削り進む
for k in ("a", "b"):
    JOBS[f"07r{k}"] = ("frames/fix14/c07.jpg", None,
        "Inside the huge gantry machining center the spindle head rotates and slowly mills the top of the large welded "
        "steel frame, moving a little along the cross rail; a fine coolant mist sprays at the cutting point and a few small "
        "metal chips fly off and land near it. The workpiece, its pockets, the machine and the covers keep exactly the same "
        "shape and position; no chip conveyor appears; no people. Locked-off static camera: no zoom, no pan. Calm, steady.")

# 10/7 カット 7 やり直し：始めと終わりを同じ絵にして機械の形・位置を固定。動くのは回転・霧・少しの切りくずだけ
for k in ("c", "d"):
    JOBS[f"07r{k}"] = ("frames/fix14/c07.jpg", "frames/fix14/c07.jpg",
        "The spindle stays in the same place and keeps rotating, cutting the top of the steel frame: a fine coolant mist "
        "sprays and swirls at the cutting point and a few tiny metal chips flick off. Nothing else moves: the spindle head, "
        "the cross rail, the machine covers, the panels, the workpiece and its pockets keep exactly the same shape and "
        "position the whole time; no new parts or panels appear; no people. Locked-off static camera.")

# 10/7 カット 7 再：ミストではなく、実際の動画のように切削液（液体）が刃に当たって低く跳ね、削り屑が少し横に飛ぶ（飛び散らせすぎない）
for k in ("e", "f"):
    JOBS[f"07r{k}"] = ("frames/fix14/c07.jpg", "frames/fix14/c07.jpg",
        "Calm, realistic milling. The cutter on the spindle keeps rotating in the same place, cutting the top of the steel "
        "frame. Thin streams of liquid cutting coolant (clear liquid, not mist, not smoke, not steam) jet onto the cutter and "
        "splash low and close along the metal surface; small curled metal chips are thrown a short distance sideways and land "
        "on the top of the frame. Keep it modest: no clouds, no big spray, nothing flying high into the air. Nothing else "
        "moves: the spindle head, the cross rail, the machine covers, the panels, the workpiece and its pockets keep exactly "
        "the same shape and position the whole time; no new parts or panels appear; no people. Locked-off static camera.")

def make(no):
    out = f"clips/cutg{no}.mp4"
    if os.path.exists(out):
        return f"skip {no}"
    first, last, motion = JOBS[no]
    inst = {"prompt": motion + " " + STYLE, "image": {"bytesBase64Encoded": b64(first), "mimeType": "image/jpeg"}}
    if last:
        inst["lastFrame"] = {"bytesBase64Encoded": b64(last), "mimeType": "image/jpeg"}
    try:
        op = call("POST", f"models/{MODEL}:predictLongRunning", {
            "instances": [inst], "parameters": {"aspectRatio": "16:9", "durationSeconds": 8}})
        while not op.get("done"):
            time.sleep(15); op = call("GET", op["name"])
        s = op.get("response", {}).get("generateVideoResponse", {}).get("generatedSamples")
        if not s:
            return f"FAIL {no} {str(op.get('error') or op.get('response'))[:160]}"
        req = urllib.request.Request(s[0]["video"]["uri"], headers={"x-goog-api-key": KEY})
        with urllib.request.urlopen(req) as r, open(out, "wb") as f:
            f.write(r.read())
        return f"ok {no}"
    except Exception as e:
        return f"FAIL {no} {str(e)[:160]}"

def join03(b="clips/cutg03b.mp4", out="clips/cutg03.mp4"):
    # カット 3 = 年を重ねる前半（1〜7 秒目を 1.25 倍速で 4.8 秒。速すぎると手の動きが不自然）＋ 図面を手渡す後半（3.5 秒）。edit.py は 8 秒のクリップを前提に中ほどを使うので、合わせて 8 秒にする
    import subprocess
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "clips/cutg03a.mp4", "-i", b, "-filter_complex",
                    "[0]trim=1:7,setpts=(PTS-STARTPTS)/1.25,scale=1280:720,fps=24,format=yuv420p[a];"
                    "[1]trim=1.5:5.0,setpts=PTS-STARTPTS,scale=1280:720,fps=24,format=yuv420p[b];"
                    "[a][b]xfade=transition=fade:duration=0.3:offset=4.5[v]",
                    "-map", "[v]", "-an", "-c:v", "libx264", "-crf", "16", out], check=True)

if __name__ == "__main__":
    nos = sys.argv[1:] or list(JOBS)
    with ThreadPoolExecutor(3) as ex:
        for m in ex.map(make, nos):
            print(m, flush=True)
    if os.path.exists("clips/cutg03a.mp4") and os.path.exists("clips/cutg03b.mp4"):
        join03(); print("joined 03")
