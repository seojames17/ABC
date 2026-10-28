#!/usr/bin/env bash
# 장면 이미지 + 오버레이 + 내레이션을 장면별 mp4로 만든 뒤 하나로 이어 붙인다.
# make_overlays.py ko|en 을 먼저 실행해 ov/ 와 durs.json을 만들어 둘 것.
set -e
mkdir -p seg
for k in $(seq 1 10); do
  D=$(python3 -c "import json;print(json.load(open('durs.json'))['$k'])")
  F=$(python3 -c "import math;print(math.ceil($D*30))")
  ffmpeg -y -v error -i img/$k.png -f concat -safe 0 -i ov/$k.txt -i aud/$k.mp3 -filter_complex \
   "[0:v]scale=1620:2895,crop=1620:2880,zoompan=z='min(zoom+0.0005,1.06)':d=$F:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,setsar=1[bg];[1:v]fps=30,format=rgba[ov];[bg][ov]overlay=0:0:eof_action=repeat,format=yuv420p[v];[2:a]aresample=44100,apad,atrim=0:$D[a]" \
   -map "[v]" -map "[a]" -t $D -r 30 -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 160k -ac 2 seg/$k.mp4
  echo "seg $k done"
done
: > seg/list.txt; for k in $(seq 1 10); do echo "file '$k.mp4'" >> seg/list.txt; done
ffmpeg -y -v error -f concat -safe 0 -i seg/list.txt -c copy episode.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact episode.mp4
