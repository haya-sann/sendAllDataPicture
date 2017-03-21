#!/usr/bin/python
#coding: utf-8
#http://karaage.hatenadiary.jp/entry/2016/05/11/073000
#に解説があったもの。
#ソースコードは
#pythonでBME280モジュールを制御するプログラムをスイッチ・サイエンスさんが公開しています。ありがたやありがたや。以下のコマンドで、プログラムのダウンロード及び実行ができます。
#$ git clone https://github.com/SWITCHSCIENCE/BME280.git

#bme280_sample.py 

#from smbus2 import SMBus #この書き方では動かなかった。
#smbus2がないと言われて読み込めない
import sys
sys.path.append('/usr/local/lib/python3.4/dist-packages/')

import os
import smbus
import time
import httplib, urllib
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)
import RPi.GPIO as GPIO
import ambient
import spidev
import subprocess

spi = spidev.SpiDev()
spi.open(0, 0)
# Settings (for example)
#spi.max_speed_hz = 10000


sleep = 180 # how many seconds to sleep between posts to the channel
key = 'GYZD7GEVRB34DX5D' #Put your Thingspeak Channel Key here'  # Thingspeak channel to update

PORT1=23
PORT2=24

GPIO.setmode(GPIO.BCM) 
GPIO.setup(PORT1, GPIO.IN)
GPIO.setup(PORT2, GPIO.OUT)

bus_number  = 1
i2c_address = 0x76

#bus = SMBus(bus_number) #元はこうなっていた。
bus = smbus.SMBus(bus_number)


class BH1750():
	""" Implement BH1750 communication. """
	# Define some constants from the datasheet
	POWER_DOWN = 0x00 # No active state
	POWER_ON   = 0x01 # Power on
	RESET	  = 0x07 # Reset data register value

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
		mode2coeff =  2 if (self.mode & 0x03) == 0x01 else 1
		ratio = 1/(1.2 * (self.mtreg/69.0) * mode2coeff)
		return ratio*count

#	def wait_for_result(self, additional=0):#what is this mean? Setting 0 to parameter.
	def wait_for_result(self, additional):#what is this mean? Setting 0 to parameter.
		basetime = 0.018 if (self.mode & 0x03) == 0x03 else 0.128
		time.sleep(basetime * (self.mtreg/69.0) + additional)

#	def do_measurement(self, mode, additional_delay=0):#パラメータを0にリセットしている。これではadditional_delay の指定が有効にならないのでは？
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


digT = []
digP = []
digH = []

t_fine = 0.0


def writeReg(reg_address, data):
	bus.write_byte_data(i2c_address,reg_address,data)

def get_calib_param():
	calib = []
	
	for i in range (0x88,0x88+24):
		calib.append(bus.read_byte_data(i2c_address,i))
	calib.append(bus.read_byte_data(i2c_address,0xA1))
	for i in range (0xE1,0xE1+7):
		calib.append(bus.read_byte_data(i2c_address,i))

	digT.append((calib[1] << 8) | calib[0])
	digT.append((calib[3] << 8) | calib[2])
	digT.append((calib[5] << 8) | calib[4])
	digP.append((calib[7] << 8) | calib[6])
	digP.append((calib[9] << 8) | calib[8])
	digP.append((calib[11]<< 8) | calib[10])
	digP.append((calib[13]<< 8) | calib[12])
	digP.append((calib[15]<< 8) | calib[14])
	digP.append((calib[17]<< 8) | calib[16])
	digP.append((calib[19]<< 8) | calib[18])
	digP.append((calib[21]<< 8) | calib[20])
	digP.append((calib[23]<< 8) | calib[22])
	digH.append( calib[24] )
	digH.append((calib[26]<< 8) | calib[25])
	digH.append( calib[27] )
	digH.append((calib[28]<< 4) | (0x0F & calib[29]))
	digH.append((calib[30]<< 4) | ((calib[29] >> 4) & 0x0F))
	digH.append( calib[31] )
	
	for i in range(1,2):
		if digT[i] & 0x8000:
			digT[i] = (-digT[i] ^ 0xFFFF) + 1

	for i in range(1,8):
		if digP[i] & 0x8000:
			digP[i] = (-digP[i] ^ 0xFFFF) + 1

	for i in range(0,6):
		if digH[i] & 0x8000:
			digH[i] = (-digH[i] ^ 0xFFFF) + 1  

