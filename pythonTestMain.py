#!/usr/bin/env python
# coding:UTF-8


x=65.6
x = int(x / 5)
timeToOff = 40
powerControlCommand = 'sudo /usr/sbin/i2cset -y 1 0x40 ' + str(timeToOff) + ' ' + str(x) + ' i'
#40秒後に電源オフ、最後のパラメーター×5分後に起動

print('電源モジュールに送信するコマンド用意：' + powerControlCommand + ':40秒後にシャットダウン、最後のパラメーター' +str(x*5) + '分後に起動')


