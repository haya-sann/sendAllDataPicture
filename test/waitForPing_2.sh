#!/bin/bash

function waitForPing1() {
    # Wait for Network to be available.
for i in {1..3};
    do ping -c1 192.168.12.8 &> /dev/null && (echo Server is available) && break; 
    echo -n .
    done
[ $i = 3 ] && echo Can not reach Server && return 0
echo just test 
return 0
}

function waitForPing2() {
    # Wait for Network to be available.
for i in {1..3};
    do ping -c1 google.com &> /dev/null && (echo Server is available) && break; 
    echo -n .
    done
[ $i = 3 ] && ( echo Can not reach Server ; return 1)
echo just test, function 2 
return 0
}

waitForPing1 || ( echo network1 error )
waitForPing2 || ( echo network2 error )
