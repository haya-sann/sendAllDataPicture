#coding: utf-8
#このデバイス（田んぼカメラ）を外に設置する際は、サーバー上のwebAPIを正確に指すように調整するのを忘れないように
#設置する機器の対応サーバーに応じて指定するconfig.confの中身を対応するサーバー情報に書き換えるのを忘れずに
#ex: configfile.read("/home/pi/Documents/field_location/config.conf")
#rc.localを修正したければ、この中でアップデートを行う。rcLocalUpdate.shという中間ファイルを経由して、これを/etc/rc.localに上書きする仕組み
#したがって、rc.localを書き直したければ、rcLocalUpdate.shを更新してやれば良い。

#todo:マシンのIPアドレスを見て、データの送り先を本番か、サンドボックスかに切替える#これはrc.localで面倒を見るので不要
#このプログラムはpython3系向け。2to3で書き換えた
#$ 2to3-3.6 -w ~/sendBMEDataToIM_periodically.py --write ~/sendBMEDataToIM_periodically.py

'''稼働時間設定'''
hourToBegin = 7 #カメラを動作開始させる時刻
hourToStop = 23 #カメラを完全休止させる時刻
everyMinutes = 60 #何分おきに撮影するのかをセット。5~60の値をセット

# from _typeshed import NoneType
import sys, os, getpass
import pprint

currentDirectory = os.path.dirname(os.path.abspath(__file__))
#homeDirectory = os.environ['HOME']
homeDirectory = '/home/pi'

print ("Effective user is [%s]" % (getpass.getuser()))

print(sys.version)

if __name__ == '__main__':
    # root権限に昇格
    if os.geteuid():
        args = [sys.executable] + sys.argv
        os.execlp('sudo', 'sudo', *args)

from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)
logger.propagate = True

logger.info('home directory:'+ homeDirectory)
#check for network connection
import subprocess
processToCall = currentDirectory + '/test_waitForPing.sh'
if subprocess.call (['bash', processToCall]) == 0:
        logger.info("Server can be reached")
else:   
        logger.info ('Error. Network might down. Reboot right away')
        subprocess.call(['sudo','reboot'])

import http.client
import urllib.parse, urllib.request, urllib.error
import time
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)
import configparser
import codecs
import ambient #ambientにデータを送込むライブラリ
#詳しい説明は https://ambidata.io/refs/python/
import requests
import RPi.GPIO as GPIO
PYTHONIOENCODING = 'utf_8'
GPIO_NO = 23 #PIN-16にプログラマースイッチを装着している。GPIO23に相当する

from bme280 import bmeRead
from retry import retry
from readBH1750 import measureLight
from read4chAnalog import read4ch
from sr04_Bluetin import sr04_read

from sendMail import send, create_message

from w1_DS18B20 import read_soil_temp
from ftps import sendLog_ftps
from ftps import send_ftps
import picamera
#カメラ撮影準備
localFile_name = None
# pictureResolution_h = 640
# pictureResolution_v = 480
# pictureResolution_h = 1920
# pictureResolution_v = 1080
pictureResolution_h = 1280
pictureResolution_v = 720
pictureBrightness =55
pictureContrast = 10
# pictureBrightness =55
# pictureContrast = 10
pictureSharpness = 20
pictureBanner = "Test Shooting. (1280)"

v0=v1=soil1=soil2=soil_temp=0.0
temperature = 28.55 #川越の8月の平均温度。取得できないときはこれを使う
pressure = None
humid = None
outer_temp =  28.55 #川越の8月の平均温度。取得できないときはこれを使う
outer_humid = None
outer_pressure = None

class Color:
    BLACK     = '\033[30m'
    RED       = '\033[31m'
    GREEN     = '\033[32m'
    YELLOW    = '\033[33m'
    BLUE      = '\033[34m'
    PURPLE    = '\033[35m'
    CYAN      = '\033[36m'
    WHITE     = '\033[37m'
    END       = '\033[0m'
    BOLD      = '\038[1m'
    UNDERLINE = '\033[4m'
    INVISIBLE = '\033[08m'
    REVERCE   = '\033[07m'

