#!/usr/bin/python
#coding: utf-8
#このデバイス（田んぼカメラ）を外に設置する際は、サーバー上のwebAPIを正確に指すように調整するのを忘れないように
#設置する機器の対応サーバーに応じて指定するconfig.confの中身を対応するサーバー情報に書き換えるのを忘れずに
#ex: configfile.read("/home/pi/Documents/field_location/config.conf")
#rc.localを修正したければ、この中でアップデートを行う。rcLocalUpdate.shという中間ファイルを経由して、これを/etc/rc.localに上書きする仕組み
#したがって、rc.localを書き直したければ、rcLocalUpdate.shを更新してやれば良い。

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
from ftps import sendLog_ftps
from ftps import send_ftps
import picamera

try:
    DEPLOY_SWITCH = os.environ['DEPLOY']
except: #rc.localからexportされて送られるはずのDEPLYがない場合は
    DEPLOY_SWITCH = "sandBox"

global_ipAddress =  commands.getoutput('hostname -I')
dir_path = os.path.abspath(os.path.dirname(__file__))#自分自身の居所情報

from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)

logger.propagate = True


try:
    import rcLocalUpdate 
    rcLocalUpdate.updateRCLocal()
    logger.info("Successfully copied updated rc.local file")
except :
    logger.debug("failed update rc.local file. Please check location of rcLocalUpdate.py")

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

logger.info("公開先は：" + DEPLOY_SWITCH)

if DEPLOY_SWITCH == "distribution":
    put_directory = 'daily_timelapse' #Both Local and Remote Server has same directory
elif DEPLOY_SWITCH == "sandBox":
    put_directory = 'daily_timelapseSandbox' #Both Local and Remote Server has same directory

logger.info("資料の保存先は：" + put_directory)

#カメラ撮影準備
localFile_name = ""
pictureBrightness =55
pictureContrast = 10

hourToBegin = 1 #カメラを動作開始させる時刻
hourToStop = 24 #カメラを完全休止させる時刻
everyMinutes = 10 #何分おきに撮影するのかをセット


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
    #keyValue={'c': imKey, 'date': d, 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure, 'outer_humid': outer_humid,  'v0':v0, 'v1':v1, 'soil1':soil1, 'soil2':soil2, 'soil_temp':soil_temp, 'deploy' : 'sandBox', 'log':field_locationLog }

    keyValue={'c': imKey, 'date': d, 'cpu_temp': cpu_temp, 'temp': temp, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure, 'outer_humid': outer_humid,  'v0':v0, 'v1':v1, 'soil1':soil1, 'soil2':soil2, 'soil_temp':soil_temp, 'deploy' : DEPLOY_SWITCH, 'memo' : localFile_name}

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
def capture_send():
    logger.info('Waiting for shooting time')
    while True:
        now = datetime.datetime.now()
        if now.minute % everyMinutes == 0: #指定毎分時になると撮影
#        if now.minute % everyMinutes <= 7: #指定毎分時、過ぎた場合は7分以内なら、待ちきれないので正常撮影
            logger.info('指定時間になりました:' + str(now.minute) + "分ごと撮影")
            captureFile_name = now.strftime('%Y%m%d%H%M') + '.jpg'
            break
        elif everyMinutes - (now.minute % everyMinutes) > 7:#7分より多く待つなら取りあえず撮影して終わる
            logger.info('指定時間まで7分以上ありますので、テスト撮影して指定時刻5分前に再起動します')
            captureFile_name = 'PowerOnTest_' + now.strftime('%Y%m%d%H%M') + '.jpg'
            break
    logger.info('写真の保存ファイル名；' + captureFile_name)
    picamera.start_preview() #あれ？　これ入れてなかったよ。これがないと露出調整がうまくいかないんじゃ？　2017/06/14
    time.sleep(2) #これも入れ忘れてた　2017/06/14　12:59
    picamera.brightness = pictureBrightness #標準の50よりほんの少し明るめに
    picamera.contrast = pictureContrast 
    #標準の50よりほんの少しコントラストを強めに
    logger.info("brightness:"+str(picamera.brightness)+" ,contrast:"+str(picamera.contrast))
    # picamera.annotate_background = picamera.Color('black')
