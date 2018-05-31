#!/usr/bin/python
#coding: utf-8
#このデバイス（田んぼカメラ）を外に設置する際は、サーバー上のwebAPIを正確に指すように調整するのを忘れないように
#設置する機器の対応サーバーに応じて指定するconfig.confを切替えるのを忘れずに
#ex: configfile.read("/home/pi/Documents/field_location/kawagoe_config.conf")


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

GPIO_NO = 23 #PIN-16にプログラマースイッチを装着している。GPIO23に相当する

from bme280 import bmeRead
from retry import retry
from readBH1750 import measureLight
from read4chAnalog import read4ch

from sendMail import send, create_message

from w1_DS18B20 import read_soil_temp


configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
#configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った
configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った

host_IM = configfile.get("settings", "host")
archive_server = configfile.get("settings", "ftpsHost")  #ftpsサーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id
key = configfile.get("settings", "key")#ThingSpeak Channel write key
ambiKey = configfile.get("settings", "ambiKey")
imKey = configfile.get("settings", "imKey")
from_addr = configfile.get("settings", "mailAddress")
mailPass = configfile.get("settings", "mailPass")


global_ipAddress =  commands.getoutput('hostname -I')
dir_path = os.path.abspath(os.path.dirname(__file__))#自分自身の居所情報


from __init__ import get_module_logger
logger = get_module_logger(__name__)

logger.propagate = True

v0=v1=soil1=soil2=soil_temp=0.0

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

    return temperature, pressure, humid

def sendDataToAmbient():
    ambi = ambient.Ambient(999, ambiKey) # チャネルID、ライトキー
    r = ambi.send({"d1": cpu_temp, "d2": temp, "d3": pressure, "d4": humid, "d5": lightLevel, "d6": v0, "d7": v1})
    if r.status_code == 200:
        logger.info('successfuly sended data to Ambient')
    else:
        logger.info('Connection to AbmiData failed')

# def nonesafe_loads(obj):
#     if obj is not None:
#         return json.loads(obj)

def sendDataToIM():
#    fileObject = open(dir_path + '/field_location.log', 'r')#サーバーにログを送信する準備
    fileObject = open('/var/log/field_location.log', 'r')#サーバーにログを送信する準備
    field_locationLog = fileObject.read()
    fileObject.close

    keyValue={'c': imKey, 'date': d, 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure, 'outer_humid': outer_humid,  'v0':v0, 'v1':v1, 'soil1':soil1, 'soil2':soil2, 'soil_temp':soil_temp, 'deploy' : 'sandBox', 'log':field_locationLog }

    valueToSend={}
    for value_label, value in keyValue.items():
        if value is not None:
            valueToSend[value_label]=value

    params_IM = urllib.urlencode(valueToSend)#最終的に送信データを用意（今回アクセスのログ含む）

    logger.info ("paramsIM:" + params_IM)

    conn = httplib.HTTPSConnection(host_IM)
    #conn = httplib.HTTPConnection(host_IM)
    conn.request("GET", "/IM/im_build/webAPI/putDataAPI_withAuth.php?" + params_IM)
    response = conn.getresponse()
    logger.info("Server respond:" + str(response.status) + str(response.reason))
    data = response.read()
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

values = [0.0]*4
read4ch(values)
logger.info('| {0:>6,.2f} | {1:>6,.2f} | {2:>6,.2f} | {3:>6,.2f} |'.format(*values))
v0=values[0]
v1=values[1]
soil1=values[2]
soil2=values[3]

soil_temp = read_soil_temp()

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
        logger.info('IOError。デバイスが認識できません')
    	logger.exception('Error in read bme280: %s', err)
    finally:
        logger.info('PowerControl設定の処理を終わりました。エラーログも確認してください')
else:
    logger.info("Programmer switch is ON. Continue to proceed\n")



#send data to host_IM
sendDataToIM()

to_addr = "haya.biz@gmail.com"

#件名と本文
subject = "田んぼカメラから"
body = """ログデータを送ります。これは詳細なログです。
ログはconsoleアプリで読んでください。
""" + "\n"


#添付ファイル設定(text.txtファイルを添付)
mime={'type':'text', 'subtype':'comma-separated-values'}
#    attach_file={'name':'boot.log', 'path':'/var/log/wifi.log'}
#ここでエンコーディングをutf8にするといいはず。
attach_file={'name':'field_location.log','path':'/var/log/field_location.log'}
 
msg = create_message(from_addr, to_addr, subject, body, mime, attach_file)
send(from_addr, to_addr, msg)

if GPIO.input(GPIO_NO) == 0:
    print('システムを終了します')
    os.system('sudo poweroff')

GPIO.cleanup()
