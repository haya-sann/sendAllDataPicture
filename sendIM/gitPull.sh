#!/bin/bash

cd /home/pi/Documents/field_location/sendAllDataPicture
git checkout ${gitBranch} | tee -a ${LOGFILE} #|| log ("Error occured in git. Update failed")
git status | tee -a ${LOGFILE} # || log ("Error occured in git. Update failed")
git pull | tee -a ${LOGFILE} # || log ("Error occured in git. Update failed")

exit 0
