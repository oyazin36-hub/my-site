#!/bin/sh
# 見本の画風の 1 枚絵から全カットを動画にする（上限に当たったら次のモデルへ）。前の画風の動画は clips/old_style へ
cd "$(dirname "$0")"
mkdir -p clips/old_style
for f in clips/cut??.mp4; do [ -e "$f" ] && [ ! -e "clips/.newstyle_$(basename $f)" ] && mv "$f" clips/old_style/; done
for m in veo-3.1-generate-preview veo-3.1-fast-generate-preview veo-3.1-lite-generate-preview; do
  # 通常版が上限なら待たずに次へ（1 件目が 429 ならそのモデルは飛ばす）
  FROM_STILLS=1 VEO_MODEL=$m python3 -u make_all.py 2>&1 | grep --line-buffered -E "^(ok|FAIL)" | cut -c1-60
  for f in clips/cut??.mp4; do [ -e "$f" ] && touch "clips/.newstyle_$(basename $f)"; done
done
python3 edit.py song.mp3
ffmpeg -v error -y -i out/mv.mp4 -c:v libx264 -preset slow -b:v 620k -maxrate 900k -bufsize 1800k -c:a aac -b:a 128k -movflags +faststart preview_mv.mp4
python3 -c "
import os
from cuts import TIMELINE
print('missing:', sorted({n for n,_,_ in TIMELINE if not os.path.exists(f'clips/cut{n}.mp4')}))"
