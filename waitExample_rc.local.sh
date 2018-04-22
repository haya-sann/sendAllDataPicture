#!/bin/bash
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address

export DEPLOY="sandBox"
#export DEPLOY="distribution"

#case文でsandBoxに送るか、本番環境に送るかを選択する。
case "$DEPLOY" in
"sandBox" )  DIRPATH="daily_timelapseSandbox" ;;
"distribution" )  DIRPATH="daily_timelapse" ;;
esac

echo "Now current directory is set : "$DIRPATH

#ログを生成する
#LOGFILE="/home/pi/Documents/mochimugi/${DIRPATH}/mochimugi.log"

LOGFILE="/home/pi/Documents/mochimugi/sendAllDataPicture/sendIM/mochimugi.log"

readonly PROCNAME=${0##*/}

function log() {
  local fname=${BASH_SOURCE[1]##*/}
  echo -e "$(date '+%Y-%m-%dT%H:%M:%S') ${PROCNAME} (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $@" | tee -a ${LOGFILE}
}
log "***** above-mentioned is previously log  *****"
log "Started logging to : "$LOGFILE
log "rc.local 更新：2017年06月10日（土）11時44分"

cd /home/pi/Documents/mochimugi/sendAllDataPicture
git pull | tee -a ${LOGFILE}



echo -e "\e[42;31mto stop this autorun script, press PROGRAM SWITCH\e[m"
echo -e "\e[31mwithin 10 seconds\e[m"

sleep 10

ntpq -p

PORT1=23
PORT2=24

gpio -g mode $PORT1 in
gpio -g mode $PORT2 out

if [ `gpio -g read $PORT1` -eq 1 ] ; then
  echo program switch is held down
  gpio -g write $PORT2 1
  exit 0
fi

echo PROGRAM SWITCH is not held down. Now system start normally

function my_shutdown() {
  /usr/sbin/i2cset -y 1 0x40 255 11 i
  sleep 240
  sudo poweroff

  exit 0
}

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

sudo python /home/pi/Documents/mochimugi/sendAllDataPicture/sendIM/sendBMEDataToIM_periodically.py || ( echo python error ; my_shutdown )

exit 0


