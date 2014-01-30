#! /bin/bash

PID="$(cat ~/log/pid)" ;

ps -p "${PID}" > /dev/null && echo 'Up' || echo 'Down' ;
