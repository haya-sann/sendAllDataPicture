#!/bin/bash
#これを更新してgit commit すると自動アップデートされる
# sandBoxへの切り替えをサポートしたrc.local
#Deploy時にSandBoxか、Distributionかを指定して出荷する
#モデムのppp接続を待つようにした。2017/06/07
#失敗したら4分後にパワーオフ、10分後にリブートするように変更
# This script is executed at the end of each multiuser runlevel.
#tee -a　は追記モードのこと、今回は毎回新しくログを記録する

#結構重要な変更。一晩悩んだ。
#次に起動するプログラムにDEPLOY情報を継承する #変数代入の＝の前後の空白を入れてはいけない#

export DEPLOY="sandBox"
#export DEPLOY="distribution"

#case文でsandBoxに送るか、本番環境に送るかを選択する。
case "$DEPLOY" in
"sandBox" )  DIRPATH="daily_timelapseSandbox" ;;
"distribution" )  DIRPATH="daily_timelapse" ;;
esac

echo "Now current directory is set : "$DIRPATH

#ログを生成する
LOGFILE="/home/pi/Documents/mochimugi/${DIRPATH}/mochimugi.log"
readonly PROCNAME=${0##*/}

function log() {
  local fname=${BASH_SOURCE[1]##*/}
  echo -e "$(date '+%Y-%m-%dT%H:%M:%S') ${PROCNAME} (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $@" | tee -a ${LOGFILE}
}
echo "***** above-mentioned is previous log  *****" | tee -a ${LOGFILE}
log "Started logging to : "$LOGFILE
echo "***** rc.local ver. 1.1 更新：2017年06月10日（土）11時44分  *****" | tee -a ${LOGFILE}

#
#Soracomのドングルppp接続またはネットワーク接続rc.local
#ppp接続ないしはSakura,ne,jpへの疎通がない場合は4分間の休止後、55分間仮死状態に
#ppp接続する方法は
#http://qiita.com/CLCL/items/95693f6a8daefc73ddaa#_reference-1e89edc09fe5b273aee3


echo -e "\e[42;31mto stop this autorun script, set PROGRAM SWITCH on\e[m"
echo -e "\e[31mwithin 10 seconds\e[m"

sleep 10
ntpq -p

PORT1=23 #GPIO23=Pin16
gpio -g mode $PORT1 in

PORT2=24 #GPIO24=Pin18
gpio -g mode $PORT2 out


if [ `gpio -g read $PORT1` -eq 1 ] ; then #シングルクオートの``が大切なようだ
  log "program switch is ON"
  gpio -g write $PORT2 1
  crontab < /home/pi/crontab
  echo -e "\e[42;31mcrontab enabled\e[m"
  exit 0
fi

log "PROGRAM SWITCH is off. Now system start normally"

function waitForPing() {
    # Wait for Network to be available.
for i in {1..5};
    do ping -c1 mochimugi.sakura.ne.jp &> /dev/null && (echo SakuraServer is available) && break; 
    echo -n .
    done
[ $i = 5 ] && ( echo Can not reach to Sakura Server ; my_shutdown2)
return 0
}

function waitForPPP() {
  echo waiting for ppp connection
  for i in {1..30}
  do
    [ -e /sys/class/net/ppp0/carrier ] && break
    echo -n .
    sleep 1
  done
  [ $i = 30 ] && ( echo not found ppp connection ; log "not found ppp connection" ; my_shutdown2 )
  return 0
}

function my_shutdown() {
  powerControlCommand="/usr/sbin/i2cset -y 1 0x40 255 11 i"
  $(echo powerControlCommand) | tee -a ${LOGFILE} #変数をコマンドとして実行させるには$()とすろ
  echo system will poweroff after 4 minutes
  log "sended power control command : "$powerControlCommand
  sleep 240
  poweroff
  exit 0
}

function my_shutdown2() {
  powerControlCommand="/usr/sbin/i2cset -y 1 0x40 255 1 i"
  $(echo powerControlCommand) | tee -a ${LOGFILE}
  echo system will poweroff after 4 minutes
  log "network is down : sended power control command : "$powerControlCommand
  log "system will poweroff after 4 minutes, and reboot after 5 minutes"
  sleep 240
  poweroff
  exit 0
}

crontab < /home/pi/crontab_off #disable crontab
echo -e "\e[42;31mcrontab is disabled\e[m"
log "crontab is off"

#まず、USBモデムがsora.comに接続できるのを待つ。失敗すると4分待って再起動させる。
waitForPPP || ( echo connectSoracom error ; my_shutdown2 )

echo -e "\e[42;31mppp is up and running\e[m"
log "ppp is up and running"

waitForPing || ( echo connectSoracom error ; my_shutdown2 )
log "Sakura server is online"

log "update all files in sendAllDataPicture with git pull"
cd /home/pi/Documents/mochimugi/sendAllDataPicture
git pull | tee -a ${LOGFILE}

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

# { { sudo python /home/pi/Documents/mochimugi/sendAllDataPicture/sendAll_IM.py | tee /home/pi/Documents/mochimugi/${DIRPATH}/mochimugi.log; } 3>&2 2>&1 1>&3 | tee /home/pi/Documents/mochimugi/${DIRPATH}/mochimugiErr.log; } 3>&2 2>&1 1>&3 || ( echo python error ; my_shutdown )

#sendAll_IM.pyに環境変数DEPLOYを送るためにはsudoでは機能しない
python /home/pi/Documents/mochimugi/sendAllDataPicture/sendAll_IM.py || ( echo python error ; my_shutdown )

exit 0