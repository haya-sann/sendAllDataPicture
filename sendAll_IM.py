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
from  subprocess import Popen, PIPE, call

import picamera
from ftplib import FTP_TLS
import logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter('[%(name)s] %(asctime)s %(levelname)s : %(message)s')
streamHandler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)


import ConfigParser
import socket
import commands

localFile_name = ""
pictureContrast = 20

try:
    DEPLOY_SWITCH = os.environ['DEPLOY']
except: #rc.localからexportされて送られるはずのDEPLYがない場合は
    DEPLOY_SWITCH = "sandBox"

hourToBegin = 5 #カメラを動作開始させる時刻
hourToStop = 23 #カメラを完全休止させる時刻
everyMinutes = 60 #何分おきに撮影するのかをセット

configfile = ConfigParser.SafeConfigParser() #sftpサーバーへの接続準備
configfile.read("/home/pi/Documents/mochimugi/config.conf")#Localに置いたconfig.confファイルへの絶対パスを使った

archive_server = configfile.get("settings", "host")  #サーバーのドメイン名
pw = configfile.get("settings", "password")      #ログインパスワード
userID = configfile.get("settings", "id")        #サーバーログインUser id
key = configfile.get("settings", "key")#ThingSpeak Channel write key
ambiKey = configfile.get("settings", "ambiKey")
imKey = configfile.get("settings", "imKey")

if DEPLOY_SWITCH == "distribution":
    put_directory = 'daily_timelapse' #Both Local and Remote Server has same directory
elif DEPLOY_SWITCH == "sandBox":
    put_directory = 'daily_timelapseSandbox' #Both Local and Remote Server has same directory


dir_path = '/home/pi/Documents/mochimugi/'+ put_directory

global_ipAddress = commands.getoutput('hostname -I')

