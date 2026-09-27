#!/bin/bash
NAME="${1:-Yan}"
python3 -m piper -m en_US-lessac-medium -f greeting.wav -- "Hi Hi Hi, ${NAME}! Welcome back. I hope you are having a wonderful day."
aplay greeting.wav

