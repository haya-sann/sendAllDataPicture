#!/usr/bin/python
# -*- coding: utf-8 -*-
from w1thermsensor import W1ThermSensor

sensor = W1ThermSensor()
celsius = sensor.get_temperature()
fahrenheit = sensor.get_temperature(W1ThermSensor.DEGREES_F)
all_units = sensor.get_temperatures([W1ThermSensor.DEGREES_C, W1ThermSensor.DEGREES_F, W1ThermSensor.KELVIN])

print("celsius:    {0:.3f}".format(celsius))
print("fahrenheit: {0:.3f}".format(fahrenheit))
s = "celsius: {0:.3f}, fahrenheit: {1:.3f}, kelvin: {2:.3f}"
print(s.format(*all_units))
