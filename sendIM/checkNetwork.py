import os
try:
        if os.system ("bash test_waitForPing.sh") !=0:
                raise Exception('Can not reach the server')
        print("Server can be reached")
except Exception as e:
        print ('Error. ' + str(e))
        os.system('sudo reboot')
