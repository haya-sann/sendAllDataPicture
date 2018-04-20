#!/usr/bin/python
#coding: utf-8

import smbus
import time

from logging import getLogger
logger = getLogger(__name__) 

bus_number = 1
#bus = SMBus(bus_number) #元はこうなっていた。
bus = smbus.SMBus(bus_number)

class BH1750():
    """ Implement BH1750 communication. """
    # Define some constants from the datasheet
    POWER_DOWN = 0x00 # No active state
    POWER_ON = 0x01 # Power on
    RESET = 0x07 # Reset data register value

    # Start measurement at 0.5lx resolution. Time typically 120ms
    # Device is automatically set to Power Down after measurement.
    ONE_TIME_HIGH_RES_MODE_2 = 0x21

    def __init__(self, bus, addr=0x23):
        self.bus = bus
        self.addr = addr
        self.power_down()
        self.set_sensitivity()

    def _set_mode(self, mode):
        self.mode = mode
        self.bus.write_byte(self.addr, self.mode)

    def power_down(self):
        self._set_mode(self.POWER_DOWN)

    def power_on(self):
        self._set_mode(self.POWER_ON)

    def reset(self):
        self.power_on() #It has to be powered on before resetting
        self._set_mode(self.RESET)

    def oneshot_high_res2(self):
        self._set_mode(self.ONE_TIME_HIGH_RES_MODE_2)

    def set_sensitivity(self, sensitivity=150):
        """ Set the sensor sensitivity.
            Valid values are 31 (lowest) to 254 (highest), default is 150.
        """
        self.mtreg = sensitivity
        self.power_on()
        self._set_mode(0x40 | (self.mtreg >> 5))
        self._set_mode(0x60 | (self.mtreg & 0x1f))
        self.power_down()

    def get_result(self):
        """ Return current measurement result in lx. """
        data = self.bus.read_word_data(self.addr, self.mode)
        count = data >> 8 | (data&0xff)<<8
        mode2coeff = 2 if (self.mode & 0x03) == 0x01 else 1
        ratio = 1/(1.2 * (self.mtreg/69.0) * mode2coeff)
        return ratio*count

#    def wait_for_result(self, additional=0):#what is this mean? Setting 0 to parameter.
    def wait_for_result(self, additional):#what is this mean? Setting 0 to parameter.
        basetime = 0.018 if (self.mode & 0x03) == 0x03 else 0.128
        time.sleep(basetime * (self.mtreg/69.0) + additional)

#    def do_measurement(self, mode, additional_delay=0):
#パラメータを0にリセットしている。これではadditional_delay の指定が有効にならないのでは？
    def do_measurement(self, mode, additional_delay):
        """
        Perform complete measurement using command
        specified by parameter mode with additional
        delay specified in parameter additional_delay.
        Return output value in Lx.
        """
        self.reset()
        self._set_mode(mode)
        self.wait_for_result(additional=additional_delay)
        return self.get_result()

    def measure_high_res2(self, additional_delay=1):#was 0. But didn't work.
        return self.do_measurement(self.ONE_TIME_HIGH_RES_MODE_2, additional_delay)


def measureLight():
    for lightSense in range(1, 20):
        try:
            logger.info("Sensing light level...")
            #bus = smbus.SMBus(0) # Rev 1 Pi uses 0
            bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
            sensor = BH1750(bus)
            logger.info("Light Sensitivity: {:d}".format(sensor.mtreg))
            lightLevel = sensor.measure_high_res2()
            logger.info("Light Level: " + str(lightLevel))
            return lightLevel
            break
        except Exception as error_inMeasureLight:
            logger.debug("Error during sensing light data: " + str(error_inMeasureLight) + " / " + str(lightSense) + " times trial")
            time.sleep(2)
    else:
        logger.debug("Error during sensing light data after : " + str(lightSense) +" times trial")

if __name__=="__main__":
    print(measureLight())
