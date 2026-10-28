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
