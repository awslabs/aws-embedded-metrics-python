#!/bin/bash
. /app/venv/bin/activate

pip3 install psutil > /dev/null
pip3 install getversion > /dev/null

python3 ./canary.py