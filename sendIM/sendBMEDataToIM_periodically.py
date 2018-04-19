#!/usr/bin/python
#coding: utf-8

import httplib, urllib
import time
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)
import os
import commands
import sys
import ConfigParser
import ambient #ambientにデータを送込むライブラリ

from bme280 import bmeRead
from retry import retry

configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
configfile.read("/home/pi/Documents/mochimugi/config.conf")#絶対パスを使った

archive_server = configfile.get("settings", "host")  #サーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id
key = configfile.get("settings", "key")#ThingSpeak Channel write key
ambiKey = configfile.get("settings", "ambiKey")
imKey = configfile.get("settings", "imKey")


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
v0=0.0
v1=0.0


def captureSensorData(i2c_address):
    #センサーからデータ収集するプログラムを実装
    #I2C、SPIなどを使ってデータキャプチャ
    try:
        temperature, pressure, humid = bmeRead(i2c_address)
    except IOError as e:
        logger.info("デバイスが見つかりません　：" + str(e))
        sys.exit(False)

    return temperature, pressure, humid

def measureLight():
    for lightSense in range(1, 20):
        try:
            logger.info("Sensing light level...")
            bus = smbus.SMBus(0) # Rev 1 Pi uses 0
            #bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
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


def sendDataToAmbient():
    ambi = ambient.Ambient(999, ambiKey) # チャネルID、ライトキー
    r = ambi.send({"d1": cpu_temp, "d2": temp, "d3": pressure/100, "d4": humid, "d5": lightLevel, "d6": v0, "d7": v1})
    if r.status_code == 200:
        logger.info('successfuly sended data to Ambient')
    else:
        logger.info('Connection to AbmiData failed')

def sendDataToIM():
    fileObject = open(dir_path + '/mochimugi.log', 'r')#サーバーにログを送信する準備
    mochimugiLog = fileObject.read()
    fileObject.close

    params_IM = urllib.urlencode({'c': str(imKey), 'date': str(d), 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure/100, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure/100, 'outer_humid': outer_humid, 'log':mochimugiLog, 'deploy' : "sandBox" })
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

try:
    lightLevel =0 #init light level
    lightLevel = measureLight()
except Exception as measureLightError:
    logger.debug("Error occured in measureLight: " + str(measureLightError))
 

logger.info("収集データ確認：" + '{:.2f}'.format(temp) +"/" + '{:.2f}'.format(pressure) +"/" + '{:.2f}'.format(humid) +"/" + '{:.2f}'.format(outer_temp) +"/" + '{:.2f}'.format(outer_pressure) +"/" + '{:.2f}'.format(outer_humid))

#Send atmosphere data to AmbiData
sendDataToAmbient()

#send data to さくらレンタルサーバー

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
