#!/usr/bin/python
#coding: utf-8

import subprocess
import time

x=0

file = "StandardError.log"

powerMonagementModule_controlCommand = 'sudo /usr/sbin/i2cset -y 1 0x41 10 ' + str(x) + ' i'

print "sending Power Control Command : "+powerMonagementModule_controlCommand

try:
    retcode = subprocess.call(powerMonagementModule_controlCommand, shell=True)
    if retcode < 0:
        print >>subprocess.sys.stderr, "Child was terminated by signal", -retcode
    else:
        print >>subprocess.sys.stderr, "Child returned", retcode
except OSError as e:
    print >>subprocess.sys.stderr, "Execution failed:", e

time.sleep(5)
#call('sudo poweroff', shell=True)