specialMailSubject = ''
alertMailMessage = ''

try:
    DEPLOY_SWITCH = os.environ['DEPLOY']
except: #rc.localからexportされて送られるはずのDEPLOYがない場合は
    DEPLOY_SWITCH = "sandBox"
logger.info('DEPLOY_SWITCH :' + DEPLOY_SWITCH)

global_ipAddress =  subprocess.getoutput('hostname -I')
dir_path = os.path.abspath(os.path.dirname(__file__))#自分自身の居所情報

configfile = configparser.ConfigParser() #sftpサーバーへの接続準備、Python3では名前変更された
#configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った
configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った

host_IM = configfile.get("settings", "host")
archive_server = configfile.get("settings", "ftpsHost")  #ftpsサーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id
key = configfile.get("settings", "key")#ThingSpeak Channel write key, not in service
ambiChannel = configfile.get("settings", "ambiChannel")
ambiKey = configfile.get("settings", "ambiKey")
ambiBoard = configfile.get("settings", "ambiBoard")
ambiChannelSandbox = configfile.get("settings", "ambiChannelSandbox") #サンドボックスチャネル
ambiKeySandbox = configfile.get("settings", "ambiKeySandbox")  #サンドボックスチャネル
ambiBoardSandbox = configfile.get("settings", "ambiBoardSandbox")
imKey = configfile.get("settings", "imKey")
from_addr = configfile.get("settings", "mailAddress")
mailPass = configfile.get("settings", "mailPass")

if DEPLOY_SWITCH == "distribution":
    put_directory = 'daily_timelapse' #Both Local and Remote Server has same directory
elif DEPLOY_SWITCH == "sandBox":
    put_directory = 'daily_timelapseSandbox' #Both Local and Remote Server has same directory
    ambiKey = ambiKeySandbox
    ambiChannel = ambiChannelSandbox


#前回起きたエラーをメール送信

#前回ログのメール送信
to_addr = "haya.biz@gmail.com"
#件名と本文
subject = "田んぼカメラ：前回ログ" + specialMailSubject + DEPLOY_SWITCH
body = alertMailMessage + "\n\n" + """前回ログデータ
ログはconsoleアプリで読んでください。
""" + "\n"

#添付ファイル設定(text.txtファイルを添付)
mime={'type':'text', 'subtype':'comma-separated-values'}
#    attach_file={'name':'boot.log', 'path':'/var/log/wifi.log'}
#ここでエンコーディングをutf8にするといいはず。
attach_file={'name':'previous_boot.log','path': homeDirectory+'/log/previous_boot.log'}
 
msg = create_message(from_addr, to_addr, subject, body, mime, attach_file)
try:
    send(from_addr, to_addr, msg)
    logger.info("Successfully sended previous log mail to " + to_addr)
except Exception as e:
        logger.debug("send mail error. :" + str(e))



#send previous log 

#エラーが起きた場合に保存しておき、次回接続時に送信
file_name = "previous_boot.log"

src = homeDirectory +'/log/' + file_name
if os.path.isfile(src):
    try:
        _timeStamp = sendLog_ftps(src, put_directory)
        logger.info(_timeStamp)

        #log送信正常終了なので、中身をクリアする
        with codecs.open(src, 'w', 'utf_8_sig') as f:
    #            f.write(unicode(codecs.BOM_UTF8, 'utf_8'))
            f.write ('アップロード終了 with no error. Log cleared at: ' + _timeStamp.strftime('%Y%m%d%H%M') + '\n')
        f.close()
    except Exception as e:
            logger.debug("sendLog_ftps error. :" + str(e))

logger.info("公開先は：" + DEPLOY_SWITCH)
logger.info("資料の保存先は：" + put_directory)