def measureLight():
	#bus = smbus.SMBus(0) # Rev 1 Pi uses 0
	bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
	sensor = BH1750(bus)
	print "Sensitivity: {:d}".format(sensor.mtreg)
	lightLevel = sensor.measure_high_res2()
	time.sleep(1)
	return lightLevel


def readData():
	data = []
	for i in range (0xF7, 0xF7+8):
		data.append(bus.read_byte_data(i2c_address,i))
	pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
	temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
	hum_raw  = (data[6] << 8)  |  data[7]
	
	temperature = compensate_T(temp_raw)
	pressure = compensate_P(pres_raw)
	humid = compensate_H(hum_raw)
	return temperature, pressure, humid

def compensate_P(adc_P):
	global  t_fine
	pressure = 0.0
	
	v1 = (t_fine / 2.0) - 64000.0
	v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * digP[5]
	v2 = v2 + ((v1 * digP[4]) * 2.0)
	v2 = (v2 / 4.0) + (digP[3] * 65536.0)
	v1 = (((digP[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)) / 8)  + ((digP[1] * v1) / 2.0)) / 262144
	v1 = ((32768 + v1) * digP[0]) / 32768
	
	if v1 == 0:
		return 0
	pressure = ((1048576 - adc_P) - (v2 / 4096)) * 3125
	if pressure < 0x80000000:
		pressure = (pressure * 2.0) / v1
	else:
		pressure = (pressure / v1) * 2
	v1 = (digP[8] * (((pressure / 8.0) * (pressure / 8.0)) / 8192.0)) / 4096
	v2 = ((pressure / 4.0) * digP[7]) / 8192.0
	pressure = pressure + ((v1 + v2 + digP[6]) / 16.0)  

	print "pressure : %7.2f hPa" % (pressure/100)
	return pressure/100

def compensate_T(adc_T):
	global t_fine
	v1 = (adc_T / 16384.0 - digT[0] / 1024.0) * digT[1]
	v2 = (adc_T / 131072.0 - digT[0] / 8192.0) * (adc_T / 131072.0 - digT[0] / 8192.0) * digT[2]
	t_fine = v1 + v2
	temperature = t_fine / 5120.0
	print "temp : %-6.2f ℃" % (temperature) 
	return temperature

def compensate_H(adc_H):
	global t_fine
	var_h = t_fine - 76800.0
	if var_h != 0:
		var_h = (adc_H - (digH[3] * 64.0 + digH[4]/16384.0 * var_h)) * (digH[1] / 65536.0 * (1.0 + digH[5] / 67108864.0 * var_h * (1.0 + digH[2] / 67108864.0 * var_h)))
	else:
		return 0
	var_h = var_h * (1.0 - digH[0] * var_h / 524288.0)
	if var_h > 100.0:
		var_h = 100.0
	elif var_h < 0.0:
		var_h = 0.0
	print "hum : %6.2f ％" % (var_h)
	return var_h

def setup():
	osrs_t = 1			#Temperature oversampling x 1
	osrs_p = 1			#Pressure oversampling x 1
	osrs_h = 1			#Humidity oversampling x 1
	mode   = 3			#Normal mode
	t_sb   = 5			#Tstandby 1000ms
	filter = 0			#Filter off
	spi3w_en = 0			#3-wire SPI Disable

	ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
	config_reg		= (t_sb << 5) | (filter << 2) | spi3w_en
	ctrl_hum_reg  = osrs_h

	writeReg(0xF2,ctrl_hum_reg)
	writeReg(0xF4,ctrl_meas_reg)
	writeReg(0xF5,config_reg)


