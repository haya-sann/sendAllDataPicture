#!/bin/bash

function waitForPing() {
    # Wait for Network to be available.
for i in {1..5};
    do ping -c1 192.168.12.8 &> /dev/null && (Server is available) && break; 
    echo -n .
    done
[ $i = 5 ] && ( echo Can not reach to Sakura Server ; exit 1)
return 0
}


waitForPing || ( echo network error ; exit 1 )
echo network available