streamHandler.setFormatter(formatter)
streamHandler.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler(dir_path + '/'+ 'mochimugi.log', mode='a', encoding=None, delay=0)
fileHandler.setFormatter(formatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(streamHandler)
logger.addHandler(fileHandler)
logger.info('logging.warning:Global IP Address:%s', global_ipAddress)
logger.info("dir_path is set to : " + dir_path + "(just for debugging)")
logger.info("これは新しいsendAll_IM.py. ver.1.4: 2017/06/18　03時14分修正")
logger.info("設定動作開始時刻："+str(hourToBegin)+"時、　終了時刻："+str(hourToStop)+ "時")

try:
    import rcLocalUpdate
    rcLocalUpdate.updateRCLocal()
    logger.info("Successfully updated rc.local file")
except :
    logger.debug("failed update rc.local file")

# logging.basicConfig(filename=dir_path + '/'+ 'mochimugi.log', level=logging.NOTSET, format='%(asctime)s %(message)s')
# logging.warning('logging.warning:Global IP Address:%s', global_ipAddress)

def sendLog_ftps(file_name):
    try:
        logger.info("Sending log with ftps to server : "+ archive_server)
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログを全部出力してみよう
    #    _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにするには、
        #ユーザが prot_p() メソッドを呼び出してそれを明示的に要求しなければなりません。

        _file = open(dir_path + '/' + file_name, 'rb') #'r' means read as text mode
        #'rb' means binarymode
        logger.info("File opened : " + dir_path + '/' + file_name)
        _timeStamp = datetime.datetime.now()
        logfile_name = 'mochimugi' + _timeStamp.strftime('%Y%m%d%H%M') + '.log'
        logger.info('Logging file on the server is : ' + logfile_name)

        _ftps.cwd('/home/mochimugi/www/seasonShots/' + put_directory) #アップロード先ディレクトリに移動
        logger.info('Success : Change directory to: /home/mochimugi/www/seasonShots/' + put_directory)

        _ftps.storbinary('STOR ' + logfile_name, _file)

        # process = Popen(ftps_storeCommand, shell=True, stdout=PIPE, stderr=PIPE)
        # output, err = process.communicate()

        # for line in _file:
        #     print line
        
        _file.close()
        _ftps.quit()
        logger.info("Upload finished and closed Log file, with no error. Clear log file.")
        #log送信正常終了なので、中身をクリアする
        with open(dir_path + '/' + file_name, "w") as f:
            f.write("Log cleared at: " + _timeStamp.strftime('%Y%m%d%H%M') + "\n")
            f.close()
    except Exception as e:
        logger.debug("sendLog_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        raise

def send_ftps(file_name): #ここにエラー処理を入れること
    try:
        logger.info("ftps accessing"+ archive_server)
        _ftps = FTP_TLS(archive_server)
        _ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
        _ftps.login(userID, pw)
        _ftps.prot_p() #データ接続をセキュアにする

        _file = open(dir_path + '/' + file_name, 'rb') #'rb'means read as binary mode.
        # アップロードが成功したらファイルは削除。2017/06/23

        _ftps.cwd('/home/mochimugi/www/seasonShots/' + put_directory) #アップロード先ディレクトリに移動
        logger.info('change directory to: /home/mochimugi/www/seasonShots/' + put_directory)
        _ftps.storbinary('STOR ' + file_name, _file)
        _file.close()
        _ftps.quit()
        logger.info("Upload finished with no error")

    except Exception as e:
        logger.debug("send(picture)_ftps error. :" + str(e))
        _file.close()
        _ftps.quit()
        raise

def capture_send():
    logger.info('Waiting for shooting time')
    while True:
        now = datetime.datetime.now()
        if now.minute % everyMinutes == 0: #指定毎分時になると撮影
            logger.info('指定時間になりました')
            captureFile_name = now.strftime('%Y%m%d%H%M') + '.jpg'
            break
        elif everyMinutes - (now.minute % everyMinutes) > 7:#、5分以上待つなら取りあえず撮影して終わる
            logger.info('指定時間まで7分以上ありますので、テスト撮影して指定時刻5分前に再起動します')
            captureFile_name = '電源投入時テスト_' + now.strftime('%Y%m%d%H%M') + '.jpg'
            break
    logger.info('写真の保存ファイル名；' + captureFile_name)
    picamera.start_preview() #あれ？　これ入れてなかったよ。これがないと露出調整がうまくいかないんじゃ？　2017/06/14
    time.sleep(2) #これも入れ忘れてた　2017/06/14　12:59
#    picamera.brightness = 55 #標準の50よりほんの少し明るめに
    picamera.contrast = pictureContrast 
#標準の50よりほんの少しコントラストを強めに
    logger.info("brightness:"+str(picamera.brightness)+" ,contrast:"+str(picamera.contrast))
    # picamera.annotate_background = picamera.Color('black')
    picamera.annotate_text = now.strftime('%Y-%m-%d %H:%M:%S') + " , Contrast : " + str(picamera.contrast)
    picamera.rotation = 180
    picamera.capture(dir_path+'/'+captureFile_name)
    
    try:
        send_ftps(captureFile_name)
        logger.info("File is sended with no error. Delete " + dir_path+'/'+ captureFile_name + " on Ras Pi")
        os.remove(dir_path+'/'+captureFile_name)
        return captureFile_name

    except:
        logger.info("Failed file transfer in send_ftps。そのまま何もしない")

spi = spidev.SpiDev()
spi.open(0, 0)
# Settings (for example)
#spi.max_speed_hz = 10000


sleep = 180 # how many seconds to sleep between posts to the channel

PORT1 = 23
PORT2 = 24

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PORT1, GPIO.IN)
GPIO.setup(PORT2, GPIO.OUT)

bus_number = 1
i2c_address = 0x76

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


digT = []
digP = []
digH = []

t_fine = 0.0


def writeReg(reg_address, data):
    bus.write_byte_data(i2c_address, reg_address, data)

def get_calib_param():
    calib = []

    for i in range(0x88, 0x88+24):
        calib.append(bus.read_byte_data(i2c_address, i))
    calib.append(bus.read_byte_data(i2c_address, 0xA1))
    for i in range(0xE1, 0xE1+7):
        calib.append(bus.read_byte_data(i2c_address, i))

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
    digH.append(calib[24])
    digH.append((calib[26]<< 8) | calib[25])
    digH.append(calib[27])
    digH.append((calib[28]<< 4) | (0x0F & calib[29]))
    digH.append((calib[30]<< 4) | ((calib[29] >> 4) & 0x0F))
    digH.append(calib[31])

    for i in range(1, 2):
        if digT[i] & 0x8000:
            digT[i] = (-digT[i] ^ 0xFFFF) + 1

    for i in range(1, 8):
        if digP[i] & 0x8000:
            digP[i] = (-digP[i] ^ 0xFFFF) + 1

    for i in range(0, 6):
        if digH[i] & 0x8000:
            digH[i] = (-digH[i] ^ 0xFFFF) + 1

def measureLight():
    #bus = smbus.SMBus(0) # Rev 1 Pi uses 0
    bus = smbus.SMBus(1)  # Rev 2 Pi uses 1
    sensor = BH1750(bus)
    logger.info("Light Sensitivity: {:d}".format(sensor.mtreg))
    lightLevel = sensor.measure_high_res2()
    time.sleep(1)
    return lightLevel


def readData():
    data = []
    for i in range(0xF7, 0xF7+8):
        data.append(bus.read_byte_data(i2c_address, i))
    pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
    temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
    hum_raw = (data[6] << 8)  |  data[7]

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

    return pressure/100

def compensate_T(adc_T):
    global t_fine
    v1 = (adc_T / 16384.0 - digT[0] / 1024.0) * digT[1]
    v2 = (adc_T / 131072.0 - digT[0] / 8192.0) * (adc_T / 131072.0 - digT[0] / 8192.0) * digT[2]
    t_fine = v1 + v2
    temperature = t_fine / 5120.0
    return temperature

def compensate_H(adc_H):
    global t_fine
    var_h = t_fine - 76800.0
    if var_h != 0:
        var_h = (adc_H - (digH[3] * 64.0 + digH[4]/16384.0 * var_h)) *(digH[1] / 65536.0 * (1.0 + digH[5] / 67108864.0 * var_h * (1.0 + digH[2] / 67108864.0 * var_h)))
    else:
        return 0
    var_h = var_h * (1.0 - digH[0] * var_h / 524288.0)
    if var_h > 100.0:
        var_h = 100.0
    elif var_h < 0.0:
        var_h = 0.0
    return var_h

def setup():
    osrs_t = 1            #Temperature oversampling x 1
    osrs_p = 1            #Pressure oversampling x 1
    osrs_h = 1            #Humidity oversampling x 1
    mode = 3            #Normal mode
    t_sb = 5            #Tstandby 1000ms
    filter = 0            #Filter off
    spi3w_en = 0            #3-wire SPI Disable

    ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
    config_reg = (t_sb << 5) | (filter << 2) | spi3w_en
    ctrl_hum_reg = osrs_h

    writeReg(0xF2, ctrl_hum_reg)
    writeReg(0xF4, ctrl_meas_reg)
    writeReg(0xF5, config_reg)


setup()
get_calib_param()


if __name__ == '__main__':
    try:
        # today()メソッドで現在日付・時刻のdatetime型データの変数を取得
        picamera = picamera.PiCamera()
        picamera.resolution = (1920, 1080) #HD Quality Size=1.5MB、研究材料としては最低限これくらいはほしい。稲穂の様子はこ$
        #picamera.resolution = (1024, 768) # こちらは554KBで済む
        # Camera warm-up time、Whiteバランスをとるための猶予時間。これがないと色が青白くて使い物にならない
        time.sleep(2)
        logger.info('PiCamera Prepared')

        now = datetime.datetime.now()
        hour = now.hour
        logger.info("現在時刻は" + str(now))

        if hour >= hourToBegin -1 and hour < hourToStop: #動作は止める時刻になる前まで
            localFile_name = capture_send() #写真撮影し、結果をサーバーに送信、送信ファイル名を受け取る

        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute
        if hour < hourToBegin -1:
            logger.info("現在時刻は" + str(hour) + "（hour < hourToBegin -1: #改良版）")
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
        logger.info("Deepsleep in " + str(x) + "minutes")
        x = x / 5
        timeToOff = 40
        powerControlCommand = 'sudo /usr/sbin/i2cset -y 1 0x40 ' + str(timeToOff) + ' ' + str(x) + ' i'
        #40秒後に電源オフ、最後のパラメーター×5分後に起動

        #logger.info('電源モジュールに送信するコマンド用意：' + powerControlCommand + ':40秒後にシャットダウン、最後のパラメーター×5分後に起動')
        timeToWait = datetime.timedelta(minutes=x*5)
        wakeupTime = now + timeToWait #起動時刻算出


        logger.info('電源モジュールに送信するコマンド用意：' + powerControlCommand + ':' + str(timeToOff) + '秒後に電源オフ、' + wakeupTime.strftime('%m月%d日%H時%M分') + 'に起動')

        temperature, pressure, humid = readData()
        logger.info("Calculate CPU temperature of Raspberry Pi in Degrees C")
        temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU temp

        lightLevel = measureLight()
        #get voltage data from MCP3002
        # ch0
        resp = spi.xfer2([0x68, 0x00])
        voltage_ch1 = ((resp[0] << 8) + resp[1]) & 0x3ff
        time.sleep(1)
        # ch1
        resp = spi.xfer2([0x78, 0x00])
        voltage_ch2 = ((resp[0] << 8) + resp[1]) & 0x3ff

        voltage_ch1 = voltage_ch1 / 38.75
        voltage_ch2 = voltage_ch2 / 38.75

        memo = localFile_name

        time.sleep(5)
        try:
            d = datetime.datetime.today()

            logger.info('sending data to さくらレンタルサーバー via INTER-Mediator')

            params_IM = urllib.urlencode({'c': str(imKey), 'date': str(d), 'temp': temp, 'temperature': temperature, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel, 'v0' : voltage_ch1, 'v1' : voltage_ch2, 'memo' : memo, 'deploy' : DEPLOY_SWITCH})

            conn = httplib.HTTPSConnection("mochimugi.sakura.ne.jp")
            conn.request("GET", "/IM/im_build/webAPI/putDataAPI_withAuth.php?" + params_IM)
            #/IM/im_build/webAPI/putDataAPI_withAuth.php にはさくらサーバー内のMySQL Databaseへのアクセス情報が書かれている
            #DEPLOY_SWITCHに"sandBox"と書いてあれば、putDataAPI_withAuth.phpが自動判別してsandBoxサーバーにデータを送る
            logger.info("connection requested")
            response = conn.getresponse()
            logger.info("Connection status:"+ str(response.status))
            logger.info("Status reason: "+ str(response.reason))
            data = response.read()
            logger.info(data)
            conn.close()

        except:
            logger.debug("Connection to IM webAPI failed")

        sendLog_ftps('mochimugi.log') #ログを送信、

        if GPIO.input(PORT1) == 0:
        #Programスイッチがオン（==1）になっているときは、パワーコントロールモジュールに電源オフ、再起動時間のセットをしない
            GPIO.cleanup() # <- GPIOポートを開放
            logger.info("sending powerControlCommand:" + powerControlCommand)
            for i in range(1,5):
                try:
                    process = Popen(powerControlCommand, shell=True, stdout=PIPE, stderr=PIPE)
                    output, err = process.communicate()

                    if "Error" in err:
                        print "Error encounterd"
                        logger.debug("Error encountered during i2c write"  + str(i) + " time retry.")
                    else:
                        break
                except OSError as e:
                    print "System will reboot"
                    logger.debug("System error. reboot now")
                    call("sudo reboot")

            time.sleep(5)
            logger.info("I2C command success: " + str(i) + " time retry. System will powerdown")
            call('sudo poweroff', shell=True)
        GPIO.cleanup() # <- GPIO 開放、複数回やってもいいのか？？？？？？？
        #2017年06月08日（木）14時27分
    except:
        logger.debug("Main program failed")
        powerControlCommand="sudo /usr/sbin/i2cset -y 1 0x40 255 0 i"
        logger.debug("Sending power control command : "+powerControlCommand)
        for i in range(1,5):
            try:
                process = Popen(powerControlCommand, shell=True, stdout=PIPE, stderr=PIPE)
                output, err = process.communicate()

                if "Error" in err:
                    logger.debug("Error encounterd during i2c write"  + str(i) + " time retry.")
                else:
                    break
            except OSError as e:
                logger.debug ("OSError. System will reboot")
                call("sudo reboot")

        time.sleep(240)
        logger.info("I2C command success: " + str(i) + " time retry. System will powerdown and reboot imedeately")
        call('sudo poweroff', shell=True)
        logger.debug("system will poweroff after 4 minutes, and reboot immediately")
