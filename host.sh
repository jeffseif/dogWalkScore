#! /bin/bash

###
# Constants
###
APP='flaskr:app' ;
DIR='../log/' ;
GUNICORN="sudo gunicorn ${APP} -w 4 -b 0.0.0.0:80" ;
SECONDS='5' ;

###
# Declare PID
###
PID="${DIR}pid" ;
\rm -f "${PID}" ;
echo "$$" > "${PID}" ;

###
# Host
###
while [ 0 ] ; do
    ###
    # Set log filename
    ###
    LOG="${DIR}$(date "+%F-%T").log" ;
    ###
    # Execute gunicorn
    ###
    ${GUNICORN} >> "${LOG}" 2>&1 ;
    ###
    # Upon fail wait before looping
    ###
    sleep "${SECONDS}" ;
done ;
