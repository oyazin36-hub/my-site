# 原マシナリー MV カット表（https://claude.ai/artifact/WybVC5PDPJGPL1YyEDS6hK）の全 41 カット
# refs: refs/ の参照画像, frame: 開始フレームに使う前カット
# 参考動画を流用する予定だった 01・02・08・26・29 も、参考動画が手元にないため生成する
CUTS = [
 dict(no="01", refs=[],
      prompt="Slow push-in from space toward Earth, approaching the Japanese archipelago, soft clouds drifting."),
 dict(no="02", refs=["okazaki"],
      prompt="Aerial descent over the city of Okazaki at dawn, morning mist over the Yahagi River, sunlight touching factory rooftops."),
 dict(no="03", refs=["c1948", "old_shop"],
      prompt="Medium shot. A young craftsman carefully wipes and adjusts an old machine in a small workshop, dust in the slanted window light. Sepia tones."),
 dict(no="04", frame="03",
      prompt="Same composition as the previous shot, now in the present day in full color. An elderly craftsman with swept-back grey hair in a navy work jacket stands in the same spot and gently picks up an old photograph, smiling softly."),
 dict(no="05", refs=["veteran", "factory_real"],
      prompt="Slow dolly back revealing a bright, spacious modern factory around the elderly craftsman; colleagues working in the background."),
 dict(no="06", refs=[], done=True,
      prompt="(生成済み)"),
 dict(no="07", refs=["operator"],
      prompt="Close-up. A young operator measures a polished metal part with a micrometer, focused eyes, then a macro shot of his fingertips adjusting the dial."),
 dict(no="08", refs=["veteran", "designer"],
      prompt="The elderly craftsman draws a blueprint with a pencil at a wooden drafting table, then rolls it up and hands it to the young woman designer with round glasses, who receives it with both hands and smiles."),
 dict(no="09", refs=["veteran", "designer"],
      prompt="Two-shot at a workbench. The elderly craftsman unrolls an old hand-drawn blueprint; the young designer holds a tablet showing the same part in CAD. They compare and nod to each other."),
 dict(no="10", refs=["factory_real"],
      prompt="Inside the factory at dawn, the large shutter door rises and golden morning light floods in across the floor, camera slowly pushing forward."),
 dict(no="11", refs=["operator", "factory_real"],
      prompt="Close-up profile of a young operator pressing buttons on a machine control panel, determined expression, rim light."),
 dict(no="12", refs=["designer", "office"],
      prompt="Over-the-shoulder shot of a young designer working in CAD; lines on the monitor assemble into a 3D machine part."),
 dict(no="13", refs=["factory_real"],
      prompt="Dramatic low-angle shot slowly tilting up the full height of a huge gantry-type machining center in a bright factory. The machine stands still."),
 dict(no="14", refs=["veteran", "mid", "designer"],
      prompt="A small team gathered around a large blueprint on a table, pointing and laughing together, warm window light."),
 dict(no="15", refs=["mid", "designer", "operator"],
      prompt="Back view of employees walking together toward a wide-open factory door filled with bright light, camera following low."),
 dict(no="16", refs=["factory_real"],
      prompt="Quiet empty factory at sunset; warm light reflects off the polished metal surfaces of the machines, slow lateral pan."),
 dict(no="17", refs=[],
      prompt="Macro tracking shot along a workbench where a silicon ingot, a clear sapphire block, a glass plate and a milky quartz piece are lined up, glowing in window light."),
 dict(no="18", refs=["mid", "operator"],
      prompt="Close-up of hands assembling a special-purpose machine, tightening bolts with a torque wrench, then a medium shot of two engineers working together."),
 dict(no="19", refs=["designer", "operator"],
      prompt="The young designer and the young operator stand in front of a finished machine, exchange a nod and a small smile."),
 dict(no="20", refs=["designer"],
      prompt="A clean inspection room; a coordinate measuring machine probe touches a metal part while the young designer records the results on a clipboard."),
 dict(no="21", refs=["mid"],
      prompt="A carefully wrapped machine part is loaded onto a truck; the engineer bows politely as the truck departs in the afternoon light."),
 dict(no="22", refs=["veteran", "newbie"],
      prompt="Close-up: an elderly craftsman places his hand over the hand of an eighteen-year-old new recruit in a brand-new uniform, guiding how to hold a precision tool."),
 dict(no="23", refs=["welder", "newbie", "inspector"],
      prompt="A new machine powers on with its indicator lights; employees around it applaud and smile."),
 dict(no="24", refs=["designer", "sales", "mid"],
      prompt="The young designer explains a sketch on a whiteboard to colleagues who nod with interest."),
 dict(no="25", refs=["okazaki"],
      prompt="Wide shot at golden hour overlooking the city of Okazaki from a hill, a factory roof in the foreground."),
 dict(no="26", refs=[],
      prompt="Camera rises from a Japanese city at golden hour up through the clouds into space, pulling back to reveal the whole Earth."),
 dict(no="27", refs=["inspector", "newbie", "sales"],
      prompt="Morning assembly on the high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor), machines lined up behind: employees stand in a row, listening and looking ahead, soft morning light."),
 dict(no="28", refs=["welder", "newbie", "inspector"],
      prompt="Lunch break: employees laughing together while eating bento boxes at a long table, relaxed and warm."),
 dict(no="29", refs=["designer", "office"],
      prompt="The young designer by the office window turns toward the camera and smiles warmly, sunlight on her face."),
 dict(no="30", refs=["factory_real"],
      prompt="Exterior of the factory at dusk, windows lighting up one by one, sky turning from orange to blue."),
 dict(no="31", refs=["c1948", "old_shop"],
      prompt="Sepia-toned close-up: a young craftsman's hands turn the handle of an old machine in a 1940s workshop."),
 dict(no="32", frame="31",
      prompt="Same composition in full color, present day: a young operator's hands in a navy work uniform operate the control panel of a modern machine."),
 dict(no="33", refs=["veteran", "designer"],
      prompt="A pencil-drawn blueprint slowly dissolves into the same design on a CAD screen, two hands, old and young, resting side by side."),
 dict(no="34", refs=["factory_real"],
      prompt="A massive machined steel part is slowly lifted by an overhead crane, workers guiding it, camera tilting up with it."),
 dict(no="35", refs=["veteran", "inspector", "newbie"],
      prompt="All employees gathered in front of the factory, smiling; the camera pulls back and rises to reveal the whole group."),
 dict(no="36", refs=["veteran", "designer"],
      prompt="The elderly craftsman and the young designer stand side by side looking up at a finished machine, light on their faces."),
 dict(no="37", refs=["factory_real"],
      prompt="Rising aerial shot of the factory at sunrise, long shadows, birds crossing the sky."),
 dict(no="38", refs=["welder", "sales", "newbie"],
      prompt="Employees look up toward bright light with determined smiles, wind moving their hair, camera slowly pushing in."),
 dict(no="39", refs=["factory_real"],
      prompt="Quiet factory exterior at dusk, warm and peaceful, gentle breeze."),
 dict(no="40", refs=[],
      prompt="Still-life on a wooden workbench: an old vernier caliper next to a modern digital measuring instrument, soft evening window light."),
 dict(no="41", refs=["okazaki"],
      prompt="Wide evening sky with soft clouds over Okazaki, calm and spacious."),
 # 曲に合わせて足したカット（カット表の時刻より実際の曲が長く歌う部分を埋める）
 dict(no="42", refs=["veteran", "factory_real"],
      prompt="Close-up: the elderly craftsman slowly runs his fingertip along a freshly machined, mirror-smooth metal surface, checking it against the light with a straightedge, utterly focused."),
 dict(no="43", refs=["mid", "welder", "factory_real"],
      prompt="A cover cloth is pulled off a newly finished special-purpose machine in the factory; the engineers look at it proudly."),
 dict(no="44", refs=["factory_real"],
      prompt="Exterior of a modern Japanese factory building in bright daylight, blue sky, camera slowly rising up the facade."),
 dict(no="45", refs=["sales", "mid", "factory_real"],
      prompt="In the factory, the salesman in a suit and the engineer show a finished machine to a visiting client in a suit; the client nods, impressed, and they shake hands."),
 dict(no="46", refs=["okazaki"],
      prompt="Night view: the camera rises from a lit-up factory to reveal the glowing city lights of Okazaki and the river under a starry sky."),
 dict(no="47", refs=[],
      prompt="Close-up of an old photo album on a wooden desk; a gentle breeze turns the pages of faded sepia photographs of a small 1940s machine workshop and its workers."),
 dict(no="48", refs=["factory_real"],
      prompt="Time-lapse of a bright factory from morning to evening: sunlight beams sweep across the floor, machines running, workers passing by as soft blurs."),
 dict(no="49", refs=[],
      prompt="Twilight sky slowly deepening from orange to deep blue, soft clouds drifting, the first stars appearing. Calm and spacious."),
]

