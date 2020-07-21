#!/bin/sh

apk add python3 py3-pip
python3 -m pip install --upgrade gallery-dl youtube-dl requests
mkdir /app/data/gallery-dl
echo '설치된 버전: '
gallery-dl --version