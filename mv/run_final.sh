#!/bin/sh
# 残りのカットだけ、1 枚絵を最初のコマにして作る（通常版→Fast→Lite）。作成済みの動画はそのまま使う
cd "$(dirname "$0")"
for m in veo-3.1-generate-preview veo-3.1-fast-generate-preview veo-3.1-lite-generate-preview; do
  FROM_STILLS=1 VEO_MODEL=$m python3 -u make_all.py 2>&1 | grep --line-buffered -E "^(ok|FAIL)" | cut -c1-60
done
python3 edit.py song.mp3
ffmpeg -v error -y -i out/mv.mp4 -c:v libx264 -preset slow -b:v 620k -maxrate 900k -bufsize 1800k -c:a aac -b:a 128k -movflags +faststart preview_mv.mp4
python3 -c "
import os
from cuts import TIMELINE
print('missing:', sorted({n for n,_,_ in TIMELINE if not os.path.exists(f'clips/cut{n}.mp4')}))"