# 実際の曲（song.mp3、4:35.8）に合わせたカット割り: (カット番号, 開始秒, 終了秒)
# 歌の時刻は Gemini で曲を書き起こして測った（song_transcript.json）
TIMELINE = [
 ("01", 0.0, 1.8), ("03", 1.8, 7.4), ("04", 7.4, 14.3), ("05", 14.3, 20.9), ("02", 20.9, 27.4), ("16", 27.4, 32.4),
 ("06", 32.4, 39.4), ("07", 39.4, 47.7), ("42", 47.7, 52.4), ("08", 52.4, 60.0),
 ("09", 60.0, 66.4), ("10", 66.4, 73.6),
 ("11", 73.6, 75.3), ("12", 75.3, 77.0), ("13", 77.0, 78.6), ("14", 78.6, 86.3), ("43", 86.3, 90.0),
 ("15", 90.0, 96.4), ("44", 96.4, 100.4),
 ("17", 100.4, 107.3), ("18", 107.3, 114.0), ("19", 114.0, 119.8), ("45", 119.8, 126.7),
 ("51", 126.7, 133.7), ("21", 133.7, 141.4),  # 品質課の課長の検査（カット 20 は使わない）
 ("22", 141.4, 148.7), ("23", 148.7, 154.5), ("24", 154.5, 158.2), ("25", 158.2, 161.2), ("26", 161.2, 168.8),
 ("27", 168.8, 175.7), ("28", 175.7, 178.8), ("29", 178.8, 183.9), ("30", 183.9, 189.9), ("46", 189.9, 195.9),
 ("47", 195.9, 202.9), ("48", 202.9, 209.8),
 ("31", 209.8, 213.3), ("32", 213.3, 216.9), ("33", 216.9, 222.8), ("34", 222.8, 226.7), ("35", 226.7, 233.3),
 ("36", 233.3, 236.8), ("37", 236.8, 241.3), ("38", 241.3, 247.4),
 ("39", 247.4, 253.9), ("40", 253.9, 258.9),
 # 「原マシナリー」の歌に合わせて、支えてくれる人たちを 2 秒ずつ見せる（お客様 → 仕入れ先様 → 運転手さん → 社員）
 ("45", 258.9, 260.9), ("48", 260.9, 262.9), ("21", 262.9, 264.9), ("35", 264.9, 266.9),
 ("50", 266.9, 275.8),
]

