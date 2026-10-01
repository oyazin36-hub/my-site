#!/bin/sh
# 未生成のカットを、上限に当たったら次のモデルへ切り替えながら作り、完成版を書き出す
cd "$(dirname "$0")"
for m in veo-3.1-generate-preview veo-3.1-fast-generate-preview veo-3.1-lite-generate-preview; do
  VEO_MODEL=$m python3 make_all.py | grep -E "^(ok|FAIL)" | cut -c1-80
done
python3 edit.py song.mp3
ffmpeg -v error -y -i out/mv.mp4 -c:v libx264 -preset slow -b:v 620k -maxrate 900k -bufsize 1800k -c:a aac -b:a 128k -movflags +faststart preview_mv.mp4
python3 -c "
import os
from cuts import TIMELINE
print('missing:', [n for n,_,_ in TIMELINE if not os.path.exists(f'clips/cut{n}.mp4')])"
