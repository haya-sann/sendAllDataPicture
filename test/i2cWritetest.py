#!/usr/bin/python
#coding: utf-8

import subprocess
import time

x=0

powerMonagementModule_controlCommand = 'sudo /usr/sbin/i2cset -y 1 0x41 10 ' + str(x) + ' i'

print "sending Power Control Command : "+powerMonagementModule_controlCommand

try:
    retcode = call(powerMonagementModule_controlCommand, shell=True)
    if retcode < 0:
        print("Call ended", -retcode, file=sys.stderr)
    else:
        print("Child returned", retcode, file=sys.stderr)
except OSError as e:
    print("Execution failed:", e, file=sys.stderr)

time.sleep(5)
#call('sudo poweroff', shell=True)

