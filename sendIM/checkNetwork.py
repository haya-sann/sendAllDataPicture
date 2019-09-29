import subprocess
if subprocess.call (['bash','test_waitForPing.sh']) == 0:
        print("Server can be reached")
else:
        print ('Error. Network might down. Reboot right away')
        subprocess.call(['sudo','reboot'])