# 歌詞テロップ: (開始秒, 終了秒, 文字)
LYRICS = [
 (1.8, 4.6, "1948年"), (4.6, 7.4, "ここから始まった"), (7.4, 10.5, "受け継いだ技術"), (10.5, 14.3, "積み重ねた想い"),
 (14.3, 17.6, "時代が変わっても"), (17.6, 20.9, "変わらないものがある"), (20.9, 27.4, "ものづくりへの　情熱"),
 (32.4, 36.0, "鉄を削り　形を生み出す"), (36.0, 39.4, "大きな素材に　挑み続ける"), (39.4, 44.8, "一ミリ　一ミクロン"),
 (44.8, 47.7, "その先にある精度を追い"), (47.7, 52.4, "見えないところまで　妥協せず向き合う"),
 (52.4, 55.8, "技術は　人から人へ"), (55.8, 60.0, "想いは　未来へ"),
 (60.0, 63.0, "守るべき技術は　守り抜く"), (63.0, 66.4, "変えるべきものは　変えていく"),
 (66.4, 68.0, "昨日を超えて"), (68.0, 69.6, "今日を超えて"), (69.6, 73.6, "まだ見ぬ未来へ"),
 (73.6, 75.3, "技術力"), (75.3, 77.0, "設計力"), (77.0, 78.6, "設備力"), (78.6, 80.3, "人間力"),
 (80.3, 86.3, "すべての力を　ひとつにして"), (86.3, 90.0, "まだない価値を　創り出せ"),
 (90.0, 91.5, "この手で"), (91.5, 92.9, "この技術で"), (92.9, 96.4, "未来を　切り拓け"), (96.4, 100.4, "原マシナリー"),
 (100.4, 103.7, "難しい素材も　不可能じゃない"), (103.7, 107.3, "シリコン　サファイア　ガラス　石英"),
 (107.3, 110.8, "削る　磨く　組み上げる"), (110.8, 114.0, "一つひとつに　技術が宿る"),
 (114.0, 116.7, "設計から　加工まで"), (116.7, 119.8, "一貫して　応えていく"), (119.8, 126.7, "求められるものの　その先へ"),
 (126.7, 128.9, "品質を追い"), (128.9, 131.0, "コストに挑み"), (131.0, 133.7, "納期を守る"),
 (133.7, 135.5, "信頼は"), (135.5, 138.4, "一つひとつの仕事から"), (138.4, 141.4, "積み上げていく"),
 (141.4, 144.9, "技術力　設計力"), (144.9, 148.7, "設備力　人間力"), (148.7, 154.5, "受け継いだ力を　進化させ"),
 (154.5, 158.2, "次の時代を　創り出せ"), (158.2, 159.8, "この街から"), (159.8, 161.2, "世界へ"),
 (161.2, 164.4, "未来を　動かせ"), (164.4, 168.8, "原マシナリー"),
 (168.8, 172.5, "変化を恐れない"), (172.5, 175.7, "挑戦を止めない"), (175.7, 177.3, "人がいる"), (177.3, 178.8, "技術がある"),
 (178.8, 181.5, "仲間がいる"), (181.5, 183.9, "だから　できる"),
 (183.9, 186.9, "一つの会社から"), (186.9, 189.9, "一つの技術から"), (189.9, 195.9, "世界の未来へ"),
 (209.8, 213.3, "技術力　設計力"), (213.3, 216.9, "設備力　人間力"), (216.9, 222.8, "四つの力を　ひとつにして"),
 (222.8, 226.7, "新しい時代を　切り拓け"), (226.7, 230.1, "1948年から"), (230.1, 233.3, "受け継いだ　ものづくり"),
 (233.3, 235.2, "100年企業へ"), (235.2, 236.8, "その先へ"), (236.8, 239.2, "まだ見ぬ未来を"), (239.2, 241.3, "この手で創る"),
 (241.3, 242.7, "技術で"), (242.7, 244.2, "未来を"), (244.2, 245.8, "切り拓け"), (245.8, 247.4, "原マシナリー！"),
 (247.4, 250.7, "受け継ぐ技術"), (250.7, 253.9, "挑み続ける心"), (253.9, 258.9, "ものづくりの未来へ"),
]

# 左上の年号・地名: (開始秒, 終了秒, 文字)
TAGS = [(2.1, 7.1, "1948"), (7.7, 14.0, "2026"), (21.2, 27.1, "岡崎"), (158.4, 161.0, "岡崎"), (210.1, 213.0, "1948"),
        (213.6, 216.6, "2026"), (233.6, 236.5, "2048")]

# 最後の社名（ロゴの代わり）の表示開始秒
LOGO_AT = 268.0

