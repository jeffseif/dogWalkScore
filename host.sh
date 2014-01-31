#! /bin/bash

###
# Constants
###
APP='flaskr:app' ;
DIR='../log/' ;
IPADDRESS='0.0.0.0:80' ;
RESTARTSECONDS='5' ;
NUMWORKERS='1' ;
PID="${DIR}pid" ;
TIMEOUTSECONDS='300' ;

###
# gunicorn command
###
GUNICORN="sudo gunicorn ${APP} -w ${NUMWORKERS} -b ${IPADDRESS} -p ${PID} --access-logfile - --error-logfile - --timeout ${TIMEOUTSECONDS}" ;

###
# Host
###
while [ 0 ] ; do
    ###
    # Set log/err filename
    ###
    LOG="${DIR}$(date "+%F-%T").log" ;
    ERR="${DIR}$(date "+%F-%T").err" ;
    ###
    # Execute gunicorn
    ###
    echo "Starting gunicorn and dumping log to ${LOG}" ;
    ${GUNICORN} >> "${LOG}" 2>> "${ERR}" ;
    ###
    # Upon fail wait before looping
    ###
    echo "gunicorn finished ... sleeping for ${RESTARTSECONDS}s ..." ;
    sleep "${RESTARTSECONDS}" ;
    echo "... restarting now" ;
done ;
