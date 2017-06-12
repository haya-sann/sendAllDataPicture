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
    if "Error" in subprocess.sys.stderr:
        print >>subprocess.sys.stderr, "I2C Write command failed"
    else:
        print >>subprocess.sys.stderr, "I2C command success", retcode
        subprocess.call('sudo poweroff', shell=True)
except OSError as e:
    print >>subprocess.sys.stderr, "Execution failed:", e
