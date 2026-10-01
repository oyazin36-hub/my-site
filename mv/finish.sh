#!/bin/sh
# クレジット追加後に実行: 追加人物の参照画像 → 未生成カット → 完成版の書き出し
set -e
cd "$(dirname "$0")"
python3 make_refs.py inspector newbie sales welder
VEO_MODEL=${VEO_MODEL:-veo-3.1-generate-preview} python3 make_all.py | tee gen_finish.log
python3 edit.py song.mp3
ffmpeg -v error -y -i out/mv.mp4 -c:v libx264 -preset slow -b:v 620k -maxrate 900k -bufsize 1800k -c:a aac -b:a 128k -movflags +faststart preview_mv.mp4
