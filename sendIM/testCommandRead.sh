#!/bin/bash

switch=`grep -o off debugControl.py` #シングルクオーテーションじゃなくてバッククオート
switch= echo ${switch#*""}
echo $switch