# 社員の皆さんで作り直すカット（架空の人物から差し替え）。ここにある番号は CUTS の同じ番号を上書きする
RECAST = {
 "10": (["factory_real"], "Inside this high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor) at dawn, the large shutter door at the end rises and golden morning light floods in across the grey concrete floor, camera slowly pushing forward."),
 "13": (["factory_real"], "Dramatic low-angle shot slowly tilting up the full height of a huge gantry-type machining center in this high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor). The machine stands still."),
 "16": (["factory_real"], "This high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows), quiet and empty at sunset; warm light pours through the high windows onto the grey concrete floor and the polished surfaces of the machined steel plates, slow lateral pan."),
 # 実際の工場の外観（refs/exterior.jpg、写真 refs/photo_exterior.jpg から作成）に合わせる
 "30": (["exterior"], "Exterior of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind) at dusk, windows lighting up one by one, sky turning from orange to blue."),
 "37": (["exterior"], "Rising aerial shot of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind) at sunrise, long shadows, birds crossing the sky."),
 "39": (["exterior"], "This factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind) at dusk, quiet, warm and peaceful, the pine trees swaying gently in the breeze."),
 "44": (["exterior"], "This factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind) in bright daylight under a blue sky, camera slowly rising up the facade."),
 "04": (["part_okami", "factory_real"], "In the bright present-day factory, the late founder's elderly wife with soft brown hair gently picks up an old sepia photograph of the 1948 workshop and smiles softly."),
 "05": (["adv_all", "factory_real"], "Slow dolly back from the dignified senior advisor in his seventies, revealing a bright, spacious modern factory around him; colleagues working in the background."),
 "07": (["machinist", "new_viet", "big_part"], "Close-up. The slim master machinist with glasses measures a huge flat precision-machined steel plate several meters long, with a mirror-like milled surface, machined pockets, T-slots and bolt holes, lying on the grey concrete factory floor, with a micrometer while the Vietnamese recruit from the large-part machining team watches closely and learns."),
 "08": (["adv_slim", "des_smile"], "The slim elderly advisor draws a machine design with a pencil at a wooden drafting table, then hands the rolled drawing to the smiling designer with glasses (a slim MAN in his fifties with black hair, not a woman), who receives it with both hands."),
 "09": (["des_white", "des_smile"], "Two-shot at a workbench. The white-haired senior designer unrolls an old hand-drawn blueprint; the smiling designer with glasses holds a tablet showing the same part in CAD. They compare and nod."),
 "11": (["machinist", "factory_real"], "Close-up profile of the slim master machinist with glasses pressing buttons on a machine control panel, determined expression, rim light."),
 "12": (["des_smile", "office"], "Over-the-shoulder shot of the smiling designer with glasses working in CAD; lines on the monitor assemble into a 3D machine part."),
 "14": (["des_white", "assembler", "des_smile"], "Three men (the white-haired senior designer, the bearded master assembler and the slim smiling designer with glasses, a man in his fifties) gathered around a large blueprint on a table, pointing and laughing together, warm window light. No women in the foreground."),
 "15": (["president", "vp", "new_viet"], "Back view of employees walking together toward a wide-open factory door filled with bright light, camera following low."),
 "18": (["assembler", "factory_real"], "Medium shot: the bearded master assembler carefully tightens bolts with a torque wrench while assembling a large special-purpose machine on the factory floor."),
 "19": (["des_smile", "assembler"], "The smiling designer with glasses and the bearded master assembler stand in front of a finished machine, exchange a nod and a small smile."),
 "20": (["insp_woman", "new_glasses", "cmm_device"], "On the grey concrete floor of this high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor), the short-haired woman inspector sweeps the handheld laser scan probe (green marker LEDs, fan of blue laser light) over a large precision-machined steel plate, while the new inspector with glasses checks the colorful 3D deviation map on a tablet; a white tracking camera on a black tripod stands nearby."),
 "21": (["driver", "president", "exterior"], "In front of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind), closer view on the paved yard directly at the large open yellow roll-up shutter (the shutter fills the background, the stone wall is NOT between the truck and the shutter): the rear of a 3-ton flatbed truck is backed up to the shutter opening and a carefully wrapped machined metal part is lifted out of the factory onto it, the small smiling elderly driver helping; he waves from the driver's seat as the president and the petite vice president bow politely, afternoon light."),
 "22": (["adv_big", "new_shy"], "Close-up: the elderly machining advisor places his weathered hand over the hand of a shy young recruit, guiding how to hold a precision tool."),
 "23": (["assembler", "new_viet", "part_pony"], "A new machine powers on with its indicator lights; employees around it applaud and smile, the Vietnamese recruit cheering happily."),
 "24": (["concept", "des_smile", "des_white"], "The cheerful, slightly plump elderly concept designer (clean-shaven, no beard) explains a whiteboard sketch of a special-purpose industrial machine (mechanical parts only, not a building; the whiteboard has drawings only, absolutely no words, labels or letters) to the smiling designer and the white-haired senior designer, who nod with interest."),
 "27": (["president", "vp", "clerk"], "Morning assembly on the high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor), machines lined up behind: the president speaks to exactly twenty employees (count them: a small company of twenty-one people, never more) standing in one short row, the vice president beside him, everyone listening, soft morning light."),
 "28": (["new_viet", "part_okami", "part_pony"], "Lunch break: employees laughing together while eating bento boxes at a long table; the talkative Vietnamese recruit tells a story, relaxed and warm."),
 "29": (["vp", "office"], "The petite vice president (short dark brown bob, NO glasses) by the office window turns toward the camera and smiles warmly and brightly, sunlight on her face."),
 "32": (["machinist", "factory_real"], "Close-up in full color, present day: the master machinist's hands operate the control panel of a modern machine."),
 "33": (["adv_slim", "des_smile"], "A pencil-drawn mechanical drawing of a machine part (gears, shafts and brackets, not a building) slowly dissolves into the same 3D machine part on a CAD screen; an old hand and a young hand rest side by side on the desk."),
 "34": (["adv_big", "new_pony_m", "big_part"], "A huge flat precision-machined steel plate several meters long, with a mirror-like milled surface, machined pockets, T-slots and bolt holes is slowly lifted by an overhead crane, the elderly advisor and a worker guiding it, camera tilting up with it."),
 "35": (["president", "vp", "exterior"], "All twenty-one employees of a small company gathered in front of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind), smiling, the president and vice president in the center; the camera pulls back and rises to reveal the whole group."),
 "36": (["adv_big", "new_shy", "big_part"], "The elderly large-part machining advisor and the shy young recruit from his team stand side by side on the grey concrete factory floor, looking proudly at a huge flat precision-machined steel plate several meters long, with a mirror-like milled surface, machined pockets, T-slots and bolt holes they just finished, light on their faces."),
 "38": (["new_viet", "insp_woman", "clerk"], "Employees look up toward bright light with determined smiles, wind moving their hair, camera slowly pushing in."),
 "42": (["new_glasses", "big_part"], "Close-up: the inspector with glasses in the navy company uniform slowly runs his fingertip along the mirror-smooth surface of a huge flat precision-machined steel plate several meters long, with a mirror-like milled surface, machined pockets, T-slots and bolt holes, checking it against the light with a straightedge, utterly focused."),
 "43": (["assembler", "des_smile", "factory_real"], "A cover cloth is pulled off a newly finished special-purpose machine in the factory; the bearded assembler and the designer look at it proudly."),
 "45": (["concept", "president", "office"], "In a meeting room, a client in a suit explains their needs while the cheerful elderly concept designer listens with a big smile and quickly sketches a machine idea; the president nods; the client leans in, delighted."),
 # お客様・仕入れ先様
 "50": (["president", "driver", "exterior"], "At golden hour in front of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind), the company's employees stand together with their customers in suits and partner suppliers in work clothes, a plain unbranded 3-ton truck (no brand name or emblem) parked nearby; they smile and look up at the sky as the camera slowly rises toward the evening sky."),
 # 品質課の課長が三次元測定機で完成品を検査する（「品質を追い」）
 "51": (["qc_chief", "cmm_device", "big_part"], "On the grey concrete floor of this high-ceilinged machining hall (orange-brown roof beams on yellow columns, high windows, grey concrete floor), the quality control section chief kneels beside a huge finished precision-machined steel plate and touches its edge with the black handheld touch probe (green glowing marker LEDs, red ruby stylus tip); a white tracking camera head on a black tripod stands a few meters away, with faint pink tracking light beams connecting it to the probe. He watches closely with a serious, satisfied expression. The chief has short jet-black hair. One single continuous shot, not comic panels."),
 "48": (["adv_big", "machinist", "exterior"], "Early morning in front of this factory building exactly as in the reference (long white two-story building with a blue band and red stripe along the top and the company emblem, light-yellow roll-up shutter under a canopy, white office wing on the right, a stone lantern and round trimmed shrubs in front, a natural stone retaining wall, wooded hill behind): closer view on the paved yard directly at the large open yellow roll-up shutter (the shutter fills the background, the stone wall is NOT between the truck and the shutter): the rear of a partner supplier's flatbed truck is backed up to the shutter opening and large steel plates are being unloaded into the factory; the supplier's driver in a green uniform and cap bows, and the factory's elderly advisor, machinist and the friendly fifty-something male recruit with long black hair in a ponytail greet him with bows and smiles, checking the material together."),
}
CUTS.append(dict(no="50", refs=[], prompt=""))
CUTS.append(dict(no="51", refs=[], prompt=""))
for _c in CUTS:
    if _c["no"] in RECAST:
        _c["refs"], _c["prompt"] = RECAST[_c["no"]]
        _c.pop("frame", None)