#update rc.local when needed. 2021/06/17
updateSwitch = os.getenv('rcLocalUpdate_switch')
if updateSwitch != "doNothing":
    try:
        subprocess.call(['sudo', 'cp', '-vu', '/home/pi/Documents/field_location/sendAllDataPicture/rcLocalUpdate.sh', '/etc/rc.local'])
        logger.info("Successfully copied updated rc.local file")
    except :
        logger.debug("failed update rc.local file. Please check location of rcLocalUpdate.py")
else:
    logger.info("Already updated. Keep present rc.local")

#アップデート／アップグレードに関する自動処理を止める
# sudo systemctl disable apt-daily-upgrade.timerは一度やれば良いので、ここは不要
# try:
#     subprocess.call("sudo systemctl disable apt-daily-upgrade.timer; sudo systemctl disable apt-daily.timer")
#     logger.info("Successfully removed service")
# except :
#     logger.debug("failed removed service")

def captureSensorData(i2c_address):
    #センサーからデータ収集するプログラムを実装
    #I2C、SPIなどを使ってデータキャプチャ
    temperature = 28.55 #川越の8月の平均温度。取得できないときはこれを使う
    pressure = None
    humid = None

    try:
        temperature, pressure, humid = bmeRead(i2c_address)
    except IOError as e:
        logger.info("デバイスが見つかりません　：" + str(e))
        #sys.exit(False)

    return temperature, pressure, humid

@retry(tries=3, delay=5, backoff=2)
def sendDataToAmbient():
    #timeout = 5.0 #指定市しない場合は30秒でエラーを返す。
    # 受取れるデータ数は８個までなので、土壌温度、土壌湿度は扱わない。
    logger.info(Color.RED + 'Trying to send data to Ambient' + Color.END)
    ambi = ambient.Ambient(ambiChannel, ambiKey) # チャネルID、ライトキー
    try:
        r = ambi.send({"d1": cpu_temp, "d2": temperature, "d3": pressure, "d4": humid, "d5": lightLevel, "d6": v0, "d7": v1, "d8": averageDepth})
#        r = ambi.send({"d1": cpu_temp, "d2": temperature, "d3": pressure, "d4": humid, "d5": lightLevel, "d6": v0, "d7": v1}, timeout = timeout)
        if r.status_code == 200:
            logger.info(Color.GREEN + 'successfuly sended data to Ambient' + Color.END)
        else:
            logger.info('Connection to AbmiData failed')
    except requests.exceptions.RequestException as e:
        global specialMailSubject, alertMailMessage
        specialMailSubject = 'AmbiData TimeoutError:'
        logger.info('Error encounterd : '+ str(e))
        alertMailMessage = "Error occured while sending AmbiData: " + str(e)
#        raise
        pass

def sendDataToIM():
    keyValue={'c': imKey, 'date': d, 'cpu_temp': cpu_temp, 'temp': temperature, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'outer_temp': outer_temp, 'outer_pressure': outer_pressure, 'outer_humid': outer_humid,  'v0':v0, 'v1':v1, 'depth':averageDepth, 'soil1':soil1, 'soil2':soil2, 'soil_temp':soil_temp, 'deploy' : DEPLOY_SWITCH, 'memo' : localFile_name}

    valueToSend={}
    for value_label, value in list(keyValue.items()):
        if value is not None:
            valueToSend[value_label]=value

    params_IM = urllib.parse.urlencode(valueToSend)#最終的に送信データを用意（今回アクセスのログ含む）

    logger.info ("paramsIM:" + params_IM)

    conn = http.client.HTTPSConnection(host_IM)
    #conn = httplib.HTTPConnection(host_IM)
    conn.request("GET", "/IM/im_build/webAPI/putDataAPI_withAuth.php?" + params_IM)
    response = conn.getresponse()
    logger.info("Server respond:" + str(response.status) + str(response.reason))
    data = response.read()
    conn.close()

def takePicture():
    logger.info('Waiting for shooting time')
    while True:
        now = datetime.datetime.now()
        if now.minute % everyMinutes == 0: #指定毎分時になると撮影
