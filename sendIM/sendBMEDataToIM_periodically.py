#!/usr/bin/python
#coding: utf-8

import httplib, urllib
import time
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)
import os
import commands
import sys

from bme280 import bmeRead
from retry import retry


global_ipAddress =  commands.getoutput('hostname -I')
dir_path = os.path.abspath(os.path.dirname(__file__))

import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(name)s] %(asctime)s %(levelname)s : %(message)s')
streamHandler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)


streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler(dir_path + '/mochimugi.log', mode='w', encoding=None, delay=0)
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.info('logging.warning:Global IP Address:%s', global_ipAddress)
logger.info(dir_path + str(__file__) + "is running. 2018/04/10の改良版です")


temperature =0.0
pressure = 0.0
humid = 0.0

def captureSensorData(i2c_address):
    #センサーからデータ収集するプログラムを実装
    #I2C、SPIなどを使ってデータキャプチャ
    try:
        temperature, pressure, humid = bmeRead(i2c_address)
    except IOError as e:
        logger.info("デバイスが見つかりません　：" + str(e))
        sys.exit(False)

    return temperature, pressure, humid

def sendDataToIM():
    fileObject = open(dir_path + '/mochimugi.log', 'r')#サーバーにログを送信する準備
    mochimugiLog = fileObject.read()
    fileObject.close

    params_IM = urllib.urlencode({'c': "TsaJt1fR5SyN", 'date': str(d), 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure/100, 'humid': humid,  'outer_temp': outer_temp, 'outer_pressure': outer_pressure/100, 'outer_humid': outer_humid, 'log':mochimugiLog, 'deploy' : "sandBox" })
    #params_IM = urllib.urlencode({'c': "TsaJt1fR5SyN", 'date': str(d), 'temp': temp, 'temperature': temperature, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'deploy' : "sandBox" })

    conn.request("GET", "/IM/dev/webAPI/putDataAPI_withAuth.php?" + params_IM)
    print ("connection requested")
    response = conn.getresponse()
    print (response.status, response.reason)
    data = response.read()
    print (data)
    conn.close()

# today()メソッドで現在日付・時刻のdatetime型データの変数を取得
d = datetime.datetime.today()

print ('データ取得時刻 == %s : %s\n' % (d, type(d))) # Microsecond(10^-6sec)まで取得

#Calculate CPU temperature of Raspberry Pi in Degrees C
cpu_temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU temp

i2c_address = 0x76
temp, pressure, humid = captureSensorData(i2c_address)

i2c_address = 0x77
outer_temp, outer_pressure, outer_humid = captureSensorData(i2c_address)

logger.info("収集データ確認：" + '{:.2f}'.format(temp) +"," + '{:.2f}'.format(pressure) +"," + '{:.2f}'.format(humid) +"," + '{:.2f}'.format(outer_temp) +"," + '{:.2f}'.format(outer_pressure) +"," + '{:.2f}'.format(outer_humid))

#send date to さくらレンタルサーバー

@retry()
def sendPowerCommand():
    os.system(powerControlCommand) #import osが必要
        #成功するまで繰り返す
	#retryのInstallationは
	#$ pip install retry
	#from retry import retry
    logger.info("sended PowerCommand" + str(powerControlCommand))

try:
    powerControlCommand = '/usr/sbin/i2cset -y 1 0x40 60 1 i'
    conn = httplib.HTTPSConnection("mochimugi.sakura.ne.jp")


    sendPowerCommand()
    time.sleep(5)

except IOError:
    logger.info('IOErrorです。デバイスが認識できません')
#		logger.exception('Error in read bme280: %s', err)
finally:
    logger.info('処理を正常に終了しました。これはオートアップデートのテストメッセージ')
        
sendDataToIM()

print('システムを終了します')
os.system('sudo poweroff')
