#!/usr/bin/env bash
# 만화풍 효과음을 sox로 합성한다 (저작권 걱정 없는 자체 제작음).
set -e
mkdir -p sfx && cd sfx
sox -n -r 44100 -c 2 hum.wav    synth 0.9 sine 120 sine 240 vol 0.25 fade 0.05 0.9 0
sox -n -r 44100 -c 2 thunk.wav  synth 0.45 sine 55 synth 0.45 brownnoise mix vol 0.9 fade 0 0.45 0.4
sox -n -r 44100 -c 2 click.wav  synth 0.03 whitenoise highpass 3000 vol 0.6 fade 0 0.03 0.02 pad 0 0.1
sox -n -r 44100 -c 2 whoosh.wav synth 0.35 pinknoise bandpass 1200 900 vol 0.35 fade q 0.1 0.35 0.2
sox -n -r 44100 -c 2 creak.wav  synth 0.6 sawtooth 180-120 vol 0.12 tremolo 18 80 lowpass 1500 fade 0.05 0.6 0.15
sox -n -r 44100 -c 2 sting.wav  synth 1.2 sine 73.4 sine 69.3 vol 0.6 fade 0 1.2 0.9
# 1화 본편에서 추가한 효과음
sox -n -r 44100 -c 2 stop.wav   synth 0.35 sine 900-90 vol 0.5 fade 0 0.35 0.1
sox -n -r 44100 -c 2 drip.wav   synth 0.09 sine 500-1300 vol 0.5 fade 0 0.09 0.05 pad 0 0.2
sox -n -r 44100 -c 2 c1.wav     synth 0.07 sine 2600-3400 vol 0.25 fade 0 0.07 0.03 pad 0 0.08 && sox c1.wav c1.wav c1.wav chirp.wav
sox -n -r 44100 -c 2 e1.wav     synth 0.13 square 280 vol 0.18 pad 0 0.07 && sox e1.wav e1.wav error.wav
sox -n -r 44100 -c 2 h1.wav     synth 0.3 sine 880 vol 0.35 fade 0 0.3 0.2
sox -n -r 44100 -c 2 h2.wav     synth 0.5 sine 659 vol 0.35 fade 0 0.5 0.35 && sox h1.wav h2.wav chime.wav
sox -n -r 44100 -c 2 s1.wav     synth 0.28 triangle 392 vol 0.3
sox -n -r 44100 -c 2 s2.wav     synth 0.28 triangle 370 vol 0.3
sox -n -r 44100 -c 2 s3.wav     synth 0.6 triangle 349 vol 0.3 fade 0 0.6 0.4 && sox s1.wav s2.wav s3.wav sad.wav
sox -n -r 44100 -c 2 ding.wav   synth 0.7 sine 1320 sine 1980 vol 0.3 fade 0 0.7 0.6
sox -n -r 44100 -c 2 pop.wav    synth 0.07 sine 450-1100 vol 0.45 fade 0 0.07 0.04 pad 0 0.1
sox -n -r 44100 -c 2 lowbat.wav synth 0.12 sine 1800 vol 0.2 pad 0 0.1 synth 0.12 sine 1800
rm -f c1.wav e1.wav h1.wav h2.wav s1.wav s2.wav s3.wav