#        if now.minute % everyMinutes <= 7: #指定毎分時、過ぎた場合は7分以内なら、待ちきれないので正常撮影
            logger.info('指定時間になりました:' + str(everyMinutes) + "分ごと撮影")
            captureFile_name = now.strftime('%Y%m%d%H%M') + '.jpg'
            break
        elif everyMinutes - (now.minute % everyMinutes) > 7:#7分より多く待つなら取りあえず撮影して終わる
            logger.info('指定時間まで7分以上ありますので、テスト撮影して指定時刻5分前に再起動します')
            captureFile_name = 'PowerOnTest_' + now.strftime('%Y%m%d%H%M') + '.jpg'
            break
    logger.info('写真の保存ファイル名；' + captureFile_name)
    logger.info("2018/06/06　14:01 写真が眠いのでpicamera.start_previewを再度入れてみた。これはいるのか、いらないのか、検証終わったらfix")
    picamera.start_preview() #あれ？　これ入れてなかったよ。これがないと露出調整がうまくいかないんじゃ？　2017/06/14
    time.sleep(2) #これも入れ忘れてた　2017/06/14　12:59
    picamera.stop_preview() #これを入れないといつまでも画面に写真が表示されたままになる
    #標準の50よりほんの少しコントラストを強めに
    logger.info("brightness:"+str(picamera.brightness)+" ,contrast:"+str(picamera.contrast) + " , Sharpness : " + str(picamera.sharpness))
    picamera.annotate_background = True
    # picamera.annotate_background = picamera.Color('black')
    # picamera.annotate_foreground = picamera.Color('yellow')
    picamera.annotate_text = now.strftime('%Y-%m-%d %H:%M:%S') + "/" + pictureBanner #+ " , Brightness : " + str(picamera.brightness) + " , Contrast : " + str(picamera.contrast) + " , Sharpness : " + str(picamera.sharpness) + " / With preview."
    picamera.rotation = 180
    picamera.capture(captureFile_name)
    return captureFile_name

@retry(exceptions=Exception, tries=3, delay=2)
def sendPowerCommand():
    os.system(powerControlCommand) #import osが必要
        #成功するまで繰り返す、回数指定も可能
	#retryのInstallationは
	#$ pip install retry
	#from retry import retry
    logger.info("sended PowerCommand" + str(powerControlCommand))

now = datetime.datetime.now()
hour = now.hour
if hour >= hourToBegin -1 and hour < hourToStop: #動作は止める時刻になる前まで
    logger.info("Will [takePicture] at every " + str(everyMinutes) + " minutes." )
    try:
        # today()メソッドで現在日付・時刻のdatetime型データの変数を取得
        picamera = picamera.PiCamera()
        picamera.resolution = (pictureResolution_h, pictureResolution_v) #HD Quality Size=1.5MB、研究材料としては最低限これくらいはほしい。稲穂の様子はこ$
        #picamera.resolution = (1024, 768) # こちらは554KBで済む
        picamera.brightness = pictureBrightness #標準の50よりほんの少し明るめに
        picamera.contrast = pictureContrast 
        picamera.sharpness = pictureSharpness

        time.sleep(2)
    # Camera warm-up time、Whiteバランスをとるための猶予時間。これがないと色が青白くて使い物にならない
        
        localFile_name = takePicture() #写真撮影し、ファイル名を受け取る

    except Exception as e:
        logger.debug("Fail in camera capture :" + str(e))

else:
    logger.info("Out of service time: No picture was taken")

logger.info('Waiting for periodic time')
while True:
    now = datetime.datetime.now()
    if now.minute % everyMinutes == 0: #指定毎分時になると実行
        logger.info('指定時間になりました:' + str(everyMinutes) + "分ごとに測定中")
        break
    elif everyMinutes - (now.minute % everyMinutes) > 7:#7分より多く待つなら取りあえず測定＆送信して終わる
        logger.info('指定時間まで7分以上ありますので、測定して指定時刻5分前に再起動します')
        break


# today()メソッドで現在日付・時刻のdatetime型データの変数を取得
d = datetime.datetime.today()

print(('データ取得時刻 == %s : %s\n' % (d, type(d)))) # Microsecond(10^-6sec)まで取得

