#!/usr/bin/python
# -*- coding: utf-8 -*-
#inspired from http://qiita.com/masato/items/cf5a27af696a27b73b86
#これの最後部に解説あり。
# $ cd ~/python_apps
# $ git clone https://github.com/timofurrer/w1thermsensor.git 
# $ cd w1thermsensor
# $ sudo python setup.py install
#Temperature sensor DS18B20 connected to Raspberry Pi GPIO4=Pin7

from w1thermsensor import W1ThermSensor

#from logging import getLogger

from __init__ import get_module_logger
logger = get_module_logger(__name__)

logger.propagate = True

def read_soil_temp():
    sensor = W1ThermSensor()
    celsius = sensor.get_temperature()
    logger.info('土の温度は：' + str(celsius))
    return celsius
