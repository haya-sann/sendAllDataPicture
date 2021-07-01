#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""File: echo_simple_once.py（sr04_Bluetin.py）
pip install Bluetin_Echo
rootからも呼ぶことがあるので、
sudo pip install Bluetin_Echo としておくこと
さらに、
$ sudo pip install datetime
も必要
https://github.com/MarkAHeywood/Bluetin_Python_Echo/blob/master/examples/echo_simple_once.py
""" 
# 
from bme280 import bmeRead
from retry import retry
from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)
logger.propagate = True


import numpy as np
from Bluetin_Echo import Echo # Import necessary libraries.      
import datetime, time

TRIGGER_PIN = 20    # Define GPIO pin constants. 
ECHO_PIN = 21
# # Initialise Sensor with pins, speed of sound.  
samples = 5  # # Measure Distance 5 times, return average.

#センサーからデータ収集するプログラムを実装
#I2C、SPIなどを使ってデータキャプチャ

@retry(tries=3)
def depth_measure_retry_3(temperature):
    dt_now = datetime.datetime.now()
    speed_of_sound = 331.50 + 0.606681 * temperature
    echo = Echo(TRIGGER_PIN, ECHO_PIN, speed_of_sound) 
    depth_result =  102.717 - echo.read('cm', samples) #実際の水高を求める
    print(dt_now, depth_result)  # Print result.  
    if -5 > depth_result or depth_result > 80:  
        print("Out of range")  # Print exception.  
        raise Exception()
    depth_result = None
    return depth_result

def sr04_read(temperature):
    repeat =5
    depth = np.arange(repeat, dtype=float)
    count = 0
    # while True:
    while (count < repeat):
        depth[count] =  depth_measure_retry_3(temperature) #実際の水高を求める
        count += 1
        time.sleep(1)
    else: #指定回数終わったら
        print("\nDepth measurement is finished normally.")
        depth = np.delete(depth,(np.argmax(depth),np.argmin(depth)),0)
        print("\n除最大最小：",(depth))
        average_depth = np.mean(depth)
        print("\n平均値：",average_depth)
        return average_depth
        echo.stop() # Reset GPIO Pins



if __name__ == '__main__':
	try:
		print ('')
		depth = sr04_read()
	except KeyboardInterrupt:
		pass