#Calculate CPU temperature of Raspberry Pi in Degrees C
cpu_temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU temp

i2c_address = 0x76
temperature, pressure, humid = captureSensorData(i2c_address)
# 外付けの気候センサー
i2c_address = 0x77
outer_temp, outer_pressure, outer_humid = captureSensorData(i2c_address)
print("outer_temp:", outer_temp, "type of val:", type(outer_temp))

try:
    lightLevel = None #init light level
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

try:
    soil_temp = read_soil_temp()
except Exception as error_soilTemperature:
    logger.debug("Error occured in measure soil temperature" + str(error_soilTemperature))

averageDepth = sr04_read(temperature) # call depth measurment

#Send atmosphere data to AmbiData
try:
    sendDataToAmbient()
except Exception as error_SendToAmbi:
    logger.info("Error occured while sending AmbiData" + str(error_SendToAmbi))

#send data to host_IM
try:
    sendDataToIM()
except Exception as error_SendIM:
    logger.info("Error occured while sending data to IM" + str(error_SendIM))

#もろもろのデータ送信が終わったので撮影しておいた写真を送信する
try:
    if localFile_name is not None:
        send_ftps(localFile_name, put_directory)
        logger.info("File is sended with no error. Delete " + localFile_name + " on Ras Pi")
        os.remove(localFile_name)
        logger.info("File removed: " + localFile_name + " on Ras Pi")
        try:
            #サーバー内で圧縮プログラムを動かす
            if (DEPLOY_SWITCH == "sandBox"):
                '''サーバーに送った写真の解像度を下げたファイルを作る。サムネール、スライドショーの表示などのために'''
                curlCommand = 'curl https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/loadThumbPhotos_'+ DEPLOY_SWITCH+ '.php'
                os.system(curlCommand)
                logger.info('Successfully kicked loadThumbPhotos_' + DEPLOY_SWITCH + '.php')
            else:
                os.system('curl https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/loadThumbPhotos.php')
#                os.system(['curl', 'https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/loadThumbPhotos.php'])
                logger.info("Successfully kicked loadThumbPhotos.php")
        except Exception as KickingPhotoEncode:
                logger.debug("Failed Kicking loadThumbPhotos" + str(KickingPhotoEncode))
except Exception as e:
    logger.debug("Failed file transfer in send_ftps。" + str(e))


now = datetime.datetime.now()
x = everyMinutes -4 -(now.minute % everyMinutes)    #毎撮影時刻の4分前までに何分あるかを算出、単にminを引くのではなく、（現在時刻／everuminute）の余りを求めて引く

if x < 0:
    x = 0 #電源モジュールは負の値は指定できない（のではないかな？）

x = int(x / 5)
timeToOff = 20 #電源オフまでの秒数を指定、15秒にしていたが短いので20にした。
powerControlCommand = 'sudo /usr/sbin/i2cset -y 1 0x40 ' + str(timeToOff) + ' ' + str(x) + ' i'
#40秒後に電源オフ、最後のパラメーター×5分後に起動

logger.info('電源モジュールに送信するコマンド用意：' + powerControlCommand + '（' + str(timeToOff) + '秒後にシャットダウン、' + str(x*5) + '分後に起動）')
# timeToWait = datetime.timedelta(minutes=x*5)
# wakeupTime = now + timeToWait #起動時刻算出
# logger.info(timeToWait + "分後の" +wakeupTime + "に起動します")

#ログをまとめてサーバーにftps送信する
#ログを正常に送れれば、ログファイルはクリアされる
#もろもろ書かれたlogは結局boot.logに上書きされているので、
#検討するのはboot.logのみでよい


file_name = "field_location.log"

src = '/var/log/' + file_name
if os.path.isfile(src):
    try:
        _timeStamp = sendLog_ftps(src, put_directory)

        #log送信正常終了なので、中身をクリアする
        with codecs.open('/var/log/' + file_name, 'w', 'utf_8_sig') as f:
    #            f.write(unicode(codecs.BOM_UTF8, 'utf_8'))
            f.write ('アップロード終了 with no error. Log cleared at: ' + _timeStamp.strftime('%Y%m%d%H%M') + '\n')
        f.close()
    except Exception as e: 
        logger.debug("sendLog_ftps error. :" + str(e))