#    picamera.annotate_text = now.strftime('%Y-%m-%d %H:%M:%S') + " , Contrast : " + str(picamera.contrast)
    picamera.rotation = 180
    picamera.capture(captureFile_name)
    
    try:
        send_ftps(captureFile_name, put_directory)
        logger.info("File is sended with no error. Delete " + captureFile_name + " on Ras Pi")
        os.remove(captureFile_name)
        return captureFile_name

    except:
        logger.info("Failed file transfer in send_ftps。そのまま何もしない")


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

#指定時間を待って写真を撮影する
try:
    # today()メソッドで現在日付・時刻のdatetime型データの変数を取得
    picamera = picamera.PiCamera()
    picamera.resolution = (1920, 1080) #HD Quality Size=1.5MB、研究材料としては最低限これくらいはほしい。稲穂の様子はこ$
    #picamera.resolution = (1024, 768) # こちらは554KBで済む
    # Camera warm-up time、Whiteバランスをとるための猶予時間。これがないと色が青白くて使い物にならない
    time.sleep(2)

    now = datetime.datetime.now()
    hour = now.hour

    if hour >= hourToBegin -1 and hour < hourToStop: #動作は止める時刻になる前まで
        localFile_name = capture_send() #写真撮影し、結果をサーバーに送信、送信ファイル名を受け取る

    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    if hour < hourToBegin -1:
        x = 60 * hourToBegin - (hour * 60 + minute)
    elif hour >= hourToStop: #停止設定時刻になったら深夜24時までストップさせる
                            #ここはちょっとおかしい。もし、開始時刻として深夜〇時以前が指定されていると、狂う
                            #運用時に注意： hourToBegin を深夜0時以降にセットすること
        x = 1440 - (hour*60 + minute)
    else:
        x = everyMinutes -5 -(minute % everyMinutes)    #毎撮影時刻の5分前までに何分あるかを算出、単にminを引くのではなく、（現在時刻／everuminute）の余りを求めて引く必要がある
        if x <0:
            x = 0 #電源モジュールは負の値は指定できない（のではないかな？）
            # x = 5   #テストのために5分のスリープを指定
    x = x / 5
    timeToOff = 40
    powerControlCommand = 'sudo /usr/sbin/i2cset -y 1 0x40 ' + str(timeToOff) + ' ' + str(x) + ' i'
    #40秒後に電源オフ、最後のパラメーター×5分後に起動

    logger.info('電源モジュールに送信するコマンド用意：' + powerControlCommand + ':40秒後にシャットダウン、最後のパラメーター×5分後に起動')
    # timeToWait = datetime.timedelta(minutes=x*5)
    # wakeupTime = now + timeToWait #起動時刻算出
    # logger.info(timeToWait + "分後の" +wakeupTime + "に起動します")

except Exception as e:
    logger.debug("Fail in camera caputer :" + str(e))

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

file_name = "field_location.log"
sendLog_ftps(file_name, put_directory)

#Programスイッチが入っているときはパワースイッチコントロールを送らずに終了
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_NO, GPIO.IN)

if GPIO.input(GPIO_NO) == 0:
    logger.info("Program switch is OFF")
    try:
        sendPowerCommand()
        logger.info('PowerControl設定正常終了。'+ str(powerControlCommand))
        time.sleep(5)

    except IOError:
        logger.info('IOError。デバイスが認識できません')
    	logger.exception('Error in read bme280: %s', err)
    finally:
        logger.info('PowerControl設定の処理を終わりました。電源を落とします。エラーログも確認してください')
        print('システムを終了します')
        os.system('sudo poweroff')
        GPIO.cleanup()

else:
    logger.info("Programmer switch is ON. Continue to proceed\n")
