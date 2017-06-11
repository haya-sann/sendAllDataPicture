#!/bin/bash

function my_shutdown2() {
  powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x40 15 0 i"
  eval $powerControlCommand | tee -a ./test.log
  sleep 10
  sudo poweroff
  echo system will poweroff after 10 seconds, and reboot
  exit 0
}

my_shutdown2