# 最後の社名の下に出す感謝の一文: (開始秒, 終了秒, 文字)
ENDNOTE = None  # 感謝は文字ではなく映像（カット 45・48・21・35・50）で表す

# 全カット共通の決まり（社員の服装と床）
from staff import STAFF as _STAFF
UNIFORM_NOTE = " Every company employee in the scene, including people in the background, wears the identical navy blue work jacket and navy work trousers."
FLOOR_NOTE = " The factory floor is grey concrete, not green."
for _c in CUTS:
    _r = set(_c.get("refs", []))
    if _r & set(_STAFF) or "employees" in _c.get("prompt", ""):
        _c["prompt"] += UNIFORM_NOTE
    if "big_part" in _r:
        _c["prompt"] += FLOOR_NOTE

# 使わなくなったカットは生成しない
for _c in CUTS:
    if _c["no"] in {"20"}:
        _c["done"] = True

# 工場内の大きさの決まり（人に対して設備を大きく）
SCALE_NOTE = (" Realistic industrial scale: the factory hall is huge with a ceiling about 15 meters high; the large machining centers and"
              " gantry machines are 4 to 6 meters tall, towering over the workers; people look small next to the machines.")
for _c in CUTS:
    _r = set(_c.get("refs", []))
    if _r & {"factory_real", "big_part", "cmm_device"} or "machining hall" in _c.get("prompt", ""):
        _c["prompt"] += SCALE_NOTE

