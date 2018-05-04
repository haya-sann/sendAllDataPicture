#!/usr/bin/python
#coding: utf-8
#このデバイス（田んぼカメラ）を外に設置する際は、サーバー上のwebAPIを正確に指すように調整するのを忘れないように

import httplib, urllib
import time
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)
import os
import commands
import sys
import ConfigParser
import ambient #ambientにデータを送込むライブラリ
import RPi.GPIO as GPIO
import json

GPIO_NO = 23 #PIN-16にプログラマースイッチを装着している。GPIO23に相当する

from bme280 import bmeRead
from retry import retry
from readBH1750 import measureLight

configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
configfile.read("/home/pi/Documents/mochimugi/config.conf")#絶対パスを使った

archive_server = configfile.get("settings", "host")  #サーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id
key = configfile.get("settings", "key")#ThingSpeak Channel write key
ambiKey = configfile.get("settings", "ambiKey")
imKey = configfile.get("settings", "imKey")


global_ipAddress =  commands.getoutput('hostname -I')
dir_path = os.path.abspath(os.path.dirname(__file__))#自分自身の居所情報


from __init__ import get_module_logger
logger = get_module_logger(__name__)

logger.propagate = True

v0=0.0
v1=0.0


def captureSensorData(i2c_address):
    #センサーからデータ収集するプログラムを実装
    #I2C、SPIなどを使ってデータキャプチャ
    try:
        temperature, pressure, humid = bmeRead(i2c_address)
    except IOError as e:
        logger.info("デバイスが見つかりません　：" + str(e))
        #sys.exit(False)
        temperature = None
        pressure = None
        humid = None

    return temperature, pressure/100, humid

def sendDataToAmbient():
    ambi = ambient.Ambient(999, ambiKey) # チャネルID、ライトキー
    r = ambi.send({"d1": cpu_temp, "d2": temp, "d3": pressure/100, "d4": humid, "d5": lightLevel, "d6": v0, "d7": v1})
    if r.status_code == 200:
        logger.info('successfuly sended data to Ambient')
    else:
        logger.info('Connection to AbmiData failed')

# def nonesafe_loads(obj):
#     if obj is not None:
#         return json.loads(obj)

def sendDataToIM():
#    fileObject = open(dir_path + '/mochimugi.log', 'r')#サーバーにログを送信する準備
    fileObject = open('/var/log/mochimugi.log', 'r')#サーバーにログを送信する準備
    mochimugiLog = fileObject.read()
    fileObject.close

    keyValue={'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure/100, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure, 'outer_humid': outer_humid}

    urlValue="{'c': str(imKey), 'date': str(d), "
    for value_label, value in keyValue.items():
        if value is not None:
            urlValue += "'" + value_label + ":" + str(value) + ","
    urlValue += "}"
    print (urlValue)
    print ("print (json.dumps(urlValue))" + json.dumps(urlValue))
    params_IM = urllib.urlencode(json.dumps(urlValue))

#    params_IM = urllib.urlencode({'c': str(imKey), 'date': str(d), 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure/100, 'humid': humid, 'lux' : lightLevel, 'outer_temp': nonesafe_loads(outer_temp), 'outer_pressure': nonesafe_loads(outer_pressure), 'outer_humid': nonesafe_loads(outer_humid), 'log':mochimugiLog, 'deploy' : "sandBox" })    

#    params_IM = urllib.urlencode({'c': str(imKey), 'date': str(d), 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure/100, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure/100, 'outer_humid': outer_humid, 'log':mochimugiLog, 'deploy' : "sandBox" })    
    conn = httplib.HTTPSConnection("mochimugi.sakura.ne.jp")
    conn.request("GET", "/IM/dev/webAPI/putDataAPI_withAuth.php?" + params_IM)
    print ("connection requested")
    response = conn.getresponse()
    logger.info("Server respond:" + str(response.status) + str(response.reason))
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
data1= '{"outer_temp":outer_temp}'

try:
    lightLevel =0 #init light level
    lightLevel = measureLight()
except Exception as measureLightError:
    logger.debug("Error occured in measureLight: " + str(measureLightError))
 

# logger.info("収集データ確認：" + '{:.2f}'.format(temp) +"/" + '{:.2f}'.format(pressure) +"/" + '{:.2f}'.format(humid) +"/" + '{:.2f}'.format(outer_temp) +"/" + '{:.2f}'.format(outer_pressure) +"/" + '{:.2f}'.format(outer_humid))

#Send atmosphere data to AmbiData
sendDataToAmbient()

@retry()
def sendPowerCommand():
    os.system(powerControlCommand) #import osが必要
        #成功するまで繰り返す
	#retryのInstallationは
	#$ pip install retry
	#from retry import retry
    logger.info("sended PowerCommand" + str(powerControlCommand))

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_NO, GPIO.IN)

if GPIO.input(GPIO_NO) == 0:
    try:
        powerControlCommand = '/usr/sbin/i2cset -y 1 0x40 60 1 i'


        sendPowerCommand()
        time.sleep(5)

    except IOError:
        logger.info('IOErrorです。デバイスが認識できません')
    #		logger.exception('Error in read bme280: %s', err)
    finally:
        logger.info('PowerControl設定の処理を終わりました。エラーログも確認してください')


print("Program exit\n")

#send data to さくらレンタルサーバー        
sendDataToIM()

if GPIO.input(GPIO_NO) == 0:
    print('システムを終了します')
    os.system('sudo poweroff')

GPIO.cleanup()
