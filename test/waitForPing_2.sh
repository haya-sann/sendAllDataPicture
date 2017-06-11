#!/bin/bash

function waitForPing1() {
    # Wait for Network to be available.
for i in {1..3};
    do ping -c1 192.168.12.8 &> /dev/null && (Server is available) && break; 
    echo -n .
    done
[ $i == 3 ] && ( echo Can not reach to Server ; exit 1)
return 1
}

function waitForPing2() {
    # Wait for Network to be available.
for i in {1..3};
    do ping -c1 127.0.0.1 &> /dev/null && (Server is available) && break; 
    echo -n .
    done
[ $i == 3 ] && ( echo Can not reach to Server ; exit 1)
return 1
}

waitForPing1 || ( echo network error ; exit 1 )
waitForPing2 || ( echo network error ; exit 1 )
echo network available