# 全カット共通: 1 枚の連続した画面、機械にメーカー名やロゴを描かない
for _c in CUTS:
    _c["prompt"] += " One single continuous shot (never split into comic panels). No maker names, brand names or logos on any machine."

# 工場内の色の決まり（大きさを変えても色は変えない）
COLOR_NOTE = (" Keep the factory colors exactly as in the reference: green radial drills and green machines, cream-white machining centers,"
              " orange-brown roof beams, yellow columns, beige walls, grey concrete floor, warm daylight.")
for _c in CUTS:
    if "towering" in _c["prompt"]:
        _c["prompt"] += COLOR_NOTE

# 完成版を見て不自然だった場面の直し（10/3）: CUTS の prompt を上書きする（共通の決まりより前に入れ直す）
FIX = {
 "43": "Unveiling moment: the bearded master assembler and the smiling designer with glasses pull a large light-grey cover cloth off a brand-new, modern cream-white special-purpose machine; the cloth is caught mid-air sliding off the machine, both men look at the machine proudly with excited smiles, colleagues clapping behind them.",
 "10": "Inside this high-ceilinged machining hall at dawn, seen from the middle of the hall toward the large roll-up shutter at the far end: the shutter slowly rises and golden morning light floods in across the grey concrete floor between the rows of machines, camera slowly pushing forward. The crane hook reel stays small and high up near the ceiling. No people.",
 "34": "An overhead crane slowly lifts a huge flat precision-machined steel plate with slings high above the floor; the elderly large-part machining advisor and the ponytailed recruit stand safely to the side, well away from under the load, steering it gently with long guide ropes and watching it with focused faces. Nobody stands under the load or touches it with their hands.",
 "40": "Still-life on a wooden workbench: an old analog vernier caliper next to a modern digital caliper whose screen is blank, soft evening window light. The instruments have no letters, no numbers, no brand names and no labels at all.",
 "38": "Three employees in navy uniforms (the cheerful Vietnamese recruit, the short-haired woman inspector and the earnest clerk) look up toward bright light with determined smiles, a gentle breeze, camera slowly pushing in. Only these three people in the foreground.",
 "35": "Wide shot from the same angle as the reference photo, across the asphalt driveway: all twenty-one employees of a small company stand together in two rows on the driveway in front of the stone retaining wall, smiling, the president and the petite vice president (short dark brown bob, NO glasses) in the center; the camera slowly pulls back and rises. Realistic scale: each person is about one sixth of the building height, the two-story building towers behind them. The building keeps its company sign exactly as in the reference: the round emblem and the yellow lettering HARA MACHINERY CO.,LTD. on the blue band. No other signboards or standing signs.",
 "28": "Lunch break in the company's small break room (a separate room with a table and windows, NOT inside the factory hall): five or six employees in navy uniforms laugh together while eating bento boxes; the talkative Vietnamese recruit tells a story, the founder's wife and the ponytailed part-time woman laugh. Relaxed and warm.",
 "06": "Low-angle side shot in this high-ceilinged machining hall: the spindle of a large gantry-type machining center, fitted with a wide face mill, moves slowly and steadily in a perfectly straight horizontal line across the top of a huge solid block of polished silver steel, leaving behind a straight, flat, mirror-like machined strip. The tool stays at the same height the whole time. Clean, calm cutting with only a few tiny metal shavings. No people, no sparks.",
 "26": "One single continuous shot: the camera rises from a Japanese city at golden hour up through the clouds into space, pulling back to reveal the whole Earth. Not split into panels.",
 "50": "Medium-wide shot at golden hour, people large in the frame with faces clearly visible: the company's employees stand together with their customers in suits and partner suppliers in work clothes in front of this factory building exactly as in the reference, a plain unbranded 3-ton truck nearby; they smile and look up at the sky as the camera slowly rises toward the evening sky.",
}
_NOTES = [n for n in ("UNIFORM_NOTE", "FLOOR_NOTE", "SCALE_NOTE", "COLOR_NOTE") if n in globals()]
for _c in CUTS:
    if _c["no"] in FIX:
        p = FIX[_c["no"]]
        if _c.get("refs") and set(_c["refs"]) & set(_STAFF) or "employees" in p:
            p += UNIFORM_NOTE
        if "big_part" in _c.get("refs", []):
            p += FLOOR_NOTE
        if set(_c.get("refs", [])) & {"factory_real", "big_part", "cmm_device"} or "machining hall" in p:
            p += SCALE_NOTE + COLOR_NOTE
        p += " One single continuous shot (never split into comic panels). No maker names, brand names or logos on any machine."
        _c["prompt"] = p

# 10/3 カットシーン集の指示で直したカット（シートのカット番号 → 新しいクリップ clips/cutXXX.mp4）
# f は fix2_videos.py で作り直したもの、c42 は看板が映らないよう少し寄せたもの。クリップができたものから差し替わる
import os as _os
_NEW = {2: "f02", 3: "f03", 9: "f09", 12: "f12", 16: "f16", 17: "f17", 30: "f30", 33: "f33", 41: "f41",
        42: "c42", 45: "f45", 47: "f47", 48: "f48", 49: "f49", 50: "f50"}