setup()
get_calib_param()


if __name__ == '__main__':
	try:
		# today()メソッドで現在日付・時刻のdatetime型データの変数を取得
		d = datetime.datetime.today()
		#   ↑モジュール名.クラス名.メソッド名
 
		print 'データ取得時刻 == %s : %s\n' % (d, type(d)) # Microsecond(10^-6sec)まで取得

		temperature, pressure, humid = readData()
		print 'This is return value of temperature: %-6.2f ℃' % (temperature)
		print 'This is return value of pressure: %7.2f hPa' % (pressure)
		print 'This is return value of Humidity: %6.2f ％' % (humid)
		#Calculate CPU temperature of Raspberry Pi in Degrees C
		temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU temp
		lightLevel = measureLight()
		print "Light Level : {:3.2f} lx".format(lightLevel)
		#get voltage data from MCP3002
		# ch0
		resp = spi.xfer2([0x68, 0x00])
		voltage_ch1 = ((resp[0] << 8) + resp[1]) & 0x3ff
		time.sleep(1)
		# ch1
		resp = spi.xfer2([0x78, 0x00])
		voltage_ch2 = ((resp[0] << 8) + resp[1]) & 0x3ff
		print "Ch1 Voltage=" + str(voltage_ch1) + "/"+ str(round((voltage_ch1 / 38.75),3)),"Ch2 Voltage=" + str(voltage_ch2) + "/"+ str(round((voltage_ch2 / 38.75),3))

		voltage_ch1 = voltage_ch1 / 38.75
		voltage_ch2 = voltage_ch2 / 38.75

		time.sleep(5)
		params = urllib.urlencode({'field1': temp, 'field2': temperature, 'field3': pressure, 'field4': humid, 'field5': lightLevel, 'field6': voltage_ch1, 'field7': voltage_ch2, 'key':key }) 
		headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
		conn = httplib.HTTPConnection("api.thingspeak.com:80")
		try:
			conn.request("POST", "/update", params, headers)
			response = conn.getresponse()
			print 'CPU Temperature = %7.2f C' % temp
			print response.status, response.reason
			print 'please visit https://thingspeak.com/channels/176877/'
			data = response.read()
			conn.close()
			#send date to ambient
			ambi = ambient.Ambient(999,"ce9add17aefe75f8") # チャネルID、ライトキー
			r = ambi.send({"d1": temp, "d2": temperature, "d3": pressure, "d4": humid, "d5": lightLevel, "d6": voltage_ch1, "d7": voltage_ch2})
			#send date to さくらレンタルサーバー
			params_IM = urllib.urlencode({'c': "TsaJt1fR%5SyN",	'date': str(d), 'temp': temp, 'temperature': temperature, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'v0' : voltage_ch1, 'v1' : voltage_ch2 })

			conn = httplib.HTTPSConnection("mochimugi.sakura.ne.jp")
			conn.request("GET", "/IM/dev/webAPI/putDataAPI_withAuth.php?" + params_IM)
			print "connection requested"
			response = conn.getresponse()
			print response.status, response.reason
			data = response.read()
			print data
			conn.close()
				
		except:
				print "connection failed"
		#Programスイッチがオンになっているときは、パワーコントロールモジュールに電源オフ、再起動時間のセットをしない
		if (GPIO.input(PORT1) == 0):
			time.sleep(0.5)
			powerControlCommand = '/usr/sbin/i2cset -y 1 0x40 20 2 i'
			#10分後に起動。本番システムではここを11（55分後）などとする
			os.system(powerControlCommand) #import osが必要
			#time.sleep(5) #import timeが必要
			os.system('poweroff')
		GPIO.cleanup() # <- GPIOポートを開放
	except KeyboardInterrupt:
		pass

