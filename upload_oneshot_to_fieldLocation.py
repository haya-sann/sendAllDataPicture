#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Final Candidate2016/08/15、18:17
import time
import picamera
import datetime
import os
from ftplib import FTP_TLS
import logging
import ConfigParser

hourToBegin = 1 #カメラを動作開始させる時刻
hourToStop = 24 #カメラを完全休止させる時刻
everyMinutes = 2 #何分おきに撮影するのかをセット

configfile = ConfigParser.SafeConfigParser()
configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った

archive_server = configfile.get("settings","ftpsHost")  #サーバーのドメイン名
pw = configfile.get("settings","password")	  #ログインパスワード
userID = configfile.get("settings","id")		#サーバーログインUser id

put_directory  = 'daily_timelapseSandbox' #Both Local and Remote Server has same directory
dir_path = '/home/pi/Documents/field_location/'+ put_directory

def send_ftps(file_name):
		print("accessing"+ archive_server)
		print("ID:"+ userID)
		print("Pass"+ pw)
		
		_ftps = FTP_TLS(archive_server)
		_ftps.set_debuglevel(1) # デバッグログをリアルタイムで確認
		_ftps.login(userID, pw)

		_file = open(dir_path + '/' +file_name, 'rb') #target file. 次のステップでアップロード成功したら削除した方がよ$
		#SD Memoryがパンクする恐れがあるので、次のステップでアップロードが成功したらファイルは削除するように、改良 $

#		_ftps.cwd('/home/users/0/ciao.jp-kawagoesatoyama/web/seasonShots/' + put_directory) #アップロード先ディレクトリに移動
		_ftps.cwd('/seasonShots/' + put_directory) #アップロード先ディレクトリに移動
		_ftps.storbinary('STOR ' + file_name, _file)
		_file.close()
		_ftps.quit()
		print "Upload finished"

def capture_send():
		print('Waitng for shooting time')
		while True:
			now = datetime.datetime.now()
			if now.minute % everyMinutes == 0: #指定毎分時になると撮影
				print('指定時間になりました')
				file_name = now.strftime('%Y%m%d%H%M') + '.jpg'
				break
			elif everyMinutes - (now.minute % everyMinutes) >7:#、5分以上待つなら取りあえず撮影して終わる
				print('指定時間まで7分以上ありますので、テスト撮影して指定時刻5分前に再起動します')
				file_name = '電源投入時テスト_' + now.strftime('%Y%m%d%H%M') + '.jpg'
				break
		print('保存ファイル名；' + file_name)
		picamera.capture(dir_path+'/'+file_name)
		send_ftps(file_name)

print ('Preparering PiCamera')
picamera = picamera.PiCamera()
picamera.resolution = (1920, 1080) #HD Quality Size=1.5MB、研究材料としては最低限これくらいはほしい。稲穂の様子はこ$
#picamera.resolution = (1024, 768) # こちらは554KBで済む
# Camera warm-up time、Whiteバランスをとるための猶予時間。これがないと色が青白くて使い物にならない
time.sleep(2)


now = datetime.datetime.now()
hour = now.hour

if hour >= hourToBegin and hour < hourToStop : #動作は止める時刻になる前まで
	capture_send()

now = datetime.datetime.now()
hour = now.hour
min = now.minute
if hour < hourToBegin :
		x = 60 * hourToBegin - (hour*60 + min)
elif hour >= hourToStop: #停止設定時刻になったら深夜24時までストップさせる
						#ここはちょっとおかしい。もし、開始時刻として深夜〇時以前が指定されていると、狂う
	x = 1440 - (hour*60 + min)
else:
	x = everyMinutes -5 -min	#毎撮影時刻の5分前までに何分あるかを算出
	if x <0:
		x = 0 #電源モジュールは負の値は指定できない（のではないかな？）
		# x = 5   #テストのために5分のスリープを指定
		print ("Deepsleep in " + str(x) + "minutes")
x = x / 5
powerMonagementModule_controlCommand = '/usr/sbin/i2cset -y 1 0x40 10 ' + str(x) + ' i' #10秒後にシャットダウン、最後のパラメーター×5分後に起動
print('電源モジュールにコマンド送信：' + powerMonagementModule_controlCommand + ':10秒後にシャットダウン、最後のパラメーター×5分後に起動')
logging.basicConfig(filename=dir_path + '/'+ 'field_location.log',level=logging.DEBUG,format='%(asctime)s %(message)s')
logging.info('Power Management command:'  + powerMonagementModule_controlCommand)
send_ftps('field_location.log')
#os.system(powerMonagementModule_controlCommand)#シャットダウンコマンドはログをとってから
# time.sleep(5)
# os.system('poweroff')