TIMELINE = [(_NEW[i] if i in _NEW and _os.path.exists(f"clips/cut{_NEW[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]
LOGO_AT = 9999.0  # 社名は finish2.py で新しい出し方に重ねる

# 10/4 カットシーン集 第2版の指示で直したカット（fix3_videos.py で作ったもの。できたものから差し替わる）
_NEW2 = {n: f"g{n:02d}" for n in (3, 4, 9, 17, 24, 27, 31, 37, 50, 51)}
TIMELINE = [(_NEW2[i] if i in _NEW2 and _os.path.exists(f"clips/cut{_NEW2[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]

# 10/4 エンディング（48〜52）は 2 秒ずつだと速すぎるので、48〜51 を 3 秒ずつに延ばし、52 を短くする
_END = [(258.9, 261.9), (261.9, 264.9), (264.9, 267.9), (267.9, 270.9), (270.9, 275.8)]
TIMELINE = TIMELINE[:47] + [(no, s, e) for (no, _, _), (s, e) in zip(TIMELINE[47:], _END)]
# 52 は短くなった分、手を振り終えて空へ上がる後半が映るよう、1.45 秒後ろから始まるクリップを使う
TIMELINE[51] = ("e52", *TIMELINE[51][1:])

# 10/4 夕 カットシーン集 第3版の指示（4 は人が時代を越えて変わらない場面に、41 は奥の小さな人を消す）
_NEW3 = {4: "g04b", 41: "g41"}
TIMELINE = [(_NEW3[i] if i in _NEW3 and _os.path.exists(f"clips/cut{_NEW3[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]

# 10/5 本物の工場（中二階からの写真）で描き直した 12・27
_NEW4 = {12: "g12r", 27: "g27r"}
TIMELINE = [(_NEW4[i] if i in _NEW4 and _os.path.exists(f"clips/cut{_NEW4[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]

# 10/5 カットシーン集 第3版への追記（本物の製品・工場・事務所の写真をもとに描き直したもの）
_NEW5 = {7: "g07", 8: "g08", 9: "g09r", 10: "g10", 11: "g11", 24: "g24r", 31: "g31r", 37: "g37r"}
TIMELINE = [(_NEW5[i] if i in _NEW5 and _os.path.exists(f"clips/cut{_NEW5[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]
# 10/5 事務所の写真で描き直した 14・33
_NEW6 = {14: "g14", 33: "g33r"}
TIMELINE = [(_NEW6[i] if i in _NEW6 and _os.path.exists(f"clips/cut{_NEW6[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]
# 10/5 カット 17 は会社で作っているガラス切断装置の除幕に
if _os.path.exists("clips/cutg17g.mp4"):
    TIMELINE[16] = ("g17g", *TIMELINE[16][1:])
# 10/5 夕：加工品の統一・10 の設計者・17 のお披露目・47 ものづくりの未来
_NEW7 = {7: "g07b", 10: "g10b", 17: "g17b", 25: "g25b", 41: "g41b", 43: "g43b", 47: "g47b", 48: "g48b", 50: "g50b"}
TIMELINE = [(_NEW7[i] if i in _NEW7 and _os.path.exists(f"clips/cut{_NEW7[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]
# 10/5 夕：カット 10 は図面が伸び縮みするので、手渡しの瞬間の 1 枚絵をゆっくり寄せる
if _os.path.exists("clips/cutg10s.mp4"):
    TIMELINE[9] = ("g10s", *TIMELINE[9][1:])
if _os.path.exists("clips/cutg10f.mp4"):
    TIMELINE[9] = ("g10f", *TIMELINE[9][1:])
# 10/6 会社のトラックに統一した 25・50
for _i, _id in ((25, "g25t"), (50, "g50t")):
    if _os.path.exists(f"clips/cut{_id}.mp4"):
        TIMELINE[_i - 1] = (_id, *TIMELINE[_i - 1][1:])
# 10/6 図面・装置の色・トラックの差し替え
_NEW8 = {3: "g03j", 10: "g10d", 11: "g11d", 14: "g14d", 16: "g16d", 17: "g17d", 25: "g25u", 28: "g28d", 40: "g40d",
         47: "g47d", 50: "g50u"}
TIMELINE = [(_NEW8[i] if i in _NEW8 and _os.path.exists(f"clips/cut{_NEW8[i]}.mp4") else no, s, e)
            for i, (no, s, e) in enumerate(TIMELINE, 1)]
# 10/6 カット 4：過去→現在をセピアのままディゾルブし、色をゆっくり戻す（編集のみ）
if _os.path.exists("clips/cutg04c.mp4"):
    TIMELINE[3] = ("g04c", *TIMELINE[3][1:])
# 10/6 図面の向きをそろえた版（3・10・11・16・40）と、カット 37（鉄の束がすり抜けない 1 枚絵）
_NEW9 = {3: "g03k", 10: "g10h", 11: "g11e", 16: "g16e", 37: "g37s", 40: "g40f"}
TIMELINE = [(_NEW9[i] if i in _NEW9 and _os.path.exists(f"clips/cut{_NEW9[i]}.mp4") else no, s, e) for i,(no,s,e) in enumerate(TIMELINE,1)]
# 10/6 夕：10 は普通の大きさの図面（描く人の向き）で手渡す 1 枚絵 2 枚、21 はガラス切断装置の組み立て
_NEW10 = {10: "g10j", 21: "g21a"}
TIMELINE = [(_NEW10[i] if i in _NEW10 and _os.path.exists(f"clips/cut{_NEW10[i]}.mp4") else no, s, e) for i,(no,s,e) in enumerate(TIMELINE,1)]
# 10/6 夜：21 は床に立って腰の高さの M20 ナットを締める（後半だけ使用）
if _os.path.exists("clips/cutg21c.mp4"):
    TIMELINE[20] = ("g21c", *TIMELINE[20][1:])
# 10/6 夜：2 は白黒。49・50 は削除し、空いた 6 秒は 48 と 51 に分ける
if _os.path.exists("clips/cutf02bw.mp4"):
    TIMELINE[1] = ("f02bw", *TIMELINE[1][1:])
TIMELINE = TIMELINE[:47] + [(TIMELINE[47][0], 258.9, 263.4), (TIMELINE[50][0], 263.4, 270.9)] + TIMELINE[51:]
# 10/6 夜：3（約 50 歳の職人が溶接 → 副社長へ A3 の図面）、4（1948 → 1990 年代 → 今）、10（A3）、22（ベトナム人の新人が溶接）、
# 社長の顔をそろえた 31・45・48（番号は 49・50 を消した後の並び）
_NEW11 = {3: "g03m", 4: "g04d", 10: "g10k", 22: "g22v", 31: "g31q", 45: "g45w", 48: "g48p"}
TIMELINE = [(_NEW11[i] if i in _NEW11 and _os.path.exists(f"clips/cut{_NEW11[i]}.mp4") else no, s, e) for i,(no,s,e) in enumerate(TIMELINE,1)]
# 10/7 カット 2：1948 年の町工場、職人の手元だけでノミとハンマーで石を削る（白黒）
if _os.path.exists("clips/cutg02t.mp4"):
    TIMELINE[1] = ("g02t", *TIMELINE[1][1:])
# 10/7 カット 4 の 1990 年代を、こぢんまりした町工場に
if _os.path.exists("clips/cutg04f.mp4"):
    TIMELINE[3] = ("g04f", *TIMELINE[3][1:])
# 10/7 カット 4 は 1948 年をやめて、1990 年代 → 今だけに
if _os.path.exists("clips/cutg04g.mp4"):
    TIMELINE[3] = ("g04g", *TIMELINE[3][1:])
# 10/7 カット 4：カット 3 に合わせた描き方。1990 年代（セピア）→ 今、どちらも自然に作業し続ける動画
if _os.path.exists("clips/cutg04h.mp4"):
    TIMELINE[3] = ("g04h", *TIMELINE[3][1:])
# 10/7 カット 4：参考動画のような小さくゆっくりした動き。1990 年代（セピア）→ 本物の事務所で図面を見ながら話し合う
if _os.path.exists("clips/cutg04i.mp4"):
    TIMELINE[3] = ("g04i", *TIMELINE[3][1:])
# 10/7 カット 4 再挑戦：カメラ固定・小さな動きの 2 本から、動きの量を測って基準内（約 3 以下）の部分だけを使用
if _os.path.exists("clips/cutg04j.mp4"):
    TIMELINE[3] = ("g04j", *TIMELINE[3][1:])
# 10/7 新しい設定表の顔（社長・品質課の課長・先代社長の奥さん）にそろえた 23・24・27・32・49（カメラ固定・小さな動き、基準内の部分だけ）
_NEW12 = {23: "g23m", 24: "g24m", 27: "g27m", 32: "g32m", 49: "g49m"}
TIMELINE = [(_NEW12[i] if i in _NEW12 and _os.path.exists(f"clips/cut{_NEW12[i]}.mp4") else no, s, e) for i,(no,s,e) in enumerate(TIMELINE,1)]
# 10/7 カット 47：社長・副社長を真ん中に
if _os.path.exists("clips/cutg47m.mp4"):
    TIMELINE[46] = ("g47m", *TIMELINE[46][1:])
# 10/7 カット 47：21 人にした 1 枚目（社長・副社長が真ん中）をゆっくり寄せる（動画化は未承認のため止め絵）
if _os.path.exists("clips/cutg47s.mp4"):
    TIMELINE[46] = ("g47s", *TIMELINE[46][1:])
# 10/7 カット 7：実際の加工動画を元にした絵。始めと終わりを同じ絵にして機械の形を固定
if _os.path.exists("clips/cutg07m.mp4"):
    TIMELINE[6] = ("g07m", *TIMELINE[6][1:])
# 10/7 カット 47：白髪の女性をトラック運転手に替えた 1 枚絵をゆっくり寄せる
if _os.path.exists("clips/cutg47t.mp4"):
    TIMELINE[46] = ("g47t", *TIMELINE[46][1:])
# 10/7 カット 3：溶接の場面だけセピア色（図面を手渡す場面へ切り替わるところで色が戻る）
if _os.path.exists("clips/cutg03n.mp4"):
    TIMELINE[2] = ("g03n", *TIMELINE[2][1:])
# 10/7 カット 41：製品を地面と平行のまま真横から吊り上げる（41hb の 1.0〜4.9 秒を使う。その後はスイッチが別の人の手に移るので使わない）
if _os.path.exists("clips/cutg41m.mp4"):
    TIMELINE[40] = ("g41m", *TIMELINE[40][1:])
# 10/8 カット 38：1990 年代の場面なのでセピア色（カット 3 の溶接と同じ色合い）
if _os.path.exists("clips/cutg38s.mp4"):
    TIMELINE[37] = ("g38s", *TIMELINE[37][1:])
