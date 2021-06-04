#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""File: echo_simple_once.py（sr04_Bluetin.py）
pip install Bluetin_Echo
rootからも呼ぶことがあるので、
sudo pip install Bluetin_Echo としておくこと
さらに、
$ sudo pip install datetime
も必要
https://github.com/MarkAHeywood/Bluetin_Python_Echo/blob/master/examples/echo_simple_once.py
""" 
# 実行ユーザーが誰なのか、調べるコードを追加
# 
import sys, os
#os.seteuid(1000)
os.system('ps -u')

import ambient #ambientにデータを送込むライブラリ
from sr04_Bluetin import sr04_read
import configparser



if __name__ == '__main__':
    # root権限に昇格
    if os.geteuid():
        args = [sys.executable] + sys.argv
        os.execlp('sudo', 'sudo', *args)

from __init__ import get_module_logger #log保存先は/var/log/field_location.log
logger = get_module_logger(__name__)
logger.propagate = True
try:
    DEPLOY_SWITCH = os.environ['DEPLOY']
except: #rc.localからexportされて送られるはずのDEPLOYがない場合は
    DEPLOY_SWITCH = "sandBox"
logger.info('DEPLOY_SWITCH :' + DEPLOY_SWITCH)


configfile = configparser.ConfigParser() #sftpサーバーへの接続準備、Python3では名前変更された
#configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った
configfile.read("/home/pi/Documents/field_location/config.conf")#絶対パスを使った

ambiChannel = configfile.get("settings", "ambiChannel")
ambiKey = configfile.get("settings", "ambiKey")
ambiChannelSandbox = configfile.get("settings", "ambiChannelSandbox") #サンドボックスチャネル
ambiKeySandbox = configfile.get("settings", "ambiKeySandbox")  #サンドボックスチャネル

depth = sr04_read()

print("計測終了")
print(depth)

