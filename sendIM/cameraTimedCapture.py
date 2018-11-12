#!/usr/bin/python
#coding: utf-8

import datetime # datetimeモジュールのインポート
import picamera
import os
import time
from ftps import send_ftps

from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)

logger.propagate = True
picamera = picamera.PiCamera()

def capture_send(everyMinutes):
    logger.info('Waiting for shooting time')
    while True:
        now = datetime.datetime.now()
        if now.minute % everyMinutes <= 7: #指定毎分時、過ぎた場合は7分以内なら正常撮影
            logger.info('指定時間になりました')
            captureFile_name = now.strftime('%Y%m%d%H%M') + '.jpg'
            break
        elif everyMinutes - (now.minute % everyMinutes) > 7:#7分より多く待つなら取りあえず撮影して終わる
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
    picamera.capture(captureFile_name)
    
    try:
        send_ftps(captureFile_name)
        logger.info("File is sended with no error. Delete " + captureFile_name + " on Ras Pi")
        os.remove(captureFile_name)
        return captureFile_name

    except:
        logger.info("Failed file transfer in send_ftps。そのまま何もしない")

