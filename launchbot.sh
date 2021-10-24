#!/bin/bash

trap "kill 0" SIGINT

while true;

do nohup python bot.py
done

