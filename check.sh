#! /bin/bash

PID="$(cat ~/log/pid)" ;

[ -e "${PID}" ] && echo 'Up' || echo 'Down' ;
