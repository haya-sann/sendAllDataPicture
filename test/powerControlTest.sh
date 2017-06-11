#!/bin/bash

function my_shutdown2() {
    powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x40 15 0 i"
    eval $powerControlCommand 2>&1 | tee -a ./logTest.log

    trap "echo Encounterd error; exit 1" ERR
    echo system will poweroff after 10 seconds, and reboot
    sleep 10
    sudo poweroff
    exit 0
}
my_shutdown2
