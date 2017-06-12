#!/usr/bin/python
#coding: utf-8
import sys
sys.path.append('/usr/local/lib/python3.4/dist-packages/')

from  subprocess import Popen, PIPE, call
import time

x=0
file = "StandardError.log"

powerMonagementModule_controlCommand = 'sudo /usr/sbin/i2cset -y 1 0x41 10 ' + str(x) + ' i'

print "sending Power Control Command : "+powerMonagementModule_controlCommand

process = Popen(powerMonagementModule_controlCommand, shell=True, stdout=PIPE, stderr=PIPE)
output, err = process.communicate()

if "Error" in err:
    print "Error encounterd"
else:
    print >>sys.stderr, "I2C command success"
    call('sudo poweroff', shell=True)

    
print output, err

#     if "Error" in subprocess.sys.stderr:
#         print >>subprocess.sys.stderr, "I2C Write command failed"
#     else:
#         print >>subprocess.sys.stderr, "I2C command success", retcode
#         subprocess.call('sudo poweroff', shell=True)
# except OSError as e:
#     print >>subprocess.sys.stderr, "Execution failed:", e
