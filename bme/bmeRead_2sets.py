#coding: utf-8

import os
import bme280
import os.path

from retry import retry

from logging import getLogger, StreamHandler, handlers, Formatter, DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)

logger.debug('hello, program started')

# ログ出力
formatter = Formatter(
    fmt="%(asctime)s:[%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
file_handler = handlers.RotatingFileHandler(
    os.path.join(os.path.abspath(os.path.dirname(__file__)), "log", "bme280.log"),
    maxBytes=50000000, backupCount=5)
file_handler.setFormatter(formatter)
file_handler.setLevel(DEBUG)
logger.addHandler(file_handler)

reg_i2c_address = 0x76

print ''
print 'センサー1：'
temperature, pressure,humid = bme280.bmeRead(reg_i2c_address)
print "temp : %-6.2f ℃" % (temperature) 
print "from main program; pressure : %7.2f hPa" % (pressure/100)
print "hum : %6.2f ％" % (humid)

reg_i2c_address = 0x77
print ''
print 'センサー2：'
temperature, pressure,humid = bme280.bmeRead(reg_i2c_address)
print "temp : %-6.2f ℃" % (temperature) 
print "from main program; pressure : %7.2f hPa" % (pressure/100)
print "hum : %6.2f ％" % (humid)


