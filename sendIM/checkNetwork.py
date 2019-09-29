import subprocess
try:
        if subprecess.call ("bash test_waitForPing.sh") !=0:
                raise Exception('Can not reach the server')
        print("Server can be reached")
except Exception as e:
        print ('Error. ' + str(e))
        subprecess.call('sudo reboot')
