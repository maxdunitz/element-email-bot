#!/bin/bash

trap "kill 0" SIGINT

while true;

do nohup python3 -m flask run --host=0.0.0.0 --port=8009
done

