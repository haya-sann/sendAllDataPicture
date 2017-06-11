#!/bin/bash

trap "echo Encounterd error; exit 1" ERR

function my_shutdown2() {
    powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x41 15 0 i"
    if [eval $powerControlCommand 2>&1 | grep "Error"]; then
        echo "Error encountered"
        exit 1
        fi
    echo system will poweroff after 10 seconds, and reboot
    sleep 10
    sudo poweroff
    exit 0
}
my_shutdown2
