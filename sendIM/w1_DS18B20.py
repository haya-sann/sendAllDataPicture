#!/usr/bin/python
# -*- coding: utf-8 -*-
#inspired from http://qiita.com/masato/items/cf5a27af696a27b73b86
#Temperature sensor DS18B20 connected to Raspberry Pi GPIO4=Pin7

from w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()

celsius = sensor.get_temperature()
print celsius
fahrenheit = sensor.get_temperature(W1ThermSensor.DEGREES_F)
all_units = sensor.get_temperatures([W1ThermSensor.DEGREES_C, W1ThermSensor.DEGREES_F, W1ThermSensor.KELVIN])

print("celsius:    {0:.3f}".format(celsius))
print("fahrenheit: {0:.3f}".format(fahrenheit))
s = "celsius: {0:.3f}, fahrenheit: {1:.3f}, kelvin: {2:.3f}"
print(s.format(*all_units))
