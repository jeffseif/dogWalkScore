#! /bin/bash

PID='/home/ubuntu/log/pid' ;

[ -e "${PID}" ] && echo 'Up' || echo 'Down' ;
