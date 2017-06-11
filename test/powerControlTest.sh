#!/bin/bash

function my_shutdown2() {
    powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x40 15 0 i"

    for i in {1..5}
    do
        if eval $powerControlCommand |& grep "Error"; then
        echo "Error encountered"
        sleep 1
        else
        break
        fi
    done


[ $i = 5 ] && echo error writing I2C && return 1
    echo system will poweroff after 10 seconds, and reboot
    sleep 10
    sudo poweroff
    return 0
}

my_shutdown2