#エラーが起きた場合には「前回ログ」として保存

file_name = "previous_field_location.log"

src = '/var/log/' + file_name
if os.path.isfile(src):
    try:
        _timeStamp = sendLog_ftps(src, put_directory)

        #log送信正常終了なので、中身をクリアする
        with codecs.open('/var/log/' + file_name, 'w', 'utf_8_sig') as f:
    #            f.write(unicode(codecs.BOM_UTF8, 'utf_8'))
            f.write ('アップロード終了 with no error. Log cleared at: ' + _timeStamp.strftime('%Y%m%d%H%M') + '\n')
        f.close()
    except Exception as e:
            logger.debug("sendLog_ftps error. :" + str(e))


file_name = "/var/log/boot.log"
try:
    _timeStamp = sendLog_ftps(file_name, put_directory)
    logger.info(_timeStamp)

except Exception as e:
    logger.debug("send boot.log ftps error . :" + str(e))

#ログのメール送信
to_addr = "haya.biz@gmail.com"
#件名と本文
subject = "田んぼカメラから：" + specialMailSubject + DEPLOY_SWITCH
body = alertMailMessage + "\n\n" + """ログデータを送ります。これは詳細なログです。
ログはconsoleアプリで読んでください。

スライドショーはこちら：
https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/dailySlideShow_v7.php

データのグラフは
https://ambidata.io/bd/board.html?id=""" + ambiBoardSandbox + """ (サンドボックス)
https://ambidata.io/bd/board.html?id=""" + ambiBoard + """ (本番ボード)

生データは
https://ciao-kawagoesatoyama.ssl-lolipop.jp/IM/sandBox_2.html （サンドボックス）
https://ciao-kawagoesatoyama.ssl-lolipop.jp/IM/index.html (本番データ)

まとめのホームページは
https://ciao-kawagoesatoyama.ssl-lolipop.jp/seasonShots/index.php

""" + "\n"

#添付ファイル設定(text.txtファイルを添付)
mime={'type':'text', 'subtype':'comma-separated-values'}
#    attach_file={'name':'boot.log', 'path':'/var/log/wifi.log'}
#ここでエンコーディングをutf8にするといいはず。
#attach_file={'name':'field_location.log','path':'/var/log/field_location.log'}
attach_file={'name':'boot.log','path':'/var/log/boot.log'}
 
msg = create_message(from_addr, to_addr, subject, body, mime, attach_file)
try:
    send(from_addr, to_addr, msg)
    logger.info("Successfully sended mail to " + to_addr)
except Exception as e:
        logger.debug("send mail error. :" + str(e))

#field_location.logをprevious_field_location.logとして複製を作る
import shutil
try:
    src = '/var/log/boot.log'
    copy = homeDirectory +'/log/previous_boot.log'
    shutil.copyfile(src,copy)
    logger.info("Successfully copied previous boot log")

except Exception as error:
    logger.info("Can't copy boot.log file " + str(error))

#Programスイッチが入っているときはパワースイッチコントロールを送らずに終了
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_NO, GPIO.IN)

if GPIO.input(GPIO_NO) == 0:
    logger.info("Program switch is OFF")
    try:
        sendPowerCommand()
        logger.info('PowerControl command is ready: '+ str(powerControlCommand))
        time.sleep(5)

    except IOError:
        logger.info("IOError. I2C device can't be found")
    finally:
        logger.info('PowerControl will be enabled. Power will be off. Please check logs')
        print('SYSTEM is going down')
        subprocess.call(['sudo', 'rm', '-rf', '/var/log/*']) #volume unmountに備えて/var/logの中をクリア
        subprocess.call(['sudo', 'poweroff'])
        GPIO.cleanup()

else:
    logger.info("Programmer switch is ON. Continue to proceed\n")
