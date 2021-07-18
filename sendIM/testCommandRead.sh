#!/bin/bash

switch=`grep -o "programmerSwitch = \"on\"" debugControl.py` #シングルクオーテーションじゃなくてバッククオート

echo $switch
switch=`echo $switch | sed -e s/^programmerSwitch\ =\ \"on\"/on/`
echo $switch

