
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import picamera
from picamera import PiCamera


with picamera.PiCamera() as camera:
    camera.resolution = (1024, 768)
    camera.start_preview()
    while True:
    #Camera warm-up time
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            break
