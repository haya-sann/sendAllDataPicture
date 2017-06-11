#!/bin/bash

for i in {1..10};
do ping -c1 192.168.12.104 &> /dev/null && echo SakuraServer is available; break;
echo -n .
done
echo Can not reach to Sakura Server.
