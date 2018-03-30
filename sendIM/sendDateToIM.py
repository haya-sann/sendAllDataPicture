#!/usr/bin/python
#coding: utf-8

import httplib, urllib
import time
import datetime # datetimeモジュールのインポート
import locale   # import文はどこに書いてもOK(可読性などの為、慣例でコードの始めの方)

def captureSensorData():
    #センサーからデータ収集するプログラムを実装
    #I2C、SPIなどを使ってデータキャプチャ
    temperature = 53.32
    pressure = 1090
    humid = 56.5
    lightLevel = 1200
    return temperature, pressure, humid, lightLevel

# today()メソッドで現在日付・時刻のdatetime型データの変数を取得
d = datetime.datetime.today()

print ('データ取得時刻 == %s : %s\n' % (d, type(d))) # Microsecond(10^-6sec)まで取得

#Calculate CPU temperature of Raspberry Pi in Degrees C
temp = int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1e3 # Get Raspberry Pi CPU temp

temperature, pressure, humid, lightLevel = captureSensorData()

#send date to さくらレンタルサーバー

params_IM = urllib.urlencode({'c': "TsaJt1fR5SyN",    'date': str(d), 'temp': temp, 'temperature': temperature, 'pressure': pressure, 'humid': humid, 'lux' : lightLevel })


if __name__ == '__main__':
    try:            
        conn = httplib.HTTPSConnection("mochimugi.ne.jp")
        conn.request("GET", "/IM/dev/webAPI/putDataAPI_withAuth.php?" + params_IM)
        print ("connection requested")
        response = conn.getresponse()
        print (response.status, response.reason)
        data = response.read()
        print (data)
        conn.close()

    except:
        print ("connection failed")





