
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import picamera
from picamera import PiCamera


with picamera.PiCamera() as camera:
    camera.resolution = (1024, 768)
    camera.start_preview()
    #Camera warm-up time
    time.sleep(2)
    # camera.capture('/home/pi/nas/201607311122.jpg')
