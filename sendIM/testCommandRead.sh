#!/bin/bash

grep -o "programmerSwitch = \"on\"" debugControl.py #シングルクオーテーションじゃなくてバッククオート


if [ $? -eq 0 ] ; then #直前のコマンド実行結果を$?が保持している。これを調べれば検査したい文脈があるかどうか分かる
#grepコマンドを実行した後、すぐに判定しないと$?が正しく動作しない
  echo program switch is ON
else echo program switch is OFF
fi
