#!/bin/sh

## This script relies on apt. 
## If you would want to use a PR to make one for brew or any other pkg man, please do!


## Root Check
if [ $USER != root ]; then
  echo -e $RED"Error: must be root! Exiting..."$ENDCOLOR
  exit 0
fi

## Updates and deps
apt update
apt install -y python3 python3-pip ffmpeg git
pip3 install -r requirements.txt ##json, subprocess are included by default.

## Gather Gentle
git clone https://github.com/lowerquality/gentle.git
cd gentle
./install.sh
