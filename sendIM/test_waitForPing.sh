#!/bin/bash
function waitForPing1 (){
    # Wait for Network to be available.
for i in {1..3};
    do ping -c1 ciao-kawagoesatoyama.ssl-lolipop.jp &> /dev/null && break;
    echo -n .
    done
[ $i = 3 ] && exit 1
return 0
}

waitForPing1
