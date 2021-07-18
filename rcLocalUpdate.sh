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

#Soracomドングルを付けた環境下かどうかは自動判定する

#export DEPLOY="sandBox" #start repair survey 2019-05-29
export DEPLOY="distribution"

#pullするgitリポジトリのブランチをセット
#gitBranch="getErrorMsgFromAmbi"
#gitBranch="homeSimulator"
export gitBranch="master"

#ログを生成する
export LOGFILE="/var/log/field_location.log"
#LOGFILE="/home/pi/Documents/field_location/${DIRPATH}/field_location.log"
readonly PROCNAME=${0##*/}


#case文でsandBoxに送るか、本番環境に送るかを選択する。
case "$DEPLOY" in
"sandBox" )  DIRPATH="daily_timelapseSandbox" ;;
"distribution" )  DIRPATH="daily_timelapse" ;;
esac

echo "Now current directory is set : "$DIRPATH | tee -a ${LOGFILE}

function log() {
  local fname=${BASH_SOURCE[1]##*/}
  echo -e "$(date '+%Y-%m-%dT%H:%M:%S') ${PROCNAME} (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $@" | tee -a ${LOGFILE}
}
echo "***** above-mentioned is previous log  *****" | tee -a ${LOGFILE}
log "Started logging to : "$LOGFILE
echo "***** rc.local ver. 2.1 更新：2021/06/17　14:45  *****" | tee -a ${LOGFILE}
#systemctl list-unit-files --state=enabled --no-pager | tee -a ${LOGFILE}

#
#Soracomのドングルppp接続またはネットワーク接続rc.local
#ppp接続ないしはSakura,ne,jpへの疎通がない場合は4分間の休止後、55分間仮死状態に
#ppp接続する方法は
#http://qiita.com/CLCL/items/95693f6a8daefc73ddaa#_reference-1e89edc09fe5b273aee3

function waitForPing() {
    # Wait for Network to be available.
    #please specify target server
for i in {1..5};
    do ping -c1 ciao-kawagoesatoyama.ssl-lolipop.jp &> /dev/null && (date | tee -a ${LOGFILE}) && break; 
    # server reached, update time
    echo -n .
    done
[ $i = 5 ] && ( echo Can not reach  Server  | tee -a ${LOGFILE} ; my_shutdown2)
return 0
}

function waitForPPP() {
  echo "waiting for ppp connection"
  for i in {1..30}
  do
    [ -e /sys/class/net/ppp0/carrier ] && break || ifup wwan0
    echo -n .
    sleep 1
  done
  [ $i = 30 ] && ( echo not found ppp connection ; log "not found ppp connection" ; my_shutdown2 )
  return 0
}

function my_shutdown() {
  powerControlCommand="/usr/sbin/i2cset -y 1 0x40 255 11 i"
    for i in {1..5}
    do
        if eval $powerControlCommand |& grep "Error"; then
        echo Error encountered in my_shutdown. write i2c bus
        log "Error encountered in my_shutdown2. Write i2c bus"
        sleep 1
        else
        break
        fi
    done
[ $i = 5 ] && echo error writing I2C && reboot
  echo system will poweroff after 4 minutes
  log "sended power control command : "$powerControlCommand
  sleep 240
  sudo poweroff
  exit 0
}

function my_shutdown2() { #ネットワーク接続に失敗したときなど
    powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x40 20 0 i" #20秒後に電源オフ、直ちに再Poweron
    for i in {1..5}
    do
        if eval $powerControlCommand |& grep "Error"; then
        echo I2C bus write error.$i" times"
        log "I2C bus write error. "$i"times"
        sleep 1
        else
        break
        fi
    done
[ $i = 5 ] && echo error writing I2C && log "error writing I2C, "$i" times. Reboot right away" && keepLogAtReboot && reboot
    echo system will poweroff after 10 seconds, and reboot
    log "network is down : sended power control command : "$powerControlCommand
#    log "system will poweroff after 10 seconds, and reboot"
    keepLogAtReboot
    sudo poweroff
    return 0
}

function keepLogAtReboot {
  logAtReboot=$(</var/log/boot.log)
echo -e "\r\nAlert message: This is a log at reboot\r\n\r\n""${logAtReboot}" |tee -a /home/pi/log/previous_boot.log
}

crontab < /home/pi/crontab_off #disable crontab
echo -e "\e[42;31mcrontab is disabled\e[m"
log "crontab is off"

# まず、network="SoracomPPP"の指定があるかどうかチェック。
#USBモデムがsora.comに接続できるのを待つ。失敗すると4分待って再起動させる。


if [ -e /sys/class/net/wlan0/carrier ];then
  	echo "Wi-Fi found"  | tee -a ${LOGFILE}
elif [ -e /sys/class/net/eth0/carrier ];then
    echo "Ethernet connected" | tee -a ${LOGFILE}
else
  waitForPPP || ( echo connectSoracom error ; my_shutdown2 )
  echo -e "\e[42;31mppp is up and running\e[m"
  log "ppp is up and running"
fi

waitForPing || ( echo connectSoracom error ; my_shutdown2 )
log "Server is online"


# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

log "update all files in sendAllDataPicture directory with git pull"
cd /home/pi/Documents/field_location/sendAllDataPicture
#gitコマンドを一般ユーザーのpiで実行する必要がある。
sudo -u pi git checkout ${gitBranch} | tee -a ${LOGFILE} 
sudo -u pi git status | tee -a ${LOGFILE} 
if sudo -u pi git pull | tee -a ${LOGFILE} | grep -sq "Already" ;then 
  export rcLocalUpdate_switch="doNothing"
else
  export rcLocalUpdate_switch="update"
fi
echo ${rcLocalUpdate}  | tee -a ${LOGFILE}

echo -e "\e[42;31mto stop this autorun script, set PROGRAM SWITCH on\e[m"

PORT1=23 #GPIO23=Pin16
gpio -g mode $PORT1 in

PORT2=24 #GPIO24=Pin18
gpio -g mode $PORT2 out

switch=`grep programmerSwitch\ =\ \"on\"  /home/pi/Documents/field_location/sendAllDataPicture/seendIM/debugControl.py`

if [ $? -eq 0 -o `gpio -g read $PORT1` -eq 1 ] ; then #シングルクオートの``が大切
#grepコマンドを実行した後、すぐに判定しないと$?が正しく動作しない
  echo program switch is ON  | tee -a ${LOGFILE}
  gpio -g write $PORT2 1
#   crontab < /home/pi/crontab
#   echo -e "\e[42;31mcrontab enabled\e[m"
  exit 0
fi

echo PROGRAM SWITCH is off. Now system start normally  | tee -a ${LOGFILE}

python /home/pi/Documents/field_location/sendAllDataPicture/sendIM/sendBMEDataToIM_periodically.py || ( echo python error ; my_shutdown )
exit 0
