#!/usr/bin/python
#coding: utf-8
import sys
sys.path.append('/usr/local/lib/python3.4/dist-packages/')

from  subprocess import Popen, PIPE, call
import time

x=0
file = "StandardError.log"

powerMonagementModule_controlCommand = 'sudo /usr/sbin/i2cset -y 1 0x40 10 ' + str(x) + ' i'

print "sending Power Control Command : "+powerMonagementModule_controlCommand

for i in range(1,5):
    try:
        process = Popen(powerMonagementModule_controlCommand, shell=True, stdout=PIPE, stderr=PIPE)
        output, err = process.communicate()

        if "Error" in err:
            print "Error encounterd"
        else:
            print >>sys.stderr, "I2C command success: ", str(i) + " time retry. System will powerdown and reboot imedeately"
            call('sudo poweroff', shell=True)
            break
    except OSError as e:
        print ("System will reboot")
        call("sudo reboot")

